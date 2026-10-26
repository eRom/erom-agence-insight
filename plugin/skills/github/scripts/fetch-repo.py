#!/usr/bin/env python3
"""fetch-repo : les faits d'un repo GitHub pour la skill github, via `gh api`.

Lecture seule côté GitHub, stdlib seule, aucun clone. Tout ce qui est un chiffre ou une
date vient d'ici, jamais du modèle : la fiche recopie, elle n'estime pas.

Écrit dans <out-dir> :
  facts.json   identité, métriques, activité, marqueurs CI/tests/docs/Docker, manifestes
  README.md    le README brut (absent si le repo n'en a pas)
  manifests/   les manifestes de dépendances, chemin aplati (`/` devient `__`)

usage : python3 fetch-repo.py <owner/repo|url GitHub> <out-dir> [--today YYYY-MM-DD]
codes : 0 ok, 2 repo introuvable ou cible illisible, 1 gh absent ou en échec
"""

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

# Seuils d'activité, en jours depuis le dernier commit de la branche par défaut.
ACTIVE_DAYS = 30
SLOWING_DAYS = 180

MAX_MANIFESTS = 8
MAX_MANIFEST_BYTES = 64 * 1024
MAX_README_BYTES = 200 * 1024
MAX_EVIDENCE = 3

MANIFEST_NAMES = {
    "package.json", "deno.json", "pyproject.toml", "requirements.txt", "setup.py",
    "Cargo.toml", "go.mod", "Gemfile", "composer.json", "pom.xml", "build.gradle",
    "build.gradle.kts", "Package.swift", "mix.exs", "pubspec.yaml", "CMakeLists.txt",
}
VENDORED_DIRS = {"node_modules", "vendor", "third_party", "third-party", ".venv", "dist", "build"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "testing"}
TEST_FILE = re.compile(
    r"(^test_.*\.py$|_test\.(py|go|rb|exs)$|\.(test|spec)\.(ts|tsx|js|jsx|mjs|cjs)$|Tests?\.swift$|_spec\.rb$)"
)
CI_FILE = re.compile(
    r"^(\.github/workflows/[^/]+\.ya?ml|\.gitlab-ci\.yml|\.circleci/config\.yml|azure-pipelines\.yml|\.travis\.yml|Jenkinsfile|\.buildkite/.+)$"
)
DOCS_FILE = re.compile(r"^(docs?/.+|mkdocs\.ya?ml|docusaurus\.config\.\w+|\.vitepress/.+|book\.toml)$")
DOCKER_FILE = re.compile(r"(^|/)(Dockerfile(\.[\w.-]+)?|Containerfile|(docker-)?compose(\.[\w-]+)?\.ya?ml)$")
CLAUDE_FILE = re.compile(r"(^|/)(\.claude-plugin/(plugin|marketplace)\.json|SKILL\.md|\.mcp\.json)$")
TARGET = re.compile(r"^(?:(?:https?://)?(?:www\.)?github\.com/)?([\w.-]+)/([\w.-]+?)(?:\.git)?(?:/.*)?$")


class GhError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def parse_target(token: str) -> tuple[str, str]:
    """`owner/repo`, une URL de repo ou de sous-page GitHub : renvoie (owner, repo)."""
    match = TARGET.match(token.strip())
    if not match:
        raise ValueError(f"cible illisible : {token}")
    return match.group(1), match.group(2)


def last_page(link_header: str | None, item_count: int) -> int:
    """Nombre total d'éléments d'une liste paginée à per_page=1, lu dans l'en-tête Link."""
    if link_header:
        match = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link_header)
        if match:
            return int(match.group(1))
    return item_count


def classify_activity(last_commit: str | None, archived: bool, today: date) -> tuple[str, int | None]:
    """Renvoie (activité, jours depuis le dernier commit). L'archivage prime sur tout."""
    if last_commit is None:
        return ("archive" if archived else "abandonne"), None
    days = (today - datetime.fromisoformat(last_commit.replace("Z", "+00:00")).date()).days
    if archived:
        return "archive", days
    if days <= ACTIVE_DAYS:
        return "actif", days
    if days <= SLOWING_DAYS:
        return "ralenti", days
    return "abandonne", days


def normalize_license(spdx_id: str | None) -> str:
    """SPDX tel quel ; `aucune` sans fichier de licence ; `non-reconnue` quand GitHub répond NOASSERTION."""
    if not spdx_id:
        return "aucune"
    return "non-reconnue" if spdx_id == "NOASSERTION" else spdx_id


