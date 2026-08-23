#!/usr/bin/env python3
"""secu-scan : inventaire de sécurité d'une skill ou d'un plugin Claude Code tiers.

Lecture seule, stdlib seule. Le dossier cible n'est jamais exécuté, jamais modifié.
Le script balaie ce que l'oeil saute (caractères invisibles, HTML caché, blobs encodés,
contenu des scripts) et classe chaque motif trouvé par famille et par niveau :

  rouge   certitude mécanique, arrêt sauf preuve d'inertie (fichier:ligne)
  orange  demande un jugement en contexte
  info    inventaire, pas un risque en soi

Le verdict reste au lecteur : ce script ne décide rien, il rend la liste opposable.

usage : python3 secu-scan.py <dossier> [--json]
"""

import json
import os
import re
import stat
import sys
import unicodedata
from collections import Counter

MAX_OCTETS_SCAN = 2 * 1024 * 1024
MAX_HITS_PAR_FICHIER_FAMILLE = 15
DOSSIERS_IGNORES = {".git", ".DS_Store"}
DOSSIERS_VENDORED = {"node_modules", "vendor", ".venv", "venv", "__pycache__", "dist", "build"}
EXT_BINAIRE_OPAQUE = {".so", ".dylib", ".node", ".wasm", ".exe", ".dll", ".jar", ".pyc", ".pyd", ".o", ".a", ".bin"}

ROUGE, ORANGE, INFO = "rouge", "orange", "info"

# ---------------------------------------------------------------------------
# Familles de motifs. Chaque motif est compilé en ignorecase.
# ---------------------------------------------------------------------------

