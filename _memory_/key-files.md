# Fichiers clés

Mise à jour : 2026-08-23

## Plugin publiable

| Chemin | Rôle |
|---|---|
| `plugin/.claude-plugin/plugin.json` | manifeste, `name: "erom-insight"`, déclare les 2 agents et le dossier skills |
| `plugin/skills/harness/SKILL.md` | le déroulé en sept temps, l'orchestration, les consignes anti-injection de la mère |
| `plugin/skills/harness/references/facettes.md` | les 5 axes de lecture d'un harnais et la règle de disjonction |
| `plugin/skills/harness/references/calibrage.md` | combien de lecteurs, quoi faire sans `docs/`, départage par volume de doc |
| `plugin/skills/harness/references/template-rapport.md` | frontmatter et les 7 sections imposées du rapport |
| `plugin/skills/tool-claude/SKILL.md` | le déroulé de décision d'installation en sept temps, l'arrêt avant écriture locale, le bloc anti-injection renforcé |
| `plugin/skills/tool-claude/references/claims.md` | méthode d'extraction des affirmations, taxonomie des cinq familles de chiffres suspects |
| `plugin/skills/tool-claude/references/cout-installation.md` | l'inventaire à remplir en entier, et les trois postes qui décident |
| `plugin/skills/tool-claude/references/mesure.md` | corpus locaux, filtre des faux prompts utilisateur, forme du jeu de cas |
| `plugin/skills/tool-claude/references/template-rapport.md` | frontmatter et les 10 sections imposées, dont `verdict` à 4 valeurs |
| `plugin/skills/skill-claude/SKILL.md` | le déroulé de jugement d'une skill tierce en cinq temps, la sécurité bloquante, le protocole d'arrêt, le piège `[REDACTED]` du harnais, le bloc anti-injection à exposition maximale |
| `plugin/skills/skill-claude/references/secu.md` | la ligne entre arrêter et rapporter : 7 cas d'arrêt, ce qui se rapporte sans arrêter, ce qui est normal, lecture d'un rouge, le piège `[REDACTED]`, ce que le scanner ne voit pas |
| `plugin/skills/skill-claude/references/template-rapport.md` | frontmatter et les 8 sections imposées, `verdict` à 4 valeurs dont `stop-secu` |
| `plugin/skills/skill-claude/scripts/secu-scan.py` | le scanner : inventaire, surfaces déclarées (frontmatter, hooks, MCP, plugin.json), hôtes, motifs en 3 niveaux et une vingtaine de familles |
| `plugin/skills/skill-claude/scripts/secu-scan.test.py` | la suite de cas du scanner : ce qui doit se déclencher, les faux positifs réels (Linear, erom-insight, skill-creator), l'invariant « n'écrit rien » |
| `plugin/agents/insight-lecteur.md` | lecteur d'une facette ou d'une zone, `tools: Read, Grep, Glob` seulement, livrable en 4 sections |
| `plugin/agents/insight-refutateur.md` | détruit les affirmations de manque, charge de la preuve à sa charge, utilisé par `harness` seul |
| `plugin/README.md` | présentation des deux skills, deux modes, composants |

## Hors plugin

| Chemin | Rôle |
|---|---|
| `docs/fixtures/rapport-deepseek-harness.md` | rapport de référence de `harness`, cible de densité et test d'acceptation |
| `docs/insight-graft-2026-08-16.md` | rapport de référence de `tool-claude` sur `nanonets/graft`, cité comme fixture par son template ; porte les 10 sections dont la mesure et la couverture |
| `docs/fixtures/skill-piegee/` | skill malveillante inerte (pipe vers shell sur TLD `.invalid`, hôte d'exfiltration à identifiant nul, `U+200B`, commentaire HTML d'injection) : cas d'arrêt de `skill-claude` |
| `docs/evals/skill-claude/evals.json` | les 3 cas d'éval de `skill-claude` : Linear distant en sous-dossier, launchd local sain, fixture piégée |
| `docs/acceptation-2026-08-15-dsh.md` | constat du rejeu : 4 critères, 6 défauts trouvés et corrigés, limites du test |
| `docs/superpowers/specs/2026-08-15-erom-insight-harness-design.md` | la spec, avec ses lignes `Battu :` |
| `docs/superpowers/plans/2026-08-15-erom-insight-harness.md` | le plan en 5 tâches, porte les deux commandes du gate |
| `_memory_/ONBOARD.md` | projet Linear (team EAT) et canal Slack, appartient à un autre outil, ne pas modifier |

## Sorties, hors repo

`~/.claude/erom-store/insights/<owner>-<repo>-<YYYY-MM-DD>.md` : les rapports de `harness`. Un exemplaire existe pour `deepseek-ai/deepseek-harness`.

`~/.claude/erom-store/insights/tool-<owner>-<repo>-<YYYY-MM-DD>.md` : les rapports de `tool-claude`. Le préfixe `tool-` est ce qui les distingue, il n'a pas suivi le renommage de la skill en `tool-claude`.

`~/.claude/erom-store/insights/skill-<owner>-<repo>[-<chemin-en-tirets>]-<YYYY-MM-DD>.md` : les rapports de `skill-claude` ; `skill-local-<dossier>-<date>.md` en mode local sans remote.

## Contrat entre composants

Le lecteur écrit ses affirmations de manque sur une ligne dédiée, avec la formule exacte `manque supposé : <capacité>`. La session mère extrait ces lignes et elles seules pour alimenter le réfutateur. Casser cette formule casse le temps 5.
