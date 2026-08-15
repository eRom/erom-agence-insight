# Fichiers clés

Mise à jour : 2026-08-15

## Plugin publiable

| Chemin | Rôle |
|---|---|
| `plugin/.claude-plugin/plugin.json` | manifeste, `name: "erom-insight"`, déclare les 2 agents et le dossier skills |
| `plugin/skills/harness/SKILL.md` | le déroulé en sept temps, l'orchestration, les consignes anti-injection de la mère |
| `plugin/skills/harness/references/facettes.md` | les 5 axes de lecture d'un harnais et la règle de disjonction |
| `plugin/skills/harness/references/calibrage.md` | combien de lecteurs, quoi faire sans `docs/`, départage par volume de doc |
| `plugin/skills/harness/references/template-rapport.md` | frontmatter et les 7 sections imposées du rapport |
| `plugin/agents/insight-lecteur.md` | lecteur d'une facette, `tools: Read, Grep, Glob` seulement, livrable en 4 sections |
| `plugin/agents/insight-refutateur.md` | détruit les affirmations de manque, charge de la preuve à sa charge |
| `plugin/README.md` | présentation, deux modes, composants |

## Hors plugin

| Chemin | Rôle |
|---|---|
| `docs/fixtures/rapport-deepseek-harness.md` | rapport de référence produit avant le plugin, sert de cible de densité et de test d'acceptation |
| `docs/acceptation-2026-08-15-dsh.md` | constat du rejeu : 4 critères, 6 défauts trouvés et corrigés, limites du test |
| `docs/superpowers/specs/2026-08-15-erom-insight-harness-design.md` | la spec, avec ses lignes `Battu :` |
| `docs/superpowers/plans/2026-08-15-erom-insight-harness.md` | le plan en 5 tâches, porte les deux commandes du gate |
| `_memory_/ONBOARD.md` | projet Linear (team EAT) et canal Slack, appartient à un autre outil, ne pas modifier |

## Sorties, hors repo

`~/.claude/erom-plugins/insights/<owner>-<repo>-<YYYY-MM-DD>.md` : les rapports produits. Un exemplaire existe pour `deepseek-ai/deepseek-harness`.

## Contrat entre composants

Le lecteur écrit ses affirmations de manque sur une ligne dédiée, avec la formule exacte `manque supposé : <capacité>`. La session mère extrait ces lignes et elles seules pour alimenter le réfutateur. Casser cette formule casse le temps 5.
