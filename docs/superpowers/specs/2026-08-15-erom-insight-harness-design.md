---
sujet: plugin erom-insight, skill harness
status: proposed
date: 2026-08-15
auteur: claude-janus-4gvc
---

# Plugin erom-insight, skill `harness`

## Objet

Industrialiser l'exploration d'un repo de harness ou d'agent CLI (dsh, opencode, crush, goose) pour en extraire ce qui vaut la peine d'être repris dans la config Claude Code de Romain. Le livrable est un rapport classé or / argent / bronze, archivé et daté.

Le découpage du plugin est par **nature de la cible**, pas par étape de pipeline. Un harness se lit sur ses mécaniques d'agent ; un éditeur comme Zed se lira sur d'autres axes, avec d'autres critères de veille. `harness` est la première famille. Les suivantes viendront comme des skills sœurs.

**Battu :** un découpage en trois skills chaînées (`scout` / `swarm` / `report`). Perdu parce que les trois descriptions se marcheraient dessus au déclenchement, et que l'état devrait transiter par un fichier entre skills alors qu'aucune n'est jamais jouée seule.

**Battu :** un socle commun (`plugin/references/deroule.md`) extrait dès maintenant pour les familles futures. Perdu parce qu'on tracerait la frontière commun / spécifique à l'aveugle, sur un seul exemplaire. L'extraction se fera quand la deuxième famille existera, avec deux cas réels sous les yeux.

## Entrées

`$ARGUMENTS` résout vers un mode et un seul :

| Entrée | Mode | Clone | Nettoyage |
|---|---|---|---|
| `https://github.com/<owner>/<repo>` ou `<owner>/<repo>` | `remote` | oui, dans le scratchpad | `trash` du clone en fin de course |
| un répertoire existant (`test -d`) | `local` | non | rien, on ne touche pas au dossier |
| rien qui résout | arrêt | | demander une fois quel repo, puis stop |

En mode `local`, si le dossier a un remote GitHub (`git -C <path> remote get-url origin`), owner et repo en sont dérivés et les métadonnées GitHub sont récupérées comme en mode `remote`. Sinon owner vaut `local` et repo vaut le nom du dossier.

Le nettoyage utilise `trash`, jamais `rm`. Le clone vit dans le scratchpad de la session, donc éphémère de toute façon ; le `trash` explicite est là pour ne pas laisser plusieurs gigaoctets en place pendant des heures.

## Arborescence

```
plugin/
  .claude-plugin/plugin.json      name: "erom-insight"
  agents/
    insight-lecteur.md
    insight-refutateur.md
  skills/harness/
    SKILL.md
    references/
      facettes.md
      calibrage.md
      template-rapport.md
  README.md
  LICENSE
docs/
  fixtures/rapport-deepseek-harness.md    rapport de reference, hors plugin publie
  superpowers/specs/
```

Convention eRom vérifiée sur `erom-agence-gemini` et `erom-agence-marketing` : tout le plugin publiable vit sous `plugin/`, le nom du manifeste est court (`erom-insight`) même quand le repo porte le préfixe long, et la marketplace pointe dessus en `git-subdir` avec `path: "plugin"`.

## Déroulé

### 1. Vérification (auto)

Mode `remote` : `gh api repos/<owner>/<repo>`. Champs retenus : `full_name`, `description`, `stargazers_count`, `created_at`, `pushed_at`, `license.spdx_id`, `size`, `archived`, `language`, `default_branch`.

Sur 404, distinguer les deux cas avant de conclure : si `gh api user` répond, le token est valide, donc le repo est inexistant ou privé sans accès. Le message le dit et la skill s'arrête. C'est le geste qui justifie toute la skill : lancer un swarm sur un repo fantôme brûle du quota pour rien.

Garde-fou taille : `size` est en kilo-octets. Au dessus de 500 000 (500 Mo), la skill annonce le volume et demande avant de cloner.

Mode `local` : vérifier que le chemin existe, mesurer sa taille, et enrichir depuis GitHub si un remote est présent.

### 2. Reconnaissance (auto)

Mode `remote` : `git clone --depth 1 <url> <scratchpad>/insight-<owner>-<repo>`.

Puis, dans les deux modes, la session mère lit elle-même : arbre au niveau 2, README racine, `AGENTS.md` ou `CLAUDE.md` s'ils existent, index des docs, liste des packages.

