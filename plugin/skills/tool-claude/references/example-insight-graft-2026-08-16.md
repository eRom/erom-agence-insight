---
outil: nanonets/graft
url: https://github.com/nanonets/graft
paquet: "@nanonets/graft 0.11.0"
mode: remote
date: 2026-08-16
licence: MIT
langage: TypeScript
verdict: ne-pas-installer
claims_confirmes: 5
claims_gonfles: 4
gestes_voles: 5
patchs_appliques: 1
---

# Insight : graft (nanonets), 2026-08-16

Repo analysé : https://github.com/nanonets/graft (`@nanonets/graft` 0.11.0, MIT, TypeScript, 15 400 lignes de src, 67 fichiers de test).
Méthode : clone, lecture du code d'intégration Claude Code, des hooks, du moteur de retrieval et de la comptabilité de tokens. Les affirmations ci-dessous sont ancrées sur `fichier:ligne`.

---

## Verdict en trois lignes

1. Le code est sérieux : tree-sitter + BM25 + centralité de graphe, fail-soft partout, commentaires ancrés sur de vrais incidents. Pas de vaporware.
2. La promesse « 4x moins cher » est invérifiable : aucun harness de benchmark n'est publié dans le repo, et le compteur d'économies embarqué est auto-servi par construction.
3. La vraie valeur pour nous n'est pas l'outil, ce sont cinq gestes de conception de hooks qu'ils ont payés en incidents et documentés dans le code.

---

## Ce que c'est vraiment, sans la brochure

Un indexeur de code qui produit deux graphes et six commandes de lecture.

**Couche structurelle (par défaut, 0 $, sans clé)**
- Parse tree-sitter de tout le repo. Pleine fidélité sur TS/JS, Python, Go, Java. Symboles + arêtes d'appel par extracteur générique sur 14 autres langages. Arêtes de compilateur en option via LSP.
- Produit `graft/.graph/wiring.json` : qui appelle qui, par symbole.
- `graft ask` est un moteur de recherche classique : BM25 sur le corps, idf, poids de centralité de graphe, routage vers une réponse structurelle quand la requête nomme un symbole. Zéro embedding, zéro LLM (`src/ask/ask.ts:13`, `:206`, `:333`).

**Couche prose (option `--deep`, votre clé, votre argent)**
- Un LLM résume chaque fichier, puis regroupe en nœuds markdown avec des liens typés.
- C'est le cœur de l'argumentaire du README (« de vraies explications, pas une liste de symboles »).
- **`graft init` ne la construit pas** (`src/cli.ts:182`, `:230`). Après l'installation standard, il n'y a aucun nœud en prose. Ce qu'on obtient, c'est un index de symboles et un grep classé.

