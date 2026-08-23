# erom-insight

Explore un repo GitHub tiers et en extrait ce qui vaut d'être repris dans une config Claude Code.

Trois skills, trois questions différentes.

| Skill | Cible | Question à laquelle elle répond |
|---|---|---|
| `harness` | harnais et agents CLI concurrents (dsh, opencode, crush, goose) | qu'est-ce qu'ils ont que je n'ai pas ? |
| `tool-claude` | outils qui se branchent sur Claude Code (indexeur, MCP, optimiseur de contexte) | est-ce que je l'installe ? |
| `skill-claude` | skills et plugins Claude Code tiers | est-ce que je peux l'installer sans risque, et est-ce que ça vaut le coup ? |

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

## `skill-claude` : juger une skill avant de l'installer

```
/erom-insight:skill-claude <owner/repo | url GitHub (repo ou tree/<branche>/<chemin>) | chemin local>
```

Cinq temps. La sécurité passe en premier, et si elle ne passe pas, tout s'arrête là.

1. **Sécurité, bloquante.** Un scanner en lecture seule (`scripts/secu-scan.py`, stdlib) balaie ce que l'oeil saute : pipe vers un shell, décodage puis exécution, secret en dur, hôte d'exfiltration connu, caractères Unicode invisibles, HTML caché dans un Markdown, consignes d'injection, hooks, serveurs MCP, permissions demandées. Trois niveaux : `rouge` (certitude mécanique), `orange` (à juger), `info`. Chaque rouge se lit à sa ligne et se conclut inerte avec preuve, ou confirmé. Un rouge confirmé arrête tout : alerte immédiate, rapport minimal `stop-secu`, clone supprimé.
2. **Le pourquoi** : pour qui, quel problème, et l'écart entre ce que la description vend et ce que le corps fait.
3. **Le comment** : où ça tourne, comment ça s'authentifie, ce qu'il faut avoir, ce qui sort du Mac et vers où, pour quel harnais c'est écrit (une skill pensée pour Claude Tag casse autrement dans Claude Code).
4. **La véracité** : les promesses de la description contre le corps, ce qu'elle nomme existe-t-il (scripts, outils, endpoints), les scripts font-ils ce que la prose dit, `fichier:ligne` obligatoire, un fait d'API vérifié contre la doc officielle.
5. **Le verdict**, après le déjà-vu local (ce que Romain a déjà qui couvre le besoin) : `installer`, `trash` ou `refaire` (l'idée vaut, la skill non), toujours avec la condition qui le ferait changer.

La skill n'installe jamais rien et n'exécute jamais rien de la cible. Le scanner a sa suite de cas à côté de lui (`scripts/secu-scan.test.py`, deux listes : ce qui doit se déclencher, et les faux positifs relevés dans des skills réelles).

## Deux modes d'entrée, pour les trois skills

| Entrée | Mode | Clone | Nettoyage |
|---|---|---|---|
| URL ou slug GitHub | `remote` | oui, dans le scratchpad de session | `trash` du clone en fin de course |
| URL GitHub d'un sous-dossier (`tree/<branche>/<chemin>`), `skill-claude` seulement | `remote` | oui, le repo entier, travail dans le sous-dossier | `trash` du clone |
| chemin d'un dossier existant | `local` | non | rien, le dossier n'est jamais touché |

En mode `local`, si le dossier a un remote GitHub, owner et repo en sont dérivés et les métadonnées GitHub sont récupérées quand même.

Les rapports sont écrits dans `~/.claude/erom-store/insights/`, puis envoyés en pièce lisible sur mobile.

## Composants

| Composant | Rôle |
|---|---|
| skill `harness` | le déroulé de veille concurrentielle, de la vérification au nettoyage |
| skill `tool-claude` | le déroulé de décision d'installation, de la brochure au patch mesuré |
| skill `skill-claude` | le déroulé de jugement d'une skill tierce, de la sécurité bloquante au verdict |
| script `skill-claude/scripts/secu-scan.py` | le scanner de sécurité en lecture seule, avec sa suite de cas |
| agent `insight-lecteur` | lit une facette ou une zone, en lecture seule stricte (`Read`, `Grep`, `Glob`) |
| agent `insight-refutateur` | détruit les fausses trouvailles, preuve à l'appui |

## Ce que ce plugin n'est pas

Il explore un repo **tiers**. La rétro du harnais local, elle, est la skill `harness-review`, et le diagnostic des skills déjà chargées est la commande native `/skill-doctor`.

## Licence

MIT
