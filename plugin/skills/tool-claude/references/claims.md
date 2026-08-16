# Geler la brochure, puis la confronter

## Extraire

Une affirmation retenue est **falsifiable** : on peut imaginer la ligne de code qui la contredit.

| À retenir | À jeter |
|---|---|
| « le graphe se reconstruit sans appeler le LLM » | « une compréhension profonde de votre code » |
| « 42 % de tokens en moins » | « radicalement plus efficace » |
| « aucune télémétrie » | « respectueux de votre vie privée » |
| « installation en une commande » | « zéro friction » |
| « fonctionne avec votre clé, votre modèle » | « ouvert et flexible » |

Numérote la liste. Elle sert de plan au temps 2 et de squelette à la section « ce qui est vrai / ce qui est gonflé » du rapport.

Les affirmations les plus rentables à geler sont celles qui portent un **chiffre**, un **absolu** (« jamais », « aucun », « toujours »), ou une **comparaison** (« 3x plus rapide que »).

## La taxonomie des chiffres suspects

### 1. La métrique auto-calculée

L'outil mesure son propre gain et affiche le résultat. Cherche la formule, pas le chiffre.

Le point d'attaque est toujours la **ligne de base** : gain = ligne de base moins coût réel, et c'est le choix de la ligne de base qui fabrique tout le résultat.

Cas de référence, graft 0.11.0, `src/context/savings.ts:42-53` : `tokens saved = taille entière des fichiers couverts moins taille du pack rendu`. La ligne de base suppose que l'agent aurait ouvert chaque fichier concerné en entier. C'est le contrefactuel le plus favorable possible. Un agent qui aurait grepé puis lu quarante lignes « économise » quand même douze mille tokens.

Aggravant, à chercher systématiquement : est-ce que l'outil **fait réciter son chiffre par l'agent** à l'utilisateur ? Chez graft, la consigne est injectée à trois endroits pour être sûre de passer (`src/context/savings.ts:60-62`, `src/claude/format.ts:220`, `skill-template.ts:130-138`), et un hook reparse le chiffre pour alimenter la statusline. L'outil fabrique sa métrique, la fait annoncer par l'agent, puis l'affiche comme un fait.

### 2. Le benchmark sans harness

Des chiffres impressionnants, aucun moyen de les rejouer. Cherche le répertoire de tâches, le script d'exécution, le jeu de données, la configuration des deux bras. Absent : `invérifiable`.

Ne confonds pas « ils citent un benchmark public » et « leur run est reproductible ». Citer SWE-bench ne donne rien si le jeu d'instances, les prompts et les limites de tours ne sont pas publiés.

### 3. Le « jusqu'à »

« Jusqu'à 4x moins cher » décrit le meilleur cas d'un corpus choisi par le vendeur. Cherche la moyenne, cherche le pire cas, cherche la taille du corpus. Un tableau qui donne le meilleur cas sans la distribution est une brochure.

### 4. Le corpus complaisant

Regarde sur quoi ils ont mesuré. Un outil d'indexation testé sur un dépôt de dix mille fichiers donnera des chiffres qui n'ont aucun rapport avec un dépôt de cent fichiers. La question à poser au tableau : est-ce que mon usage ressemble à leur corpus ?

Cas de référence : graft mesure sur django et sur son propre repo. Nos dépôts font quelques centaines de fichiers TypeScript, où l'agent s'oriente déjà en trois greps.

### 5. Le défaut qui n'est pas celui de la brochure

Vérifie que la fonctionnalité vantée est **celle qui s'installe**. L'argumentaire porte souvent sur la couche haute, et la commande d'installation ne construit que la couche basse.

Cas de référence : tout le README de graft vend des nœuds en prose écrits par un modèle. `graft init` ne les construit pas (`src/cli.ts:182`, `:230`). Il faut `graft build --deep`, une clé API, et payer un passage LLM sur chaque fichier du dépôt.

## Vérifier que ce que l'outil nomme existe

Les prompts, skills et documentations d'un outil citent des noms : subagents, outils MCP, commandes, flags, variables d'environnement. Ces noms pourrissent en silence, parce que rien ne les teste.

Liste-les et vérifie-les un par un contre le système réel. Une commande qui n'existe pas dans un prompt injecté à chaque session, c'est du token dépensé pour envoyer l'agent dans le mur.

Cette règle vient du harnais local, pas d'un repo tiers : au 2026-08-16, `~/.claude/hooks/freshness-check.py` citait six pointeurs d'outils, quatre étaient morts (`perplexity-web-search`, `fast-websearch`, `/tech-deep-research`, un préfixe MCP d'un plugin désinstallé). Applique-la d'abord au tiers, puis à toi-même.

## Ce qui compte comme preuve

Un verdict `confirmé` ou `gonflé` porte un `fichier:ligne`. Pas un nom de fichier, pas « quelque part dans le module de retrieval ». La ligne.

Un verdict qui ne peut pas porter de ligne est `invérifiable`, et le rapport dit ce qui manquait pour trancher.