**Les six commandes**
`ask` (retrieval classé), `grep` (exhaustif, groupé par symbole englobant), `skeleton` (toutes les signatures d'un fichier, sans les corps), `callers` (arêtes exactes, `--depth all` pour la fermeture transitive), `map` (orientation repo), `check` (dérive). Exposées aussi en six outils MCP.

---

## Ce qui est vrai

- **Le call graph est un vrai manque comblé.** `graft callers <sym> --depth all` avant un refactor donne ce que grep ne donnera jamais : les fichiers frères et l'aval. Claude Code n'a pas d'équivalent natif.
- **`skeleton`** : toute l'API d'un fichier en ~200 tokens au lieu de lire le fichier. Gain réel et mesurable, sans discussion.
- **Le graphe se rafraîchit avant chaque requête**, structurellement, en millisecondes, sans appeler le LLM. Les éditions non commitées sont vues.
- **Le code d'intégration est de bonne facture.** Les hooks ne peuvent pas planter une session (try/catch partout, dégradation silencieuse), le merge de `settings.json` est idempotent et ne casse pas une statusline existante (`src/claude/settings-merge.ts:44-78`).
- **Pas de télémétrie** vers leurs serveurs. Vérifié : les seuls appels réseau sont le LLM que vous configurez et une interrogation du registre npm une fois par jour pour la mise à jour (`src/upkeep.ts:50-53`). Le README affirme « les seuls appels réseau sont les requêtes LLM que vous avez configurées » : c'est faux d'un cran, sans gravité.

## Ce qui est gonflé

**1. Le compteur d'économies note sa propre copie.**
`tokens saved = (taille entière des fichiers couverts) moins (taille du pack rendu)` (`src/context/savings.ts:42-53`, `:69-82`). La ligne de base suppose que l'agent aurait lu chaque fichier concerné **en entier**. C'est le contrefactuel le plus favorable possible. Un agent qui aurait grepé puis lu 40 lignes « économise » quand même 12 000 tokens dans cette comptabilité.

**2. Et l'agent est instruit d'annoncer ce chiffre à l'utilisateur, chaque tour.**
La consigne est injectée à trois endroits pour être sûre de passer : dans la sortie de chaque outil (`src/context/savings.ts:60-62`), dans la directive de session (`src/claude/format.ts:220`), et dans le SKILL.md (`skill-template.ts:130-138`). Texte attendu : `🌱 graft saved ~12,400 tokens this turn (3 calls)`. Un hook `PostToolUse` reparse ce même chiffre pour alimenter la statusline (`src/claude/hooks.ts:188-198`).
C'est un outil qui fabrique sa propre métrique de succès, la fait réciter par l'agent à son utilisateur, puis l'affiche à l'écran comme un fait. C'est du growth hacking dans la boucle de l'agent.

**3. Les chiffres du README ne sont pas reproductibles.**
« 162 runs contrôlés », « SWE-bench Verified 50 instances, 66 % contre 54 % ». Aucun harness, aucun script, aucun jeu de tâches dans le repo. On ne peut ni rejouer ni auditer. À traiter comme une annonce marketing, pas comme un résultat.

**4. La directive de session est impérative et prend le pas sur nos règles.**
À chaque `SessionStart`, ~2 000 caractères sont injectés (`src/claude/format.ts:203-223`) dont : « pour trouver, comprendre ou changer du code, prends graft d'abord », et « ne pipe jamais une commande graft dans head/tail » (motif réel : le clipping mange la ligne d'économies). Sur un setup qui a déjà sa doctrine, c'est un concurrent, pas un complément.

---

## Le coût réel d'une installation

| Poste | Détail |
|---|---|
| Hooks écrits | 5 entrées dans `.claude/settings.json` : `PostToolUse` x2, `UserPromptSubmit`, `SessionStart`, `Stop` (`src/claude/settings-merge.ts:22-42`) |
| Latence par tour | `UserPromptSubmit` lance un `graft ask` en processus fils sur **chaque** prompt de 12 caractères ou plus, budget 15 s (`src/claude/hooks.ts:16`, `:255`) |
| Tokens par session | ~500 à 700 tokens de directive au `SessionStart`, plus un pack de pointeurs par prompt qui passe les deux portes |
| Écritures hors repo | Si `~/.codex/` existe, `init` touche `config.toml`, `hooks.json` et pose un shim, **pour tous vos repos** |
| Installation | `npm install -g @nanonets/graft`, bloqué par `guard-tools.sh`. Contournement nécessaire, et le paquet a des dépendances natives tree-sitter |
| Statusline | Prend la place de la vôtre si vous n'en avez pas ; sinon `init` la laisse et prévient |

Pour nos repos (quelques centaines de fichiers TypeScript), le rapport est mauvais : cinq hooks et un fils par prompt pour indexer un repo que l'agent parcourt déjà en trois greps.

---

## Ce qu'on vole (le vrai butin)

Ces cinq gestes viennent de leurs propres échecs, documentés dans le code. Ils valent plus que l'outil.

**1. Un rappel répété devient du papier peint. Plafonnez-le.**
`NUDGE_CAP = 2` (`src/claude/format.ts:152`), commentaire : « une ligne qui apparaît à chaque tour cesse d'être lue ; deux suffisent à ancrer l'habitude ».
Application directe chez nous : notre hook `UserPromptSubmit` de fraîcheur crache le même bloc à **chaque** prompt. Deux fois par session suffirait, ou une fois par déclencheur nouveau.