FAMILLES = [
    ("exec-distant", ROUGE, [
        r"(?:curl|wget)[^|\n;]*\|\s*(?:sudo\s+)?(?:ba|z|da|k)?sh\b",
        r"(?:ba|z|da|k)?sh\s+-c\s+[\"']?\$\(\s*(?:curl|wget)",
        r"(?:ba|z|da|k)?sh\s+<\(\s*(?:curl|wget)",
        r"\beval\b[^\n]*(?:\bcurl\b|\bwget\b|\bbase64\b|decode|\bnc\b|\bfetch\b)",
        r"\bbase64\s+(?:-d|-D|--decode)\b",
        r"\bb64decode\s*\(",
        r"\bbytes\.fromhex\s*\(",
        r"\bmarshal\.loads\s*\(",
        r"\bpickle\.loads?\s*\(",
        r"\bnew\s+Function\s*\(",
        r"\bvm\.runIn\w*Context\s*\(",
    ]),
    ("secret-en-dur", ROUGE, [
        r"\bsk-ant-[A-Za-z0-9_\-]{20,}",
        r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}\b",
        r"\bghp_[A-Za-z0-9]{30,}\b",
        r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
        r"\bxox[abpors]-[A-Za-z0-9\-]{10,}",
        r"\blin_api_[A-Za-z0-9]{20,}\b",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"\bAIza[0-9A-Za-z_\-]{35}\b",
        r"\bglpat-[A-Za-z0-9_\-]{20,}\b",
        r"\bnpm_[A-Za-z0-9]{36}\b",
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY",
    ]),
    ("exfil-connu", ROUGE, [
        r"hooks\.slack\.com/",
        r"discord(?:app)?\.com/api/webhooks",
        r"api\.telegram\.org/bot",
        r"\bngrok\.(?:io|app|dev)\b",
        r"\brequestbin\b",
        r"\bpipedream\.net\b",
        r"\bwebhook\.site\b",
        r"\bburpcollaborator\b",
        r"\boast\.(?:fun|pro|live|site|online|me)\b",
        r"\binteract\.sh\b",
        r"\bcanarytokens\b",
        r"\.onion\b",
        r"\bpastebin\.com\b",
        r"\btransfer\.sh\b",
        r"\b0x0\.st\b",
        r"\btermbin\.com\b",
    ]),
    ("persistance-forte", ROUGE, [
        r"\.ssh/authorized_keys",
        r"\bcrontab\s+-[^\n]*(?:curl|wget|python|sh\b)",
    ]),
    ("secrets", ORANGE, [
        r"~/\.ssh\b|\$HOME/\.ssh\b|/\.ssh/",
        r"\bid_(?:rsa|ed25519|ecdsa|dsa)\b",
        r"~/\.aws\b|\$HOME/\.aws\b|\.aws/credentials",
        r"~/\.gnupg\b|\.gnupg/",
        r"\.netrc\b|\.npmrc\b|\.pypirc\b|\.git-credentials\b",
        r"\.docker/config\.json|\.kube/config",
        r"\bkeychain\b|security\s+find-(?:generic|internet)-password",
        r"\.claude/\.credentials|\.credentials\.json",
        r"(?<![\w-])\.env\b(?!\.example|\.sample|\.template)",
        r"\b(?:ANTHROPIC|OPENAI|AWS_SECRET|GITHUB|GH|NPM|SLACK|LINEAR|NOTION|STRIPE|OPENROUTER|GEMINI|GOOGLE)_(?:API_KEY|TOKEN|ACCESS_KEY|SECRET|SECRET_KEY)\b",
        r"/etc/(?:passwd|shadow|sudoers)\b",
        r"\bprintenv\b|\bexport\s+-p\b",
        r"\bos\.environ\b(?!\s*[\[.])",
        r"\bprocess\.env\b(?!\s*[\[.])",
    ]),
    ("reseau", ORANGE, [
        r"\bcurl\b", r"\bwget\b", r"\bnc\s+-", r"\bncat\b", r"\bsocat\b",
        r"\bfetch\s*\(", r"\brequests\.(?:get|post|put|patch|delete|request)\s*\(",
        r"\burllib\.request\b|\burlopen\s*\(", r"\bhttp\.client\b", r"\bhttpx\.", r"\baiohttp\b",
        r"\baxios\b", r"\bXMLHttpRequest\b", r"\bnew\s+WebSocket\s*\(",
        r"(?<![\w-])(?:ssh|scp|sftp|rsync)\s+\S", r"\bsmtplib\b|\bsendmail\b",
        r"\bnslookup\b|\bdig\s+\S",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?<!127\.0\.0\.1)(?<!0\.0\.0\.0)",
    ]),
    ("telemetrie", ORANGE, [
        r"\bposthog\b|\bsegment\.io\b|\bmixpanel\b|\bsentry\.io\b|google-analytics|\bgtag\(|\bamplitude\b",
        r"\bipinfo\.io\b|\bicanhazip\b|\bifconfig\.me\b|\bipify\b",
    ]),
    ("exec-local", ORANGE, [
        r"\beval\b",
        r"\bsubprocess\.(?:run|call|Popen|check_output|check_call)\s*\(",
        r"\bos\.(?:system|popen|exec[lv]p?e?)\s*\(",
        r"\bchild_process\b|\bexecSync\s*\(|\bspawnSync\s*\(",
        r"\bosascript\b|\bpowershell\b",
        r"\b(?:python3?|node|perl|ruby)\s+-[ce]\s+[\"']",
        r"\bchmod\s+(?:\+x|[0-7]*7[0-7]*)\b",
    ]),
    ("installe-a-la-volee", ORANGE, [
        r"\bpip3?\s+install\b", r"\buv\s+(?:pip\s+)?(?:add|install)\b", r"\buvx\s+\S",
        r"\bnpm\s+(?:i|install|exec)\b", r"\bnpx\s+\S", r"\bpnpm\s+(?:add|dlx|exec)\b",
        r"\bbunx\s+\S|\bbun\s+(?:add|install|x)\b",
        r"\bbrew\s+install\b", r"\bcargo\s+install\b", r"\bgo\s+install\b", r"\bgem\s+install\b",
        r"\b(?:apt|apt-get|yum|dnf|apk)\s+(?:-y\s+)?(?:install|add)\b",
    ]),
    ("persistance", ORANGE, [
        r"~/\.claude\b|\$HOME/\.claude\b|/\.claude/settings",
        r"\bsettings(?:\.local)?\.json\b",
        r"(?<![\w/])CLAUDE\.md\b",
        r"~/\.(?:zshrc|bashrc|bash_profile|profile|zprofile|zshenv)\b",
        r"/etc/(?:hosts|profile|environment|paths)\b",
        r"\bcrontab\b|\blaunchctl\b|LaunchAgents|LaunchDaemons|\bsystemctl\b|\bsystemd\b",
        r"\.git/hooks\b|git\s+config\s+--global",
        r"\bsudo\b", r"\bdefaults\s+write\b",
        r"/usr/local/bin\b|~/\.local/bin\b|\bPATH=",
        r"(?:>>?|\btee|\bcp|\bmv|\binstall)\s+(?:-\w+\s+)*[\"']?(?:~/|\$HOME/|/Users/|/home/)",
    ]),
    ("destruction", ORANGE, [
        r"\brm\s+-[a-zA-Z]*[rf]", r"\brmdir\b", r"\bshred\b",
        r"git\s+push\b[^\n]*(?:--force\b|\s-f\b)", r"git\s+reset\s+--hard", r"git\s+clean\s+-[a-z]*f",
        r"git\s+branch\s+(?-i:-D)\b",
        r"\bDROP\s+(?:TABLE|DATABASE)\b", r"\bTRUNCATE\s+TABLE\b",
        r"\bmkfs\b", r"\bdd\s+if=", r">\s*/dev/(?:sd|disk|nvme)",
        r"\bkill\s+-9\b|\bpkill\b|\bkillall\b",
        r"\bshutil\.rmtree\s*\(|\bos\.remove\s*\(|\bos\.unlink\s*\(|\bfs\.rm(?:Sync)?\s*\(|\brimraf\b",
    ]),
    ("injection", ORANGE, [
        r"\bignore\s+(?:all\s+|any\s+)?(?:previous|prior|above|earlier|other)\s+(?:instructions?|rules?|prompts?|guidelines?)",
        r"\bdisregard\s+(?:your|the|all|any)\s+(?:instructions?|rules?|system\s+prompt|guidelines?)",
        r"\bignor\w*\s+(?:toutes?\s+)?(?:les|tes|vos|ses)\s+(?:instructions?|consignes?|règles?)",
        r"\byou\s+are\s+now\b", r"\bnew\s+instructions?\s*:",
        r"\bsystem\s+prompt\b",
        r"\b(?:do\s+not|don'?t|never)\s+(?:tell|inform|mention|reveal|show|warn)\s+(?:this\s+to\s+)?(?:the\s+)?user\b",
        r"\bwithout\s+(?:telling|informing|asking|notifying|warning)\s+(?:the\s+)?user\b",
        r"\bsans\s+(?:le\s+|en\s+)?(?:dire|prévenir|avertir|demander)\s+(?:à\s+)?l'utilisateur",
        r"\bne\s+(?:dis|révèle|mentionne|montre)\s+(?:rien|pas|jamais)\b",
        r"\b(?:don'?t|do\s+not|never)\s+ask\s+(?:for\s+)?(?:permission|confirmation|approval)",
        r"\bbypass\w*\s+(?:the\s+)?(?:permissions?|sandbox|guard|hooks?|safety|checks?)",
        r"--dangerously-skip-permissions|\bbypassPermissions\b",
        r"\b(?:secretly|covertly)\b",
        r"\b(?:hide|conceal|mask|obscure)\s+(?:this|the|your|any)\b",
        r"\bthis\s+is\s+(?:an?\s+)?(?:authorized|approved|sanctioned|official)\b",
        r"\banthropic\s+(?:has\s+)?(?:approved|authorized|verified|sanctioned)|(?:approved|authorized|verified|reviewed|sanctioned)\s+by\s+anthropic",
        r"\bskip\s+(?:any\s+|the\s+|all\s+)?(?:security|safety)\s+(?:analysis|check|review|scan|audit)",
        r"\bas\s+(?:an?\s+|the\s+)?(?:admin|administrator|root|developer\s+mode|superuser)\b",
        r"\bjailbreak\b|\bDAN\s+mode\b",
        r"\b(?:before|after)\s+(?:every|each)\s+(?:response|turn|tool\s+call|message)\b",
        r"\b(?:send|post|upload|forward|transmit)\s+(?:the\s+|all\s+|any\s+|your\s+)?(?:contents?|files?|keys?|tokens?|secrets?|credentials?|environment|env)\b",
        r"\bexfiltrat\w*",
    ]),
]

