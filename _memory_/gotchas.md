# Pièges

Mise à jour : 2026-08-15

## Outillage plugin

**`claude plugin validate --strict` ne lit pas le frontmatter des agents ni des skills.** Vérifié en retirant le champ `name` d'un agent sur une copie : la validation passe sans un mot. Elle ne contrôle que la présence des fichiers déclarés dans le manifeste (`agents[0]: Path not found: ...` si le chemin est mort). D'où le second contrôle maison dans `patterns.md`.

**Un plugin ne peut pas porter de permissions.** Champ `permissions` injecté dans un manifeste de test : `Unknown field 'permissions'. Claude Code ignores it at load time.` Les permissions n'existent qu'en scope user, projet, local ou `--settings`, donc liées à un répertoire et jamais à un plugin. Une skill de plugin s'invoquant depuis n'importe quel dossier, il n'existe aucun moyen de restreindre des permissions « au périmètre de ce plugin ».

## Agents

**Ne pas donner de `name` à un agent one-shot.** Un agent nommé devient un teammate adressable : il se signale disponible et son texte final ne remonte pas à la session mère tant qu'on ne le lui redemande pas par `SendMessage`. Constaté au rejeu : 3 lecteurs sur 5 ont dû être relancés, 2 n'avaient toujours rien rendu au moment où on les a respawnés en anonymes. Sans `name`, le texte final est la valeur de retour.

**Un agent doté de Bash laisse des résidus.** Le réfutateur a laissé 45,4 Mo dans le scratchpad (extraction de chaînes du binaire Claude Code). Le nettoyage doit balayer le scratchpad, pas seulement le répertoire du clone.

**Deux exécutions du même prompt sur la même facette divergent nettement en trouvailles**, tout en concordant sur le fond. Un passage unique ne rend donc pas tout ce qu'il y a à prendre. `[candidat 1x - rejeu dsh du 2026-08-15, facettes memoire et extensibilite]`

## Sandbox et permissions

Source : documentation officielle du sandboxing, lue le 2026-08-15.

**Le sandbox borde Bash et ses sous-processus, rien d'autre.** `Read`, `Edit` et `Write` passent par le système de permissions. Conséquences dans les deux sens : un `permissions.deny` sur `Read(...)` n'empêche pas un `cat` lancé via Bash, et il ne casse ni `git`, ni `gh`, ni `ssh`, qui sont des sous-processus.

**Les subagents tournent dans le même process que le parent et héritent de sa configuration sandbox.**

**Les syntaxes de chemin diffèrent entre les deux mécanismes.** `sandbox.filesystem` utilise les conventions standard (`/tmp/build` est absolu). Les règles de permission `Read` et `Edit` utilisent `//chemin` pour absolu et `/chemin` pour relatif au projet.

**Précédence en lecture : le plus spécifique gagne.** `denyRead: ["~/"]` plus `allowRead: ["~/projects"]` rend `projects` lisible. `allowRead: ["~/"]` plus `denyRead: ["~/.env"]` garde `.env` bloqué. Un allow large ne peut donc pas ré-exposer un secret nommé. Préférer cette approche à une liste noire, qui oublie toujours quelque chose.

**`sandbox.filesystem.disabled` n'est honoré que depuis les settings user, managed, ou le flag `--settings`.** Un repo checked-out ne peut pas couper l'isolation filesystem.

**Rien dans la configuration ne couvre l'injection de prompt.** C'est le seul risque résiduel de ce plugin, puisque rien du repo exploré n'est jamais exécuté. La parade est dans les prompts : consignes dans le temps 2 du SKILL.md pour la mère, et dans `insight-lecteur.md` pour les lecteurs. La mère est le maillon exposé, car elle ouvre `AGENTS.md` et `CLAUDE.md` en premier et dispose de tous les outils.

## Shell et environnement

**Le glob zsh échoue quand rien ne correspond** : `plugin/skills/*/SKILL.md` sort en `no matches found` et interrompt la boucle. Utiliser `find` dans les scripts de contrôle.

**Un `grep` avec une regex large sur le binaire Claude Code (45 Mo) dépasse les 120 s** et part en tâche de fond. Utiliser `strings`, ou des motifs courts avec `grep -ao`.

**Faux positif de recherche à connaître :** « gaspillage » contient « pillage ». Une vérification du vocabulaire doit chercher en mot entier (`grep -niE '\b(...)\b'`).

## Repo exploré

`deepseek-ai/deepseek-harness` : 117 Mo annoncés par l'API GitHub, 80 Mo sur disque après `git clone --depth 1`. Le garde-fou de la skill est à 500 Mo, ce repo passe donc largement. Il porte trois variantes par document (`x.md`, `x.zh.md`, `x.i18n.yaml`) : sans filtre, la reconnaissance assigne les mêmes chemins en triple.