**2. Une porte de nouveauté sur ce qui est injecté.**
Ils gardent la trace des pointeurs déjà injectés dans la session et suppriment les doublons ; si tout est déjà vu, ils n'injectent rien (`src/claude/format.ts:185-201`). Un contexte réinjecté est du plein tarif pour une information que le modèle a déjà.

**3. Push vers pull : injecter des adresses, pas du contenu.**
Commentaire à `src/claude/hooks.ts:250-254` : les tokens injectés par prompt sont de l'entrée fraîche à plein tarif à chaque tour, contrairement à l'orientation de `SessionStart` qui est mise en cache. Donc le pack porte des localisateurs, jamais du code inliné ; l'agent tire lui-même s'il en veut.
Le contre-incident est documenté à `src/claude/format.ts:134-143` : leur premier seuil était trop bas, un pack faible passait, se lisait comme de l'orientation et **supprimait** l'appel de retrieval qu'il aurait dû déclencher. Résultat tracé : « l'agent n'a pas tiré. Il a grepé 38 fois. » Un contexte injecté médiocre est pire que pas de contexte.

**4. L'information critique va en tête de sortie, jamais en pied.**
`src/context/savings.ts:84-91` : les agents pipent dans `head`, les hosts tronquent par la fin. Tout ce qui doit survivre se met en première ligne. Vaut pour nos propres sorties d'outils et de scripts.

**5. Un hook lit son propre timeout installé au lieu de le coder en dur.**
`src/claude/hooks.ts:55-79` : mettre à jour le paquet npm ne réécrit pas les `settings.json` déjà posés. Un fils calibré sur le nouveau budget se fait tuer par l'ancien, et le hook meurt avant d'émettre quoi que ce soit. Ils relisent donc le timeout réellement présent dans `.claude/settings.json` au runtime.
Notre équivalent : tout plugin qui pose des hooks chez l'utilisateur porte cette dette de version.

**Bonus, à parquer :** leur `.claude/proven-config.json` référence un outil tiers, `ruflo`, qui accorde les paramètres de ranking contre un corpus étiqueté avec un delta sur jeu retenu, un test red/blue et un canari. Piste pour plus tard si on veut calibrer des paramètres de prompt autrement qu'au doigt mouillé.

## Ce qu'on ne vole pas

- La métrique d'économies contrefactuelle. Si un jour on mesure des tokens, on mesure la consommation réelle A/B, pas un « ce que tu aurais lu sinon ».
- Faire réciter à l'agent l'éloge de l'outil en fin de tour.
- Une directive de session impérative qui dit « prends mon outil d'abord ». Nos règles passent avant celles d'une dépendance.

---

## La mesure

Les gestes 1, 2, 3 et 4 visaient tous le même fichier : `~/.claude/hooks/freshness-check.py`, le hook `UserPromptSubmit` qui injecte un rappel de vérifier les versions en live. Mesure faite avant d'écrire une ligne de patch.

**Corpus** : 400 fichiers de session, 1066 vrais prompts utilisateur. Le filtrage est la moitié du travail : un transcript contient des enregistrements `type: user` qui ne sont pas des prompts tapés (chargements de skill marqués `isMeta`, notifications de tâche, messages entre sessions, tours de sous-agents). Sans filtre, le taux de déclenchement mesuré était de 57 %. Avec, 20 %. Le premier chiffre aurait justifié un chantier trois fois trop gros.

**État initial**

| Nombre | Valeur |
|---|---|
| Déclenchements | 217 sur 1066 prompts, soit 20 % |
| Coût | 46 367 tokens sur le corpus, 215 tokens par injection |
| Concentration | une session encaissait 66 fois le même bloc |
| Cause dominante | 89 % des déclenchements venaient d'un seul motif, celui qui matche « nouvelle », « dernier », « actuel », « stable », « sortie » |

Le quatrième nombre est celui qui a changé le patch. Le geste volé était le plafond ; le vrai problème était un motif trop large qui matchait du français ordinaire.

