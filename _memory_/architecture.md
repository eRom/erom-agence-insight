# Architecture

Mise à jour : 2026-08-15

## Objectif

Plugin Claude Code `erom-insight` (repo `erom-agence-insight`). Il explore un repo GitHub tiers et en extrait ce qui vaut d'être repris dans une config Claude Code. Livrable : un rapport classé or / argent / bronze, archivé et daté.

## Stack

Aucun code exécutable. Le plugin est fait de Markdown. Les dépendances externes sont `gh` (authentifié), `git`, `trash`, et les agents Claude Code en modèle `sonnet`.

## Découpage

**Par nature de la cible, pas par étape de pipeline.** La skill `harness` couvre les harnais et agents CLI (dsh, opencode, crush, goose). Les familles suivantes (éditeur, outil) seront des skills sœurs. Le socle commun sera extrait quand la deuxième famille existera, pas avant.

```
plugin/                      tout le publiable, envoyé sur la marketplace
  .claude-plugin/plugin.json
  agents/                    2 agents
  skills/harness/            1 skill + 3 références
docs/                        hors plugin publié
  fixtures/                  rapport de référence servant de test d'acceptation
  superpowers/{specs,plans}/
_memory_/
```

## Flux

Sept temps, un seul arrêt utilisateur, placé juste avant la dépense :

1. **vérification** `gh api repos/<owner>/<repo>`, s'arrête net si le repo n'existe pas
2. **reconnaissance** clone shallow dans le scratchpad, la session mère lit elle-même et assigne des chemins de départ disjoints par facette
3. **arrêt** brief de 10 lignes, Romain valide ou corrige l'intention
4. **swarm** N agents `insight-lecteur`, spawnés séquentiellement
5. **réfutation** 1 agent `insight-refutateur` reçoit les seules affirmations de manque et doit les détruire
6. **rapport** synthèse, écriture dans `~/.claude/erom-plugin-artefacts/insights/`, `SendUserFile`
7. **nettoyage** `trash` du clone et du scratchpad

## Deux modes d'entrée

| Entrée | Mode | Clone | Nettoyage |
|---|---|---|---|
| URL ou slug GitHub | `remote` | oui, scratchpad | `trash` |
| chemin d'un dossier | `local` | non | rien, dossier jamais touché |

## Décision structurante

Le temps 5 (réfutation) existe à cause d'une erreur réelle : une trouvaille avait été classée or sur un manque de Claude Code jamais vérifié, et le chantier lancé puis annulé. La charge de la preuve remonte donc avant le classement.