FAMILLES_COMPILEES = [(f, n, [re.compile(p, re.IGNORECASE) for p in motifs]) for f, n, motifs in FAMILLES]
INJECTION_COMPILEE = next(m for f, _, m in FAMILLES_COMPILEES if f == "injection")

HEX_BLOB = re.compile(r"(?:\\x[0-9a-fA-F]{2}){8,}")
B64_BLOB = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{120,}={0,2}(?![A-Za-z0-9+/=])")
HTML_COMMENTAIRE = re.compile(r"<!--(.*?)-->", re.DOTALL)
HTML_CACHE = re.compile(
    r"<[^>]+(?:\bhidden\b|display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?![.\d])|"
    r"opacity\s*:\s*0(?![.\d])|color\s*:\s*(?:white|#fff(?:fff)?|transparent)\b)[^>]*>",
    re.IGNORECASE,
)
# Le HTML caché ne compte que dans les fichiers que le modèle lit comme des consignes.
EXT_CONSIGNES = {".md", ".mdx", ".markdown", ".txt", "(sans)"}
ESCAPE_INVISIBLE = re.compile(
    r"&#x?(?:200[b-f]|202[a-e]|2060|feff|8203|8204|8205|8206|8207);|"
    r"&(?:zwj|zwnj|lrm|rlm|shy);|\\u(?:200[b-f]|202[a-e]|2060|feff)",
    re.IGNORECASE,
)
URL = re.compile(r"https?://([A-Za-z0-9.\-]+)(?::\d+)?(?=[/\s\"'<>)\]]|$)")
SCRIPT_MIXTE = re.compile(r"\b(?=\w*[A-Za-z])(?=\w*[Ͱ-ϿЀ-ӿ])\w+\b")