def language_shares(byte_counts: dict[str, int]) -> list[dict]:
    """Octets par langage vers des parts en pourcentage, la plus grosse en tête."""
    total = sum(byte_counts.values())
    if total == 0:
        return []
    shares = [{"language": name, "percent": round(100 * count / total, 1)} for name, count in byte_counts.items()]
    return sorted(shares, key=lambda s: -s["percent"])


def _is_vendored(path: str) -> bool:
    return any(part in VENDORED_DIRS for part in path.split("/")[:-1])


def scan_tree(paths: list[str]) -> dict:
    """Marqueurs oui/non tirés de l'arbre des fichiers, avec quelques chemins en preuve."""
    evidence: dict[str, list[str]] = {"ci": [], "tests": [], "docs": [], "docker": [], "claude_code": []}
    for path in paths:
        if _is_vendored(path):
            continue
        parts = path.split("/")
        name = parts[-1]
        hits = {
            "ci": bool(CI_FILE.match(path)),
            "tests": bool(TEST_FILE.search(name)) or any(p in TEST_DIRS for p in parts[:-1]),
            "docs": bool(DOCS_FILE.match(path)),
            "docker": bool(DOCKER_FILE.search(path)),
            "claude_code": bool(CLAUDE_FILE.search(path)),
        }
        for key, hit in hits.items():
            if hit and len(evidence[key]) < MAX_EVIDENCE:
                evidence[key].append(path)
    return {key: {"present": bool(found), "evidence": found} for key, found in evidence.items()}


def pick_manifests(paths: list[str]) -> list[str]:
    """Manifestes de dépendances, la racine d'abord, au plus deux niveaux de profondeur."""
    found = [
        p for p in paths
        if p.split("/")[-1] in MANIFEST_NAMES and p.count("/") <= 2 and not _is_vendored(p)
    ]
    return sorted(found, key=lambda p: (p.count("/"), p))[:MAX_MANIFESTS]


def gh(path: str, raw: bool = False, include: bool = False) -> tuple[dict, str]:
    """Un appel `gh api`. Renvoie (en-têtes, corps). Lève GhError sur une réponse HTTP en erreur."""
    args = ["gh", "api", path]
    if raw:
        args += ["-H", "Accept: application/vnd.github.raw"]
    if include:
        args.append("-i")
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        match = re.search(r"HTTP (\d{3})", proc.stderr)
        raise GhError(int(match.group(1)) if match else 0, proc.stderr.strip() or proc.stdout.strip())
    if not include:
        return {}, proc.stdout
    head, _, body = proc.stdout.replace("\r\n", "\n").partition("\n\n")
    headers = {}
    for line in head.split("\n")[1:]:
        key, _, value = line.partition(":")
        headers[key.strip().lower()] = value.strip()
    return headers, body


def gh_json(path: str):
    return json.loads(gh(path)[1])


def gh_count(path: str) -> int | None:
    """Taille d'une liste paginée en un appel (per_page=1). None si la liste n'existe pas."""
    sep = "&" if "?" in path else "?"
    try:
        headers, body = gh(f"{path}{sep}per_page=1", include=True)
    except GhError as err:
        # 409 : dépôt vide. 404 : liste absente. 204 : rien.
        if err.status in (204, 404, 409):
            return None
        raise
    items = json.loads(body) if body.strip() else []
    return last_page(headers.get("link"), len(items))


def gh_optional(path: str, raw: bool = False):
    try:
        body = gh(path, raw=raw)[1]
    except GhError as err:
        if err.status in (404, 409):
            return None
        raise
    return body if raw else json.loads(body)


