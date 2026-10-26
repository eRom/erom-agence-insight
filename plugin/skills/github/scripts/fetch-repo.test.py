#!/usr/bin/env python3
"""Cas de fetch-repo.py, sans réseau. Lancer : python3 fetch-repo.test.py

Seules les fonctions pures sont testées ici : la lecture de la cible, l'en-tête Link,
les seuils d'activité, les parts de langages, les marqueurs de l'arbre et le choix des
manifestes. Les appels `gh api` se vérifient en lançant le script sur un vrai repo.
"""

import importlib.util
import os
import unittest
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("fetch_repo", os.path.join(HERE, "fetch-repo.py"))
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)

TODAY = date(2026, 10, 26)


class ParseTarget(unittest.TestCase):
    def test_accepts_slug_and_urls(self):
        for token in (
            "apple/security-pcc",
            "https://github.com/apple/security-pcc",
            "https://github.com/apple/security-pcc.git",
            "https://github.com/apple/security-pcc/tree/main/CloudAttestation",
            "github.com/apple/security-pcc",
        ):
            self.assertEqual(fetch.parse_target(token), ("apple", "security-pcc"), token)

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            fetch.parse_target("pas un repo")


class LastPage(unittest.TestCase):
    def test_reads_last_page_from_link(self):
        link = '<https://api.github.com/x?per_page=1&page=2>; rel="next", <https://api.github.com/x?per_page=1&anon=1&page=341>; rel="last"'
        self.assertEqual(fetch.last_page(link, 1), 341)

    def test_single_page_falls_back_to_item_count(self):
        self.assertEqual(fetch.last_page(None, 1), 1)
        self.assertEqual(fetch.last_page(None, 0), 0)


class ClassifyActivity(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(fetch.classify_activity("2026-10-20T10:00:00Z", False, TODAY), ("actif", 6))
        self.assertEqual(fetch.classify_activity("2026-06-01T10:00:00Z", False, TODAY)[0], "ralenti")
        self.assertEqual(fetch.classify_activity("2025-01-01T10:00:00Z", False, TODAY)[0], "abandonne")

    def test_boundaries_are_inclusive(self):
        at_active = (TODAY.toordinal() - fetch.ACTIVE_DAYS)
        iso = date.fromordinal(at_active).isoformat() + "T00:00:00Z"
        self.assertEqual(fetch.classify_activity(iso, False, TODAY)[0], "actif")

    def test_archived_wins_even_when_recent(self):
        self.assertEqual(fetch.classify_activity("2026-10-25T10:00:00Z", True, TODAY)[0], "archive")

    def test_empty_repo(self):
        self.assertEqual(fetch.classify_activity(None, False, TODAY), ("abandonne", None))


class NormalizeLicense(unittest.TestCase):
    def test_values(self):
        self.assertEqual(fetch.normalize_license("MIT"), "MIT")
        self.assertEqual(fetch.normalize_license(None), "aucune")
        self.assertEqual(fetch.normalize_license("NOASSERTION"), "non-reconnue")


class LanguageShares(unittest.TestCase):
    def test_sorted_percentages_sum_to_about_100(self):
        shares = fetch.language_shares({"C": 180, "Swift": 750, "C++": 70})
        self.assertEqual([s["language"] for s in shares], ["Swift", "C", "C++"])
        self.assertAlmostEqual(sum(s["percent"] for s in shares), 100, delta=0.2)

    def test_no_code(self):
        self.assertEqual(fetch.language_shares({}), [])


class ScanTree(unittest.TestCase):
    def present(self, paths):
        return {k: v["present"] for k, v in fetch.scan_tree(paths).items()}

    def test_detects_each_marker(self):
        result = self.present([
            ".github/workflows/ci.yml",
            "src/parser.test.ts",
            "docs/index.md",
            "deploy/docker-compose.yml",
            "plugin/.claude-plugin/plugin.json",
        ])
        self.assertEqual(result, {"ci": True, "tests": True, "docs": True, "docker": True, "claude_code": True})

    def test_test_directories_and_language_conventions(self):
        for path in ("tests/fixtures/a.json", "pkg/server_test.go", "test_api.py", "Sources/FooTests.swift"):
            self.assertTrue(self.present([path])["tests"], path)

    def test_ignores_vendored_code(self):
        result = self.present(["node_modules/x/test/a.js", "vendor/y/Dockerfile"])
        self.assertFalse(result["tests"])
        self.assertFalse(result["docker"])

    def test_bare_repo_has_no_markers(self):
        self.assertFalse(any(self.present(["README.md", "src/main.rs"]).values()))

    def test_lookalikes_are_not_markers(self):
        # Un fichier nommé comme un dossier de docs, ou un workflow hors .github/workflows.
        result = self.present(["src/docs.ts", "scripts/workflows/build.yml", "contest/main.py"])
        self.assertEqual(result, {"ci": False, "tests": False, "docs": False, "docker": False, "claude_code": False})

    def test_evidence_is_capped(self):
        paths = [f"tests/t{i}.py" for i in range(10)]
        self.assertEqual(len(fetch.scan_tree(paths)["tests"]["evidence"]), fetch.MAX_EVIDENCE)


class PickManifests(unittest.TestCase):
    def test_root_first_then_depth(self):
        picked = fetch.pick_manifests(["packages/core/package.json", "package.json", "a/b/c/d/Cargo.toml", "go.mod"])
        self.assertEqual(picked, ["go.mod", "package.json", "packages/core/package.json"])

    def test_skips_vendored_and_caps(self):
        paths = ["node_modules/x/package.json"] + [f"p{i}/package.json" for i in range(20)]
        picked = fetch.pick_manifests(paths)
        self.assertNotIn("node_modules/x/package.json", picked)
        self.assertEqual(len(picked), fetch.MAX_MANIFESTS)


if __name__ == "__main__":
    unittest.main()