# Caractères invisibles ou directionnels. Le BOM en tout premier caractère du fichier est toléré.
PLAGES_INVISIBLES = [
    (0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C), (0x115F, 0x1160), (0x180E, 0x180E),
    (0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x2064), (0x2066, 0x2069),
    (0x3164, 0x3164), (0xFEFF, 0xFEFF), (0xFFF9, 0xFFFB), (0xE0000, 0xE007F),
]


def est_invisible(cp):
    return any(a <= cp <= b for a, b in PLAGES_INVISIBLES)


def nom_codepoint(ch):
    try:
        return unicodedata.name(ch)
    except ValueError:
        return "SANS NOM"


def blob_suspect(s):
    """Un vrai blob base64 mêle majuscules, minuscules et chiffres, et n'est pas de l'hexa pur."""
    return (any(c.isupper() for c in s) and any(c.islower() for c in s) and any(c.isdigit() for c in s)
            and not re.fullmatch(r"[0-9a-fA-F]+", s))


def est_texte(octets):
    return b"\x00" not in octets[:8192]


def tronquer(s, n=160):
    s = s.replace("\t", " ").strip()
    return s if len(s) <= n else s[: n - 3] + "..."


def echapper_invisibles(s):
    return "".join(f"<U+{ord(c):04X}>" if est_invisible(ord(c)) else c for c in s)