Cette étape ne produit pas un résumé mais une **assignation** : pour chaque facette retenue, trois à huit chemins de départ nommés, disjoints entre facettes. C'est ce qui a fait fonctionner le swarm de référence. Sans chemins nommés, les lecteurs convergent tous sur les mêmes README.

### 3. Arrêt, brief à Romain

Dix lignes, pas plus :

- ce qu'est le repo, factuel : nom, âge, étoiles, licence, langage
- l'intention déduite, en une phrase
- le plan : N lecteurs, une ligne par facette

Romain valide, corrige l'intention, ou retire des facettes. C'est le seul arrêt, et il est placé juste avant la dépense.

**Battu :** un second arrêt avant le clone pour cadrer l'intention. Perdu parce que deux allers-retours sur un geste souvent lancé depuis le mobile coûtent plus qu'ils ne rapportent, et que l'intention se cadre mieux une fois la structure connue.

### 4. Swarm (auto)

N agents `insight-lecteur`, un par facette, **spawnés séquentiellement, jamais en batch parallèle**. Motif : un call qui plante tue ses voisins dans le même batch. Chaque spawn retourne immédiatement, donc le séquencement ne coûte rien en temps réel.

### 5. Réfutation (auto)

La mère extrait des rapports les seules trouvailles qui affirment un manque de Claude Code. Un agent `insight-refutateur` les reçoit, sans le reste du matériau, avec pour mission de les détruire.

Ce temps existe à cause d'une erreur réelle : dans la session de référence, une trouvaille a été classée or parce qu'elle comblait un manque supposé de Claude Code, Romain a dit GO, et un test de quatre appels d'outil a prouvé après coup que la capacité était native. Chantier annulé. La charge de la preuve remonte donc avant le classement, pas après le GO.

**Battu :** un fichier `deja-vu.md` figé listant ce que Claude Code sait déjà faire. Perdu parce qu'il pourrit à chaque release et que c'est exactement le mécanisme qui a produit l'erreur.

**Battu :** la contre-vérification faite par la session mère pendant la synthèse. Perdu parce que la même tête juge et rédige, ce qui est la configuration qui a laissé passer l'erreur.

### 6. Rapport et livraison (mère)

Synthèse, jamais une concaténation des rapports de lecteurs. Structure imposée par `template-rapport.md` :

- verdict en trois lignes
- ce que c'est
- **or** : faible coût, gain réel, manque confirmé par le réfutateur
- **argent** : bonnes idées à parquer, dont les trouvailles retoquées avec leur preuve
- **bronze** : leçons de design, rien à construire
- **déjà-vu** : ce qu'on a déjà, parfois en mieux
- **couverture et limites**, obligatoire : ce qui n'a pas été lu, le fait que rien n'a été exécuté ni testé, l'âge du repo et l'instabilité qui va avec

Écriture dans `~/.claude/erom-store/insights/<owner>-<repo>-<YYYY-MM-DD>.md`. En mode `local` sans remote, `local-<nom-du-dossier>-<date>.md`. Collision le même jour : suffixe `-2`.

Puis `SendUserFile` en `display: "render"`, et gravure des conclusions durables en mémoire.

### 7. Nettoyage (auto)

Mode `remote` uniquement : `trash` du clone. Mode `local` : rien, ni suppression ni écriture dans le dossier cible.

## Contrats des agents

### `insight-lecteur`

```
tools: Read, Grep, Glob
model: sonnet
```

Pas de Bash. On clone du code tiers non audité et on lâche des agents dedans : la lecture seule doit être structurelle, pas une consigne qu'un prompt peut contourner. En mode `local`, la même contrainte protège le repo de travail de Romain.

**Battu :** l'agent `general-purpose` du déroulé de référence. Perdu sur l'argument outils : `general-purpose` a Bash et tout le reste. Retenu de lui la raison qui l'avait fait préférer à `Explore` : un lecteur doit lire des documents entiers, pas des extraits.

Reçoit : racine absolue du repo, nom de la facette, les chemins de départ, le contexte client.

Règles permanentes, portées par l'agent et non répétées à chaque appel :

- lecture seule
- ignorer les doublons de traduction (`.zh.md`, `.i18n.yaml` et équivalents)
- au delà de 30 Ko, lecture en diagonale
- distinguer ce qui est **vu**, avec le chemin cité, de ce qui est **déduit**
- ne pas déborder sur les facettes des autres lecteurs

