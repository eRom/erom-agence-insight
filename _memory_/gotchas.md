# Pièges

Mise à jour : 2026-08-16

## Publication

**La description de l'entrée marketplace duplique des chemins du plugin, et pourrit en silence.** Le commit `c684ac6` a renommé le répertoire d'artefacts `~/.claude/erom-plugins/` en `erom-plugin-artefacts` dans ce repo. La description de `erom-insight` dans `~/dev/erom-marketplace/.claude-plugin/marketplace.json` pointait toujours l'ancien chemin le 2026-08-16, corrigée dans `8e52192`. Rien ne relie les deux repos : un renommage ici n'atteint jamais la marketplace. À la release suivante, relire la description de l'entrée en entier, pas seulement la version.

**Publier ne rend pas la skill utilisable en local.** Au 2026-08-16, après la release 0.4.0, `erom-insight@erom-marketplace` valait `false` dans `enabledPlugins` de `~/.claude/settings.json`, le cache s'arrêtait à `0.3.0`, et `installed_plugins.json` n'avait qu'un enregistrement de scope `user` sur cette même version. Deux gestes séparés restent nécessaires après un push : `claude plugin update erom-insight@erom-marketplace`, puis l'activation via `/plugin`.

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

**Un `grep` avec une regex large sur le binaire Claude Code dépasse les 120 s** et part en tâche de fond. Utiliser `strings`, ou des motifs courts avec `grep -ao`. Le binaire grossit vite : 45 Mo au 2026-08-15, **293 Mo** en 2.1.233 au 2026-08-16. Le geste qui tient : `strings -n 6 <binaire> > <scratchpad>/cc-strings.txt` une fois (~472 000 lignes), puis toutes les recherches sur ce dump.

**`grep -o` avec une répétition bornée au delà de 255 est refusé par le grep BSD de macOS.** `command grep -o "async function EDe(.\{0,1800\}"` sort `grep: maximum repetition exceeds 255` et ne rend rien. Pour extraire du contexte autour d'un motif dans un gros dump, passer par `python3` avec `re.finditer` et une tranche, jamais par `grep -o`. Re-testable en une commande.

**Faux positif de recherche à connaître :** « gaspillage » contient « pillage ». Une vérification du vocabulaire doit chercher en mot entier (`grep -niE '\b(...)\b'`).

**`grep -rn ... | grep -v <motif>` filtre aussi sur le chemin**, que `-rn` préfixe à chaque ligne. Pendant le renommage `tool` en `tool-claude` le 2026-08-16, `grep -v "tool-claude"` a masqué toutes les occurrences réelles restées dans `plugin/skills/tool-claude/SKILL.md`, dont le `name:` du frontmatter. Le contrôle a conclu « aucune occurrence » à tort. Filtrer sur le champ, pas sur la ligne entière, ou vérifier fichier par fichier.

## Vérifier un fait sur Claude Code

Source : session `tool-claude` sur `awrshift/claude-memory-kit`, 2026-08-16.

**La documentation en ligne est tronquée par `WebFetch` sur les sections de contrôle de décision des hooks**, exactement celles qui servent à retoquer un claim. Deux appels sur `code.claude.com/docs/en/hooks` : le premier a rendu un tableau par événement qui s'est révélé faux sur `Stop` et incomplet sur `PreCompact`, le second a répondu `[Content truncated due to length...]` en nommant la section manquante. Au passage, `docs.claude.com/en/docs/claude-code/hooks` redirige en 301 vers `code.claude.com/docs/en/hooks`, et `WebFetch` ne suit pas la redirection.

**La preuve fiable est le binaire installé**, `~/.local/share/claude/versions/<version>` (Mach-O compilé, le JS est dedans). Extraction de chaînes puis recherche Python sur le dump. C'est la source qui a tranché les deux claims porteurs du rapport, et c'est ce que le temps 2 de la skill appelle « vérifier que ce que l'outil nomme existe ». Limite à écrire dans tout rapport qui s'en sert : code minifié, noms brouillés, une seule version, donc le verdict est à re-jouer après une montée de version.

**Deux faits Claude Code établis ainsi le 2026-08-16, en 2.1.233 :**

- Un hook `PreCompact` bloque bien la compaction avec `{"decision":"block"}` ou un exit 2, mais **son `reason` n'atteint jamais le modèle**. Sur compaction automatique il part dans le logger interne et la session continue non compactée ; sur `/compact` manuel il est journalisé en `warn`, l'humain ne voit qu'une notification au texte fixe sans le motif, puis une erreur est levée. Le hook `Stop` se comporte à l'inverse : son `reason` remonte au modèle via `getStopHookMessage`. Un outil qui écrit une consigne pour l'agent dans un `reason` de `PreCompact` parle dans le vide.
- **Un `.claude/rules/` à la racine d'un projet n'est jamais chargé.** Le loader n'est appelé que sur le dossier managed (portée Managed) et le dossier rules de la config utilisateur (portée User) ; la fonction de portée Project ne charge que `CLAUDE.md`. Le champ de portée natif s'appelle `globs`, pas `paths`.

**Le slug d'un projet dans `~/.claude/projects/` ne se décode pas par substitution.** `-Users-recarnot-dev-erom-agence-insight` donne `/Users/recarnot/dev/erom/agence/insight` si on remplace chaque tiret par une barre, ce qui fait passer un projet vivant pour un projet supprimé. Le slug encode `/` **et** `.` par un tiret. Il faut une descente gloutonne testant les préfixes du plus long au plus court, avec et sans point initial, et accepter que certains slugs restent indécodables (chemins à espaces, arobases, numéros de version). Erreur commise puis corrigée dans la session.

## Repo exploré

`deepseek-ai/deepseek-harness` : 117 Mo annoncés par l'API GitHub, 80 Mo sur disque après `git clone --depth 1`. Le garde-fou de la skill est à 500 Mo, ce repo passe donc largement. Il porte trois variantes par document (`x.md`, `x.zh.md`, `x.i18n.yaml`) : sans filtre, la reconnaissance assigne les mêmes chemins en triple.

`awrshift/claude-memory-kit` : 178 Mo annoncés par l'API GitHub, **17 Mo** sur disque après `git clone --depth 1`. L'écart tient à l'historique des révisions graphiques, et le README le dit lui-même. Un poids annoncé n'est donc pas un critère de refus : mesurer après le clone superficiel, pas avant. Le dépôt lui-même fait une cinquantaine de fichiers, aucun besoin de déléguer à `insight-lecteur`.