def lister(root):
    fichiers = []
    for dossier, sous, noms in os.walk(root):
        sous[:] = sorted(d for d in sous if d not in DOSSIERS_IGNORES)
        for nom in sorted(noms):
            if nom in DOSSIERS_IGNORES:
                continue
            fichiers.append(os.path.join(dossier, nom))
    return fichiers


class Scan:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.hits = []
        self.inventaire = {
            "fichiers": 0, "octets": 0, "extensions": Counter(), "binaires": [],
            "executables": [], "liens": [], "gros_fichiers": [], "vendored": Counter(),
        }
        self.hotes = Counter()
        self.surfaces = {"skills": [], "agents": [], "plugin": None, "hooks": [], "mcp": [], "settings": []}
        self._compteur = Counter()

    def rel(self, chemin):
        return os.path.relpath(chemin, self.root)

    def hit(self, niveau, famille, chemin, ligne, extrait):
        cle = (chemin, famille)
        self._compteur[cle] += 1
        if self._compteur[cle] > MAX_HITS_PAR_FICHIER_FAMILLE:
            return
        self.hits.append({
            "niveau": niveau, "famille": famille, "fichier": self.rel(chemin),
            "ligne": ligne, "extrait": tronquer(echapper_invisibles(extrait)),
        })

    # -- parcours ----------------------------------------------------------

    def lancer(self):
        for chemin in lister(self.root):
            self.examiner(chemin)
        for (chemin, famille), n in self._compteur.items():
            if n > MAX_HITS_PAR_FICHIER_FAMILLE:
                self.hits.append({
                    "niveau": INFO, "famille": famille, "fichier": self.rel(chemin), "ligne": 0,
                    "extrait": f"+{n - MAX_HITS_PAR_FICHIER_FAMILLE} autres occurrences non listées",
                })
        for dossier, n in self.inventaire["vendored"].items():
            self.hits.append({
                "niveau": ORANGE, "famille": "vendored", "fichier": dossier, "ligne": 0,
                "extrait": f"{n} fichiers de dépendances embarquées, inventoriés mais non balayés ligne à ligne",
            })
        ordre = {ROUGE: 0, ORANGE: 1, INFO: 2}
        self.hits.sort(key=lambda h: (ordre[h["niveau"]], h["famille"], h["fichier"], h["ligne"]))
        return self

    def examiner(self, chemin):
        inv = self.inventaire
        rel = self.rel(chemin)
        if os.path.islink(chemin):
            cible = os.path.realpath(chemin)
            dedans = cible.startswith(self.root + os.sep)
            inv["liens"].append({"fichier": rel, "cible": cible, "dedans": dedans})
            if not dedans:
                self.hit(ROUGE, "lien-sortant", chemin, 0, f"lien symbolique vers {cible}")
            return
        try:
            st = os.stat(chemin)
        except OSError:
            return
        inv["fichiers"] += 1
        inv["octets"] += st.st_size
        ext = os.path.splitext(chemin)[1].lower() or "(sans)"
        inv["extensions"][ext] += 1
        if st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            inv["executables"].append(rel)
        if st.st_size > 1024 * 1024:
            inv["gros_fichiers"].append({"fichier": rel, "octets": st.st_size})
        parties = rel.split(os.sep)
        vendored = next((p for p in parties[:-1] if p in DOSSIERS_VENDORED), None)
        if vendored:
            inv["vendored"][os.sep.join(parties[: parties.index(vendored) + 1])] += 1
            return
        try:
            with open(chemin, "rb") as f:
                octets = f.read(MAX_OCTETS_SCAN + 1)
        except OSError:
            return
        if not est_texte(octets):
            inv["binaires"].append(rel)
            if ext in EXT_BINAIRE_OPAQUE:
                self.hit(ORANGE, "binaire-opaque", chemin, 0, f"binaire {ext} de {st.st_size} octets, illisible")
            return
        if len(octets) > MAX_OCTETS_SCAN:
            self.hit(INFO, "non-balaye", chemin, 0, f"{st.st_size} octets, seuls les premiers {MAX_OCTETS_SCAN} ont été lus")
            octets = octets[:MAX_OCTETS_SCAN]
        texte = octets.decode("utf-8", errors="replace")
        self.balayer_texte(chemin, texte, ext)
        self.surfaces_declarees(chemin, texte)

    # -- balayage texte ----------------------------------------------------

    def balayer_texte(self, chemin, texte, ext):
        lignes = texte.split("\n")
        for i, ligne in enumerate(lignes, 1):
            if i == 1 and ligne.startswith("\ufeff"):
                self.hit(INFO, "bom", chemin, 1, "BOM UTF-8 en tête de fichier, toléré")
                ligne = ligne[1:]
            invisibles = [c for c in ligne if est_invisible(ord(c))]
            if invisibles:
                detail = ", ".join(f"U+{ord(c):04X} {nom_codepoint(c)} x{n}" for c, n in Counter(invisibles).items())
                self.hit(ROUGE, "invisible", chemin, i, f"{detail} | {ligne}")
            mixte = SCRIPT_MIXTE.search(ligne)
            if mixte:
                self.hit(ORANGE, "script-mixte", chemin, i, f"mot mêlant latin et cyrillique/grec : {mixte.group(0)}")
            if ESCAPE_INVISIBLE.search(ligne):
                self.hit(ORANGE, "invisible-echappe", chemin, i, ligne)
            if len(ligne) > 2000 and ext in (".md", ".txt", ".yaml", ".yml", ".json"):
                self.hit(ORANGE, "ligne-geante", chemin, i, f"{len(ligne)} caractères sur une ligne : {ligne[:80]}")
            if HEX_BLOB.search(ligne):
                self.hit(ROUGE, "blob-encode", chemin, i, ligne)
            for m in B64_BLOB.finditer(ligne):
                if blob_suspect(m.group(0)):
                    niveau = ORANGE if "data:image/" in ligne else ROUGE
                    self.hit(niveau, "blob-encode", chemin, i, ligne)
                    break
            for h in URL.finditer(ligne):
                self.hotes[h.group(1).lower()] += 1
            for famille, niveau, motifs in FAMILLES_COMPILEES:
                for motif in motifs:
                    if motif.search(ligne):
                        self.hit(niveau, famille, chemin, i, ligne)
                        break
        if ext in EXT_CONSIGNES:
            for m in HTML_COMMENTAIRE.finditer(texte):
                contenu = " ".join(m.group(1).split())
                if not contenu:
                    continue
                ligne = texte.count("\n", 0, m.start()) + 1
                # Une consigne d'injection cachée à l'humain mais lue par le modèle : certitude, pas jugement.
                if any(motif.search(contenu) for motif in INJECTION_COMPILEE):
                    self.hit(ROUGE, "injection-cachee", chemin, ligne, contenu)
                else:
                    self.hit(ORANGE, "html-commentaire", chemin, ligne, contenu)
            for m in HTML_CACHE.finditer(texte):
                self.hit(ROUGE, "html-cache", chemin, texte.count("\n", 0, m.start()) + 1, m.group(0))

    # -- surfaces déclarées ------------------------------------------------

    @staticmethod
    def frontmatter(texte):
        if not texte.startswith("---"):
            return None
        fin = texte.find("\n---", 3)
        if fin < 0:
            return None
        cles = {}
        for ligne in texte[3:fin].split("\n"):
            m = re.match(r"^([A-Za-z_][\w\-]*)\s*:\s*(.*)$", ligne)
            if m:
                cles[m.group(1)] = m.group(2).strip()
        return cles

    CLES_SENSIBLES = ("allowed-tools", "tools", "hooks", "disable-model-invocation", "user-invocable", "context", "agent", "model", "effort")

    def surfaces_declarees(self, chemin, texte):
        rel = self.rel(chemin)
        nom = os.path.basename(chemin)
        parties = rel.split(os.sep)
        est_agent = len(parties) >= 2 and parties[-2] == "agents" and nom.endswith(".md")
        if nom == "SKILL.md" or est_agent:
            fm = self.frontmatter(texte) or {}
            entree = {"fichier": rel, "cles": sorted(fm.keys())}
            for cle in self.CLES_SENSIBLES:
                if cle in fm:
                    entree[cle] = fm[cle]
            outils = fm.get("allowed-tools", fm.get("tools"))
            if outils is not None:
                niveau = ORANGE if re.search(r"\bBash\b(?!\()", outils) else INFO
                self.hit(niveau, "permissions", chemin, 1, f"outils déclarés : {outils or '(vide)'}")
            if "hooks" in fm:
                self.hit(ORANGE, "permissions", chemin, 1, "hooks déclarés dans le frontmatter")
            (self.surfaces["agents"] if est_agent else self.surfaces["skills"]).append(entree)
            return
        if nom == "plugin.json" and ".claude-plugin" in parties:
            try:
                data = json.loads(texte)
            except ValueError:
                self.hit(ORANGE, "manifeste", chemin, 0, "plugin.json illisible (JSON invalide)")
                return
            if not isinstance(data, dict):
                return
            self.surfaces["plugin"] = {
                "fichier": rel, "name": data.get("name"), "version": data.get("version"),
                "composants": sorted(k for k in ("commands", "agents", "skills", "hooks", "mcpServers", "lspServers", "outputStyles") if k in data),
            }
            if isinstance(data.get("mcpServers"), dict):
                self.mcp(chemin, data["mcpServers"])
            if isinstance(data.get("hooks"), dict):
                self.hooks(chemin, data["hooks"])
            return
        if nom == "hooks.json" or (nom.endswith(".json") and "hooks" in parties[:-1]):
            try:
                data = json.loads(texte)
            except ValueError:
                return
            if isinstance(data, dict):
                self.hooks(chemin, data.get("hooks", data))
            return
        if nom == ".mcp.json":
            try:
                data = json.loads(texte)
            except ValueError:
                return
            if isinstance(data, dict):
                self.mcp(chemin, data.get("mcpServers", data))
            return
        if nom in ("settings.json", "settings.local.json"):
            self.surfaces["settings"].append(rel)
            self.hit(ORANGE, "permissions", chemin, 0, "fichier settings embarqué dans le paquet")

    def hooks(self, chemin, data):
        rel = self.rel(chemin)
        if not isinstance(data, dict):
            return
        for evenement, entrees in data.items():
            if not isinstance(entrees, list):
                continue
            for entree in entrees:
                if not isinstance(entree, dict):
                    continue
                for h in entree.get("hooks", []):
                    if not isinstance(h, dict):
                        continue
                    commande = str(h.get("command") or h.get("prompt") or "")
                    self.surfaces["hooks"].append({"fichier": rel, "evenement": evenement, "type": h.get("type"), "commande": tronquer(commande)})
                    self.hit(ORANGE, "hook", chemin, 0, f"{evenement} {h.get('type')} : {commande}")

    def mcp(self, chemin, serveurs):
        rel = self.rel(chemin)
        if not isinstance(serveurs, dict):
            return
        for nom, conf in serveurs.items():
            if not isinstance(conf, dict):
                continue
            env = conf.get("env") if isinstance(conf.get("env"), dict) else {}
            commande = " ".join([str(conf.get("command", ""))] + [str(a) for a in conf.get("args", []) or []]).strip()
            entree = {"fichier": rel, "nom": nom, "type": conf.get("type"), "commande": tronquer(commande), "url": conf.get("url"), "env": sorted(env.keys())}
            self.surfaces["mcp"].append(entree)
            self.hit(ORANGE, "mcp", chemin, 0, f"serveur {nom} : {commande or conf.get('url')}")
            for k, v in env.items():
                v = str(v)
                if v and not v.startswith("$") and len(v) >= 16:
                    self.hit(ROUGE, "secret-en-dur", chemin, 0, f"env {k} porte une valeur littérale de {len(v)} caractères")

    # -- sorties -----------------------------------------------------------

    def totaux(self):
        c = Counter(h["niveau"] for h in self.hits)
        return {ROUGE: c[ROUGE], ORANGE: c[ORANGE], INFO: c[INFO]}

    def json(self):
        inv = dict(self.inventaire)
        inv["extensions"] = dict(inv["extensions"])
        inv["vendored"] = dict(inv["vendored"])
        return {"root": self.root, "inventaire": inv, "surfaces": self.surfaces, "hotes": dict(self.hotes), "hits": self.hits, "totaux": self.totaux()}

    def texte(self):
        inv, s, out = self.inventaire, self.surfaces, []
        exts = ", ".join(f"{e} {n}" for e, n in inv["extensions"].most_common())
        out.append(f"secu-scan  {self.root}")
        out.append(f"fichiers : {inv['fichiers']}  ({exts})  taille : {inv['octets'] / 1024:.0f} Ko")
        out.append(f"binaires : {len(inv['binaires'])}  exécutables : {len(inv['executables'])}  liens : {len(inv['liens'])}  gros fichiers : {len(inv['gros_fichiers'])}")
        for e in inv["executables"]:
            out.append(f"  exécutable  {e}")
        for b in inv["binaires"]:
            out.append(f"  binaire     {b}")
        for g in inv["gros_fichiers"]:
            out.append(f"  gros        {g['fichier']} ({g['octets']} octets)")
        for d, n in inv["vendored"].items():
            out.append(f"  vendored    {d} ({n} fichiers)")
        out.append("")
        out.append("surfaces déclarées :")
        if s["plugin"]:
            p = s["plugin"]
            out.append(f"  plugin.json  {p['fichier']} : name={p['name']} version={p['version']} composants={', '.join(p['composants']) or 'aucun déclaré'}")
        for e in s["skills"] + s["agents"]:
            extras = ", ".join(f"{k}={e[k]}" for k in self.CLES_SENSIBLES if k in e)
            out.append(f"  frontmatter  {e['fichier']} : clés {', '.join(e['cles']) or 'aucune'}" + (f" | {extras}" if extras else ""))
        out.append(f"  hooks        {len(s['hooks'])}" + "".join(f"\n    {h['evenement']} {h['type']} : {h['commande']}" for h in s["hooks"]))
        out.append(f"  mcp          {len(s['mcp'])}" + "".join(f"\n    {m['nom']} ({m['type'] or 'stdio'}) : {m['commande'] or m['url']} env={m['env']}" for m in s["mcp"]))
        if s["settings"]:
            out.append(f"  settings     {', '.join(s['settings'])}")
        out.append("hôtes cités : " + (", ".join(f"{h} ({n})" for h, n in self.hotes.most_common()) or "aucun"))
        t = self.totaux()
        for niveau in (ROUGE, ORANGE, INFO):
            out.append("")
            familles = Counter(h["famille"] for h in self.hits if h["niveau"] == niveau)
            resume = ", ".join(f"{f} {n}" for f, n in familles.most_common())
            out.append(f"{niveau.upper()} ({t[niveau]})" + (f" : {resume}" if resume else ""))
            for h in self.hits:
                if h["niveau"] == niveau:
                    pos = f"{h['fichier']}:{h['ligne']}" if h["ligne"] else h["fichier"]
                    out.append(f"  {h['famille']:<20} {pos}  {h['extrait']}")
        out.append("")
        out.append(f"total : rouge {t[ROUGE]}, orange {t[ORANGE]}, info {t[INFO]}")
        return "\n".join(out)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        sys.stderr.write(__doc__)
        return 2
    root = args[0]
    if not os.path.isdir(root):
        sys.stderr.write(f"secu-scan : dossier introuvable : {root}\n")
        return 2
    scan = Scan(root).lancer()
    if "--json" in argv:
        print(json.dumps(scan.json(), ensure_ascii=False, indent=1))
    else:
        print(scan.texte())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
