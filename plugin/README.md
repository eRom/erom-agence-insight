# erom-insight

Explore un repo GitHub tiers et en extrait ce qui vaut d'être volé pour une config Claude Code.

La skill `harness` cible les harnais et agents CLI (dsh, opencode, crush, goose). Elle vérifie que le repo existe, reconnaît sa structure elle-même, te montre son plan de lecture, puis lâche un swarm de lecteurs sur des facettes disjointes. Avant de classer, un agent réfutateur essaie de détruire toute trouvaille qui prétend combler un manque de Claude Code. Ce qui survit est or.

## Invocation

```
/erom-insight:harness <owner/repo | url GitHub | chemin local>
```

Exemples :

```
/erom-insight:harness deepseek-ai/deepseek-harness
/erom-insight:harness https://github.com/sst/opencode
/erom-insight:harness ~/dev/un-repo-deja-clone
```

## Deux modes d'entrée

| Entrée | Mode | Clone | Nettoyage |
|---|---|---|---|
| URL ou slug GitHub | `remote` | oui, dans le scratchpad de session | `trash` du clone en fin de course |
| chemin d'un dossier existant | `local` | non | rien, le dossier n'est jamais touché |

En mode `local`, si le dossier a un remote GitHub, owner et repo en sont dérivés et les métadonnées GitHub sont récupérées quand même. Les lecteurs n'ont ni Bash ni Write : le dossier cible est en lecture seule par construction, pas par consigne.

## Le rapport

Classé en trois tiers, plus une section de couverture et limites qui dit ce qui n'a pas été lu.

- **or** : faible coût, gain réel, manque confirmé par le réfutateur
- **argent** : bonnes idées à parquer, dont les trouvailles retoquées avec leur preuve
- **bronze** : leçons de design, rien à construire

Il est écrit dans `~/.claude/erom-plugins/insights/<owner>-<repo>-<date>.md`, puis envoyé en pièce lisible sur mobile.

## Composants

| Composant | Rôle |
|---|---|
| skill `harness` | le déroulé complet, de la vérification au nettoyage |
| agent `insight-lecteur` | lit une facette, en lecture seule stricte (`Read`, `Grep`, `Glob`) |
| agent `insight-refutateur` | détruit les fausses trouvailles, preuve à l'appui |

## Ce que ce plugin n'est pas

Il explore un repo **tiers**. La rétro du harnais local, elle, est la skill `harness-review`.

## Licence

MIT