**Défaut trouvé en chemin, indépendant de graft.** Le rappel citait six pointeurs d'outils. Quatre étaient morts : `perplexity-web-search` et `fast-websearch` n'existent pas (les vrais noms sont `search-perplexity` et `search-builtin`), `/tech-deep-research` n'existe ni en commande ni en skill, et le préfixe MCP cité appartient à un plugin non installé. Le hook dépensait 215 tokens pour envoyer l'agent vers des outils fantômes.

**Le patch appliqué**

- Précision : un signal faible (« nouvelle », « dernier ») ne déclenche plus seul, il lui faut un signal moyen ou fort à côté.
- Plafond : deux injections par session, puis silence.
- Nouveauté : réinjection seulement si un déclencheur jamais vu apparaît.
- Push vers pull : liste d'outils à la première injection seulement, règle seule ensuite. 863 caractères passent à 543 puis 250.
- Règle en tête : la partie actionnable est en ligne 2 au lieu d'être en pied, où une troncature la mangeait.

**Résultat**

| | Avant | Après |
|---|---|---|
| Déclenchements | 217 | 52 |
| Tokens injectés | 46 367 | 6 392 |
| Économie | | 86 % |

**Jeu de cas écrit à la main** : 9 sur 10 des cas qui doivent se déclencher passent, 10 sur 10 des cas qui doivent rester muets sont muets. Le cas raté, « on passe à React 19 », ratait déjà avant : c'est un trou préexistant, pas une régression, et il n'a pas été bouché parce que la rustine matcherait « lot 2 » et « ligne 42 ».

**Cas perdus** : tous vérifiés un par un contre l'ancien module. Du bruit sans exception (messages entre sessions, reprises après compaction, « ouvre une nouvelle session », prompts de revue de code).

**Suite de test installée** : `python3 ~/.claude/hooks/freshness-check.test.py`, 10 invariants de comportement, verts. Elle n'assert aucun compte figé et ne lit pas le source du fichier testé.

---

## Recommandation

**Ne pas installer.** Le rapport coût/bénéfice est défavorable sur nos tailles de repo, et l'outil se met en conflit avec notre doctrine de session.

**À surveiller :** `callers --depth all` et `skeleton` sont deux vrais manques de Claude Code. Si un jour on travaille sur un repo tiers de plusieurs milliers de fichiers, graft en lecture seule via ses commandes CLI (sans `init`, sans hooks, sans statusline) est une option honnête : `npx @nanonets/graft build` puis `graft callers`. Toute la valeur structurelle est là, sans aucune des ficelles.

**Ce qui ferait changer d'avis :** un dépôt de travail au dessus de deux mille fichiers, ou une session où le call graph manque vraiment. Alors on installe la couche CLI seule, jamais `init`.

---

## Couverture et limites

- **Lu** : l'intégralité du README, le code d'intégration Claude Code (`src/claude/`, 1089 lignes, hooks et formatage lus en entier), la comptabilité de tokens (`src/context/savings.ts`), la fusion des réglages, le gabarit de skill, le scoring de `src/ask/ask.ts` en lecture ciblée, le manifeste de paquet, le script de post-installation.
- **Non lu** : les extracteurs tree-sitter par langage (`src/graph/`, ~4000 lignes), la couche LSP, le visualiseur, les 67 fichiers de test.
- **Jamais exécuté.** graft n'a été ni installé ni lancé. Aucun chiffre de ce rapport ne vient d'un run de graft ; les mécanismes cités viennent du code lu, les chiffres du vendeur sont signalés comme tels et jamais mélangés aux chiffres mesurés localement.
- **Le benchmark n'a pas été rejoué** parce qu'il n'est pas publiable en l'état : aucun harness, aucun jeu de tâches dans le repo.
- **Aucune tentative d'injection rencontrée.** Les gabarits de prompt du repo sont impératifs envers l'agent qui installe graft, ce qui est leur fonction, mais rien n'y vise un agent qui lirait le repo.
- **Version** : `@nanonets/graft` 0.11.0, commit `d834ca2`, cloné le 2026-08-16. Projet en mouvement rapide, ces conclusions vieilliront vite.
