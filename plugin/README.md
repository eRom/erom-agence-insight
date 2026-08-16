# erom-insight

Explore un repo GitHub tiers et en extrait ce qui vaut d'être repris dans une config Claude Code.

Deux skills, deux questions différentes.

| Skill | Cible | Question à laquelle elle répond |
|---|---|---|
| `harness` | harnais et agents CLI concurrents (dsh, opencode, crush, goose) | qu'est-ce qu'ils ont que je n'ai pas ? |
| `tool-claude` | outils qui se branchent sur Claude Code (indexeur, MCP, optimiseur de contexte) | est-ce que je l'installe ? |

## `harness` : piller un concurrent

```
/erom-insight:harness <owner/repo | url GitHub | chemin local>
```

Elle vérifie que le repo existe, reconnaît sa structure elle-même, te montre son plan de lecture, puis lâche un swarm de lecteurs sur des facettes disjointes. Avant de classer, un agent réfutateur essaie de détruire toute trouvaille qui prétend combler un manque de Claude Code. Ce qui survit est or.

Rapport classé en trois tiers, plus une section de couverture et limites qui dit ce qui n'a pas été lu.

- **or** : faible coût, gain réel, manque confirmé par le réfutateur
- **argent** : bonnes idées à parquer, dont les trouvailles retoquées avec leur preuve
- **bronze** : leçons de design, rien à construire

## `tool-claude` : décider d'une installation

```
/erom-insight:tool-claude <owner/repo | url GitHub | chemin local>
```

Sept temps, un seul arrêt, placé juste avant la seule action irréversible.

1. **Geler la brochure** avant d'ouvrir une ligne de code. Lire le code d'abord, c'est noter sur une courbe.
2. **Confronter** chaque affirmation au code, verdict `confirmé` / `gonflé` / `invérifiable`, `fichier:ligne` obligatoire.
3. **Chiffrer le coût d'installation** : ce qui s'écrit hors du repo, ce qui est imposé au modèle à chaque tour, la latence par tour.
4. **Trier le butin.** Le vrai butin est dans les commentaires de code qui documentent un incident, pas dans le README.
5. **Mesurer** chaque geste volé sur le corpus local, avant d'écrire la moindre ligne.
6. **Rapport, puis arrêt.** Rien n'est écrit dans la configuration sans accord explicite.
7. **Appliquer** : sauvegarde, patch, suite de test installée à côté du fichier, résultat rapporté brut.

La règle qui gouverne le déroulé : **aucun patch sans mesure, aucune mesure sans un fichier cible nommé.** Un geste admirable qui n'atterrit nulle part se parque, il ne se construit pas.

Le verdict prend une de quatre valeurs : `installer`, `ne-pas-installer`, `installer-partiellement`, `surveiller`.

## Deux modes d'entrée, pour les deux skills

| Entrée | Mode | Clone | Nettoyage |
|---|---|---|---|
| URL ou slug GitHub | `remote` | oui, dans le scratchpad de session | `trash` du clone en fin de course |
| chemin d'un dossier existant | `local` | non | rien, le dossier n'est jamais touché |

En mode `local`, si le dossier a un remote GitHub, owner et repo en sont dérivés et les métadonnées GitHub sont récupérées quand même.

Les rapports sont écrits dans `~/.claude/erom-plugin-artefacts/insights/`, puis envoyés en pièce lisible sur mobile.

## Composants

| Composant | Rôle |
|---|---|
| skill `harness` | le déroulé de veille concurrentielle, de la vérification au nettoyage |
| skill `tool-claude` | le déroulé de décision d'installation, de la brochure au patch mesuré |
| agent `insight-lecteur` | lit une facette ou une zone, en lecture seule stricte (`Read`, `Grep`, `Glob`) |
| agent `insight-refutateur` | détruit les fausses trouvailles, preuve à l'appui |

## Ce que ce plugin n'est pas

Il explore un repo **tiers**. La rétro du harnais local, elle, est la skill `harness-review`.

## Licence

MIT