Livrable imposé, 600 mots maximum : 1. comment ça marche, 2. trouvailles notables avec chemins, 3. à reprendre, 4. déjà-vu.

### `insight-refutateur`

```
tools: Read, Grep, Glob, Bash, WebFetch
model: sonnet
```

Reçoit une liste d'affirmations de la forme « Claude Code ne sait pas faire X », et rien d'autre. L'isolement est délibéré : il ne doit pas être influencé par la qualité du reste du rapport.

Preuves recevables : documentation officielle Claude Code, `claude --help`, un test minimal réellement exécuté, ou un grep des settings, hooks et skills installés localement.

Rend, par affirmation : `verdict` (`deja_natif` ou `manque_tient`), `preuve` (ce qui a été fait ou lu, cité), `confiance`.

La charge de la preuve pèse sur le réfutateur : il doit démontrer que la capacité est native. S'il n'y parvient pas, le manque tient, mais le rapport cite ce qui a été cherché sans succès. Romain garde ainsi de quoi juger, ce qui manquait précisément lors de l'épisode qui a motivé cette étape.

## Facettes d'un harness

Contenu de `references/facettes.md`, le savoir-faire propre à cette skill :

1. **Boucle et contexte** : construction du tour, compaction, spill sur disque, ce que le modèle voit réellement, logs de session
2. **Outils et sandbox** : catalogue d'outils, modèle d'approbation, isolation, ce qui est bloqué et comment
3. **Mémoire et reprise** : notes de décision, état entre sessions, comportement après crash, resume
4. **Extensibilité** : plugins, skills, hooks, marketplace, comment un tiers ajoute une capacité
5. **Discipline d'exploitation** : postmortems, gouvernance de la doc, dogfooding, CI

Ces cinq axes sont ceux qui ont produit le rapport de référence sur deepseek-harness.

## Calibrage

Contenu de `references/calibrage.md`. Le nombre de lecteurs et l'orientation des facettes sont décidés à la reconnaissance, jamais codés en dur.

| Observation | Décision |
|---|---|
| moins de 5 packages ou moins de 10 fichiers de doc | 2 à 3 lecteurs, facettes fusionnées |
| taille moyenne, `docs/` fourni | 5 lecteurs, les 5 facettes |
| monorepo large | jusqu'à 7, jamais plus : au delà la synthèse devient une soupe |
| pas de `docs/` | lecteurs orientés code source, tests et README de packages |
| repo minuscule | pas de swarm, lecture directe par la mère |

**Battu :** figer 5 lecteurs, comme dans le déroulé de référence. Perdu parce que ce déroulé a été validé sur un seul repo, exceptionnellement bien documenté. Le premier repo sans `docs/` casserait la règle.

## Frontmatter du rapport

```yaml
---
repo: deepseek-ai/deepseek-harness
url: https://github.com/deepseek-ai/deepseek-harness
mode: remote
date: 2026-08-15
repo_cree: 2026-08-13
repo_pousse: 2026-08-15
etoiles: 100000
licence: MIT
facettes: [boucle, outils, memoire, extensibilite, exploitation]
lecteurs: 5
session: claude-janus-4gvc
session_id: e394bc44-0e93-4629-8a5b-935c03c46c00
bridge_url: https://claude.ai/code/session_013N7rdGvb6vG5z6mYm74nyM
---
```

Les trois derniers champs viennent de `~/.claude/skills/session-whoami/scripts/*.sh --json`, qui vit dans le global. Si le script est absent, le frontmatter est écrit sans eux : dégradation propre, pas d'échec.

## Hors périmètre

- une skill pour une autre famille de cible (éditeur, outil, bibliothèque)
- tout script bun ou python : `gh`, `git` et les agents suffisent
- cache de clone, reprise incrémentale, comparaison entre deux versions d'un repo
- publication du rapport vers Linear ou Slack

## Critères de succès

Le test d'acceptation est un rejeu sur `deepseek-ai/deepseek-harness`, dont on connaît la bonne réponse :

1. la skill produit un rapport de structure et de densité comparables à `docs/fixtures/rapport-deepseek-harness.md`
2. le réfutateur retoque le verrou de version optimiste, avec la preuve que Claude Code le fait nativement, et cette trouvaille sort en argent et non en or
3. la section couverture et limites mentionne l'âge du repo et le fait que rien n'a été exécuté
4. en mode `remote`, le clone a disparu du scratchpad à la fin ; en mode `local`, `git status` du dossier cible est inchangé