def collect(owner: str, name: str, today: date, out_dir: str) -> dict:
    slug = f"{owner}/{name}"
    repo = gh_json(f"repos/{slug}")
    slug = repo["full_name"]  # suit les renommages et redirections
    branch = repo["default_branch"]

    head = gh_optional(f"repos/{slug}/commits?per_page=1&sha={branch}")
    last_commit = head[0]["commit"]["committer"]["date"] if head else None
    activity, days = classify_activity(last_commit, repo["archived"], today)

    def commits_since(n_days: int) -> int | None:
        since = (datetime.combine(today, datetime.min.time(), timezone.utc) - timedelta(days=n_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return gh_count(f"repos/{slug}/commits?sha={branch}&since={since}")

    latest = gh_optional(f"repos/{slug}/releases/latest")
    tags = gh_optional(f"repos/{slug}/tags?per_page=1")
    open_issues = gh_json(f"search/issues?q=repo:{slug}+type:issue+state:open&per_page=1")["total_count"]

    tree = gh_optional(f"repos/{slug}/git/trees/{branch}?recursive=1") or {"tree": [], "truncated": False}
    paths = [entry["path"] for entry in tree["tree"] if entry["type"] == "blob"]

    os.makedirs(os.path.join(out_dir, "manifests"), exist_ok=True)
    manifests = []
    for path in pick_manifests(paths):
        content = gh_optional(f"repos/{slug}/contents/{path}?ref={branch}", raw=True)
        if content is None:
            continue
        local = os.path.join(out_dir, "manifests", path.replace("/", "__"))
        with open(local, "w", encoding="utf-8") as handle:
            handle.write(content[:MAX_MANIFEST_BYTES])
        manifests.append({"path": path, "local": local, "truncated": len(content) > MAX_MANIFEST_BYTES})

    readme = gh_optional(f"repos/{slug}/readme", raw=True)
    readme_path = None
    if readme is not None:
        readme_path = os.path.join(out_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as handle:
            handle.write(readme[:MAX_README_BYTES])

    owner_info = repo["owner"]
    return {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "today": today.isoformat(),
        "identity": {
            "full_name": slug,
            "name": repo["name"],
            "url": repo["html_url"],
            "owner": owner_info["login"],
            "owner_type": owner_info["type"],
            "owner_url": owner_info["html_url"],
            "owner_avatar": owner_info["avatar_url"],
            "description": repo["description"],
            "homepage": repo["homepage"] or None,
            "topics": repo.get("topics", []),
            "license": normalize_license((repo.get("license") or {}).get("spdx_id")),
            "created_at": repo["created_at"],
            "pushed_at": repo["pushed_at"],
            "default_branch": branch,
            "size_kb": repo["size"],
        },
        "release": {
            "latest_tag": latest["tag_name"] if latest else None,
            "latest_published_at": latest["published_at"] if latest else None,
            "releases_count": gh_count(f"repos/{slug}/releases") or 0,
            "latest_git_tag": tags[0]["name"] if tags else None,
        },
        "languages": {
            "primary": repo["language"],
            "shares": language_shares(gh_json(f"repos/{slug}/languages")),
        },
        "health": {
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            # watchers_count est un alias des étoiles : le vrai nombre d'abonnés est subscribers_count.
            "watchers": repo["subscribers_count"],
            "open_issues": open_issues,
            # open_issues_count compte aussi les PR ouvertes.
            "open_pull_requests": max(0, repo["open_issues_count"] - open_issues),
            "contributors": gh_count(f"repos/{slug}/contributors?anon=1") or 0,
            "last_commit_at": last_commit,
            "days_since_last_commit": days,
            "commits_90d": commits_since(90),
            "commits_365d": commits_since(365),
            "activity": activity,
            "activity_rule": f"actif <= {ACTIVE_DAYS} j, ralenti <= {SLOWING_DAYS} j, abandonne au-delà, archive si archivé",
            "archived": repo["archived"],
            "is_fork": repo["fork"],
            "fork_parent": (repo.get("parent") or {}).get("full_name"),
        },
        "markers": scan_tree(paths),
        "tree": {"files": len(paths), "truncated": tree.get("truncated", False)},
        "manifests": manifests,
        "readme": readme_path,
    }


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--today")]
    today = date.today()
    for i, arg in enumerate(argv):
        if arg == "--today" and i + 1 < len(argv):
            today = date.fromisoformat(argv[i + 1])
            args.remove(argv[i + 1])
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        owner, name = parse_target(args[0])
    except ValueError as err:
        print(err, file=sys.stderr)
        return 2
    out_dir = args[1]
    os.makedirs(out_dir, exist_ok=True)
    try:
        facts = collect(owner, name, today, out_dir)
    except GhError as err:
        if err.status == 404:
            print(f"repo introuvable ou privé sans accès : {owner}/{name}", file=sys.stderr)
            return 2
        print(f"gh en échec (HTTP {err.status}) : {err}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("gh introuvable dans le PATH", file=sys.stderr)
        return 1
    path = os.path.join(out_dir, "facts.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(facts, handle, ensure_ascii=False, indent=2)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
