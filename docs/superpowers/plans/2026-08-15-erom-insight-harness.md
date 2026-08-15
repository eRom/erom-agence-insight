# Plan d'implémentation : plugin erom-insight, skill `harness`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Livrer une skill `harness` qui explore un repo GitHub tiers de harness ou d'agent CLI et rend un rapport de pillage or / argent / bronze, archivé et daté.

**Architecture:** Aucun code exécutable. Le plugin est fait de Markdown : un manifeste, deux définitions d'agent, une skill et trois fichiers de référence. Le déroulé est porté par le SKILL.md ; les règles permanentes de lecture sont portées par les agents, donc jamais répétées à l'appel. La session mère orchestre, les agents lisent, un agent réfutateur casse les fausses trouvailles avant le classement.

**Tech Stack:** Markdown, `gh` CLI, `git`, `trash`, agents Claude Code (`sonnet`), `claude plugin validate`.

**Spec:** `docs/superpowers/specs/2026-08-15-erom-insight-harness-design.md`

## Global Constraints

Ces contraintes valent pour toutes les tâches.

- Nom du plugin dans le manifeste : `erom-insight`. Repo : `erom-agence-insight`. Tout le publiable vit sous `plugin/`.
- Gate obligatoire en fin de chaque tâche, deux commandes, pas une :

```bash
RTK_DISABLED=1 command claude plugin validate /Users/recarnot/dev/erom-agence-insight/plugin --strict

RTK_DISABLED=1 command find plugin -name '*.md' \( -path '*/agents/*' -o -name 'SKILL.md' \) -print0 \
  | while IFS= read -r -d '' f; do
      if RTK_DISABLED=1 command head -12 "$f" | RTK_DISABLED=1 command grep -q '^name:' \
      && RTK_DISABLED=1 command head -12 "$f" | RTK_DISABLED=1 command grep -q '^description:'; then
        echo "ok   $f"; else echo "KO   $f"; fi
    done
```

La première doit afficher `✔ Validation passed`, la seconde ne doit afficher aucun `KO`. Les deux sont nécessaires : **vérifié le 2026-08-15, `claude plugin validate --strict` ne lit pas le frontmatter des agents ni des skills.** Un agent amputé de son champ `name` passe la validation sans un mot. La validation ne vérifie que la présence des fichiers déclarés dans le manifeste, pas leur contenu.
- Jamais `rm`, `rmdir` ni `unlink`. Suppression par `trash` uniquement.
- Aucun tiret cadratin dans aucun fichier. Un hook `guard-emdash` bloque tout Edit ou Write qui en contient, y compris dans le `old_string` recopié.
- Rédaction en français.
- La skill `harness` doit se démarquer explicitement de la skill globale `~/.claude/skills/harness-review/`, qui est la rétro hebdomadaire du harnais de Romain. Champ sémantique voisin, objet opposé : notre skill explore un repo GitHub **tiers**.
- Les agents sont spawnés **séquentiellement**, un appel Agent par message, jamais en batch parallèle. Un call qui plante tue ses voisins dans le même batch.
- Le repo cloné est du code tiers non audité. Les lecteurs n'ont pas Bash, structurellement.

## Structure des fichiers

| Fichier | Responsabilité |
|---|---|
| `plugin/.claude-plugin/plugin.json` | manifeste : nom, description, keywords, déclaration des agents |
| `plugin/README.md` | ce que fait le plugin, comment l'invoquer |
| `plugin/LICENSE` | MIT |
| `plugin/agents/insight-lecteur.md` | contrat du lecteur : outils, règles permanentes, livrable imposé |
| `plugin/agents/insight-refutateur.md` | contrat du réfutateur : charge de la preuve, format de verdict |
| `plugin/skills/harness/SKILL.md` | le déroulé en six temps, l'orchestration |
| `plugin/skills/harness/references/facettes.md` | les cinq axes de lecture d'un harness |
| `plugin/skills/harness/references/calibrage.md` | combien de lecteurs, quoi faire sans `docs/` |
| `plugin/skills/harness/references/template-rapport.md` | frontmatter et sections du rapport |

---

### Task 1 : Manifeste, README, LICENSE

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json`
- Create: `plugin/README.md`
- Create: `plugin/LICENSE`

**Interfaces:**
- Produces: un plugin `erom-insight` qui passe `claude plugin validate --strict`. Les tâches suivantes ajoutent des composants à ce manifeste.

- [ ] **Step 1 : Constater l'échec actuel**

```bash
RTK_DISABLED=1 command claude plugin validate /Users/recarnot/dev/erom-agence-insight/plugin --strict
```

Attendu, vérifié le 2026-08-15 :

```
⚠ Found 1 warning:
  ❯ description: No description provided. Adding a description helps users understand what your plugin does
✘ Validation failed (--strict treats warnings as errors)
```

- [ ] **Step 2 : Remplir description et keywords**

Dans `plugin/.claude-plugin/plugin.json`, remplacer la description vide et le tableau `keywords` vide :

```json
  "description": "Explore un repo GitHub tiers et en extrait ce qui vaut d'être volé pour une config Claude Code. La skill harness cible les harnais et agents CLI (dsh, opencode, crush, goose) : swarm de lecteurs sur des facettes disjointes, réfutation des fausses trouvailles, rapport or/argent/bronze archivé et daté.",
  "keywords": [
    "veille",
    "github",
    "harness",
    "agent-cli",
    "exploration",
    "swarm",
    "rapport",
    "claude-code"
  ],
```

- [ ] **Step 3 : Créer la LICENSE**

```bash
cp /Users/recarnot/dev/erom-agence-deep-research/plugin/LICENSE /Users/recarnot/dev/erom-agence-insight/plugin/LICENSE
```

Vérifier que l'année et le nom sont corrects, corriger si besoin.

- [ ] **Step 4 : Écrire le README du plugin**

`plugin/README.md`, structure calquée sur `~/dev/erom-agence-gemini/plugin/README.md`. Contenu obligatoire :

- une phrase sur ce que fait le plugin
- le tableau des deux modes d'entrée (URL GitHub, chemin local) et de leur nettoyage
- l'invocation : `/erom-insight:harness <owner/repo | url | chemin>`
- où atterrit le rapport : `~/.claude/erom-plugins/insights/<owner>-<repo>-<date>.md`
- la liste des composants (une skill, deux agents)
- une ligne disant que la skill ne couvre pas la rétro du harnais local, qui est `harness-review`

- [ ] **Step 5 : Re-valider**

```bash
RTK_DISABLED=1 command claude plugin validate /Users/recarnot/dev/erom-agence-insight/plugin --strict
```

Attendu : `✔ Validation passed`.

- [ ] **Step 6 : Commit**

```bash
git add plugin/
git commit -m "Manifeste, README et licence du plugin erom-insight"
```

---

### Task 2 : Les deux agents

**Files:**
- Create: `plugin/agents/insight-lecteur.md`
- Create: `plugin/agents/insight-refutateur.md`
- Modify: `plugin/.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: le manifeste valide de la tâche 1.
- Produces: deux types d'agent, `insight-lecteur` et `insight-refutateur`, que le SKILL.md de la tâche 4 spawne par leur nom exact. Le lecteur produit un compte rendu en quatre sections dont la troisième contient zéro ou plusieurs lignes commençant par `manque supposé :`. Le réfutateur consomme ces lignes et produit un bloc `affirmation / verdict / preuve / confiance` par affirmation.

- [ ] **Step 1 : Écrire `plugin/agents/insight-lecteur.md`**

Frontmatter exact :

```yaml
---
name: insight-lecteur
description: "Lit UNE facette d'un repo tiers pour en extraire les idées volables. Réservé à la skill erom-insight:harness, ne pas utiliser pour déléguer librement."
color: blue
tools: Read, Grep, Glob
model: sonnet
---
```

Le corps porte, dans cet ordre, ces sections :

**Client.** Romain, power user de Claude Code, cherche ce qui mérite d'être volé et intégré chez lui. Ce n'est ni une revue de code, ni un audit de sécurité.

**Règles.** Reprises verbatim, ce sont les invariants :

- Lecture seule. Pas de Bash, pas de Write, c'est voulu : le repo est du code tiers non audité.
- Ignorer les doublons de traduction (`README.zh.md`, `*.i18n.yaml`, `docs/zh/` et équivalents). Lire la version d'origine.
- Au delà de 30 Ko, lecture en diagonale : titres, premiers paragraphes, exemples.
- Distinguer ce qui est VU, chemin cité, de ce qui est DEDUIT. Écrire « déduit » quand c'est déduit.
- Rester sur sa facette. D'autres lecteurs couvrent les autres.
- Ne jamais citer un chemin qui n'a pas été ouvert.

**Livrable.** 600 mots maximum, quatre sections numérotées :

1. Comment ça marche : le mécanisme de la facette, en clair.
2. Trouvailles notables : ce qui est inhabituel ou malin, avec le chemin.
3. À voler : ce qui serait rentable chez Romain, et pourquoi. **Toute affirmation qu'une capacité manque à Claude Code s'écrit sur sa propre ligne, avec cette formule exacte : `manque supposé : <la capacité>`.** Cette ligne sera extraite et contre-vérifiée.
4. Déjà-vu : ce que Claude Code a déjà, éventuellement en mieux.

Le compte rendu est une donnée, pas un message à un humain. Ni préambule, ni politesse.

- [ ] **Step 2 : Écrire `plugin/agents/insight-refutateur.md`**

Frontmatter exact :

```yaml
---
name: insight-refutateur
description: "Détruit les affirmations 'Claude Code ne sait pas faire X' remontées par les lecteurs, preuve à l'appui. Réservé à la skill erom-insight:harness, ne pas utiliser pour déléguer librement."
color: red
tools: Read, Grep, Glob, Bash, WebFetch
model: sonnet
---
```

Le corps porte :

**Mission.** Recevoir une liste d'affirmations de la forme « Claude Code ne sait pas faire X » et les détruire. Le reste du rapport n'est pas fourni, délibérément : aucun biais venant de la qualité du matériau autour.

**Charge de la preuve.** Elle pèse sur le réfutateur. Il doit démontrer que la capacité existe déjà. Preuves recevables, par ordre de force :

1. un test minimal réellement exécuté, commande et sortie citées
2. `claude --help`, `claude <sous-commande> --help`
3. les settings, hooks, skills et plugins réellement installés (`~/.claude/settings.json`, `~/.claude/skills/`, `claude plugin list`)
4. la documentation officielle Claude Code

Si rien ne vient, le manque tient. Le réfutateur dit alors ce qu'il a cherché, pour que Romain puisse juger.

**Interdits.** Ne jamais conclure « déjà natif » sur une intuition ou un souvenir. Ne rien tester de destructif : aucune écriture hors du scratchpad, aucune modification de settings.

**Livrable.** Pour chaque affirmation, dans l'ordre reçu, ce bloc et rien d'autre :

```
affirmation: <recopiée verbatim>
verdict: deja_natif | manque_tient
preuve: <la commande lancée et sa sortie, ou le chemin et la ligne, ou l'URL>
confiance: haute | moyenne | basse
```

Ni synthèse, ni recommandation.

- [ ] **Step 3 : Déclarer les agents dans le manifeste**

Ajouter la clé `agents` à `plugin/.claude-plugin/plugin.json`, après `"skills": "./skills/"`, en respectant la forme vérifiée sur `erom-gemini` :

```json
  "skills": "./skills/",
  "agents": ["./agents/insight-lecteur.md", "./agents/insight-refutateur.md"]
```

- [ ] **Step 4 : Valider**

```bash
RTK_DISABLED=1 command claude plugin validate /Users/recarnot/dev/erom-agence-insight/plugin --strict
```

Attendu : `✔ Validation passed`, puis aucun `KO` au second contrôle. Un chemin d'agent absent du disque est signalé par la validation (`agents[0]: Path not found`), mais un frontmatter invalide ne l'est pas : c'est le second contrôle qui l'attrape.

- [ ] **Step 5 : Commit**

```bash
git add plugin/agents plugin/.claude-plugin/plugin.json
git commit -m "Agents insight-lecteur et insight-refutateur"
```

---

### Task 3 : Les trois fichiers de référence

**Files:**
- Create: `plugin/skills/harness/references/facettes.md`
- Create: `plugin/skills/harness/references/calibrage.md`
- Create: `plugin/skills/harness/references/template-rapport.md`

**Interfaces:**
- Produces: trois fichiers chargés à la demande par le SKILL.md de la tâche 4. `facettes.md` définit les cinq identifiants de facette (`boucle`, `outils`, `memoire`, `extensibilite`, `exploitation`) que le frontmatter du rapport reprend tels quels.

- [ ] **Step 1 : Écrire `facettes.md`**

Cinq sections, une par facette. Chacune porte : l'identifiant, la question centrale, les endroits typiques où chercher, et les signaux qui valent de l'or.

| id | Question centrale | Où chercher typiquement |
|---|---|---|
| `boucle` | comment un tour est construit, et que voit réellement le modèle | docs sur le contexte, la compaction, le spill, les logs de session |
| `outils` | quel catalogue d'outils, quel modèle d'approbation, quelle isolation | docs sandbox et permissions, définitions d'outils, garde-fous |
| `memoire` | qu'est-ce qui survit entre deux sessions, et comment on reprend après un crash | notes de décision, état persisté, resume, handoff |
| `extensibilite` | comment un tiers ajoute une capacité | plugins, skills, hooks, marketplace, points d'extension |
| `exploitation` | ce que le projet s'impose à lui-même | postmortems, gouvernance de la doc, dogfooding, CI |

Ajouter en fin de fichier la règle de disjonction : deux facettes ne partagent jamais un chemin de départ. Si un document couvre deux facettes, il est assigné à une seule, et l'autre lecteur reçoit une note disant qu'il ne doit pas le traiter.

- [ ] **Step 2 : Écrire `calibrage.md`**

La table de décision, reprise de la spec :

| Observation à la reconnaissance | Décision |
|---|---|
| moins de 5 packages ou moins de 10 fichiers de doc | 2 à 3 lecteurs, facettes fusionnées |
| taille moyenne, `docs/` fourni | 5 lecteurs, les 5 facettes |
| monorepo large | jusqu'à 7 lecteurs, jamais plus |
| pas de `docs/` | lecteurs orientés code source, tests et README de packages |
| repo minuscule | pas de swarm, lecture directe par la session mère |

Ajouter la justification en une ligne du plafond à 7 : au delà, la synthèse devient une soupe et les facettes se recouvrent.

Ajouter la consigne de sortie : la reconnaissance produit, pour chaque facette retenue, trois à huit chemins de départ nommés et disjoints. Une facette sans chemin de départ nommé est une facette qu'on ne lance pas.

- [ ] **Step 3 : Écrire `template-rapport.md`**

Le frontmatter exact, avec les valeurs d'exemple réelles capturées le 2026-08-15 via `gh api repos/deepseek-ai/deepseek-harness` :

```yaml
---
repo: deepseek-ai/deepseek-harness
url: https://github.com/deepseek-ai/deepseek-harness
mode: remote
date: 2026-08-15
repo_cree: 2026-08-13
repo_pousse: 2026-08-13
etoiles: 102269
licence: MIT
langage: TypeScript
facettes: [boucle, outils, memoire, extensibilite, exploitation]
lecteurs: 5
session: <nom de session>
session_id: <id harness>
bridge_url: <url claude.ai>
---
```

Puis les sections du corps, dans cet ordre imposé :

1. Verdict en trois lignes
2. Ce que c'est
3. Or : faible coût, gain réel, manque confirmé par le réfutateur
4. Argent : à parquer, dont les trouvailles retoquées avec leur preuve
5. Bronze : leçons de design, rien à construire
6. Déjà-vu : ce qu'on a déjà, parfois en mieux
7. Couverture et limites : ce qui n'a pas été lu, le fait que rien n'a été exécuté ni testé, l'âge du repo et l'instabilité qui va avec

Préciser que les trois derniers champs de session viennent de `~/.claude/skills/session-whoami/scripts/*.sh --json`, et que s'il est absent, ils sont simplement omis.

Le rapport de référence à imiter en densité et en ton : `docs/fixtures/rapport-deepseek-harness.md`.

- [ ] **Step 4 : Valider et commit**

```bash
RTK_DISABLED=1 command claude plugin validate /Users/recarnot/dev/erom-agence-insight/plugin --strict
git add plugin/skills
git commit -m "References de la skill harness : facettes, calibrage, template de rapport"
```

---

### Task 4 : Le SKILL.md

**Files:**
- Create: `plugin/skills/harness/SKILL.md`

**Interfaces:**
- Consumes: les agents `insight-lecteur` et `insight-refutateur` de la tâche 2, les trois références de la tâche 3.
- Produces: la skill invocable `/erom-insight:harness`.

- [ ] **Step 1 : Écrire le frontmatter**

```yaml
---
name: harness
description: "Explore un repo GitHub TIERS qui est un harnais ou un agent CLI (dsh, opencode, crush, goose) et rend un rapport de pillage or/argent/bronze : ce qui vaut d'être volé pour la config Claude Code, ce qu'on a déjà, ce qui est du bruit. Accepte une URL ou un slug GitHub (clone puis trash) ou un chemin local (aucune écriture). Triggers : /erom-insight:harness <owner/repo|url|chemin>, 'pille ce repo', 'analyse ce harness', 'qu'est-ce qu'ils ont dans X'. Ne couvre PAS la retro du harnais local, qui est la skill harness-review."
argument-hint: "<owner/repo | url GitHub | chemin local>"
---
```

La dernière phrase de la description est obligatoire : elle empêche le déclenchement croisé avec `~/.claude/skills/harness-review/`, qui est la rétro hebdomadaire du harnais de Romain.

- [ ] **Step 2 : Étape 0 du corps, racine du plugin**

Reprendre le motif vérifié dans `~/dev/erom-agence-gemini/plugin/skills/transcribe/SKILL.md` : `ROOT` vaut `${CLAUDE_PLUGIN_ROOT}` s'il arrive expansé, sinon deux niveaux au dessus du « Base directory for this skill » injecté. Les références se chargent depuis `$ROOT/skills/harness/references/`.

- [ ] **Step 3 : Résolution du mode**

Un seul appel Bash. Le premier token de `$ARGUMENTS` décide :

| Forme | Mode | Suite |
|---|---|---|
| `https://github.com/<owner>/<repo>` ou `<owner>/<repo>` | `remote` | vérification GitHub puis clone |
| chemin qui passe `test -d` | `local` | pas de clone |
| rien ne résout | arrêt | demander une fois quel repo, puis stop |

En mode `local`, tenter `git -C <path> remote get-url origin`. Si le remote est un GitHub, en dériver `owner/repo` et enrichir depuis l'API. Sinon owner vaut `local` et repo vaut le nom du dossier.

- [ ] **Step 4 : Temps 1, vérification**

Commande exacte, vérifiée le 2026-08-15 :

```bash
RTK_DISABLED=1 command gh api repos/<owner>/<repo> --jq '{full_name,stars:.stargazers_count,created:.created_at,pushed:.pushed_at,size_ko:.size,licence:.license.spdx_id,archived,lang:.language}'
```

Sortie réelle observée sur le repo de référence :

```json
{"archived":false,"created":"2026-08-13T11:56:32Z","full_name":"deepseek-ai/deepseek-harness","lang":"TypeScript","licence":"MIT","pushed":"2026-08-13T13:00:21Z","size_ko":117204,"stars":102269}
```

Règles à écrire dans la skill :

- sur 404, lancer `gh api user`. S'il répond, le token est valide, donc le repo est inexistant ou privé sans accès. Le dire et s'arrêter. Ne jamais enchaîner sur un clone.
- `size_ko` au dessus de 500000, soit 500 Mo, annoncer le volume et demander avant de cloner. Repère : le repo de référence pèse 117 Mo.
- si `archived` est vrai, le signaler dans le brief et dans les limites du rapport.

- [ ] **Step 5 : Temps 2, reconnaissance**

Mode `remote` :

```bash
git clone --depth 1 https://github.com/<owner>/<repo>.git "$SCRATCHPAD/insight-<owner>-<repo>"
```

Puis, dans les deux modes, la session mère lit elle-même : arbre au niveau 2, README racine, `AGENTS.md` ou `CLAUDE.md` s'ils existent, index des docs, liste des packages.

Sortie de cette étape : pour chaque facette retenue, trois à huit chemins de départ nommés et disjoints. Charger `references/calibrage.md` pour décider du nombre de lecteurs et de l'orientation.

- [ ] **Step 6 : Temps 3, l'arrêt**

Dix lignes maximum, puis attendre :

- ce qu'est le repo, factuel : nom, âge, étoiles, licence, langage
- l'intention déduite, en une phrase
- le plan : N lecteurs, une ligne par facette

Ne rien spawner avant la réponse de Romain. C'est le seul arrêt du déroulé, placé juste avant la dépense.

- [ ] **Step 7 : Temps 4, le swarm**

Un appel `Agent` par message, `subagent_type: insight-lecteur`, jamais deux dans le même bloc. Écrire le motif dans la skill pour que personne ne l'optimise plus tard : un call qui plante tue ses voisins du même batch, et chaque spawn retourne immédiatement, donc le séquencement ne coûte pas de temps réel.

Chaque prompt d'appel contient uniquement : la racine absolue du repo, l'identifiant de la facette, les chemins de départ, et la liste des chemins réservés aux autres lecteurs. Les règles permanentes sont dans l'agent, ne pas les répéter.

- [ ] **Step 8 : Temps 5, la réfutation**

Extraire de tous les comptes rendus les lignes commençant par `manque supposé :`. Si la liste est vide, sauter ce temps et le dire dans le rapport.

Sinon, un seul appel `Agent`, `subagent_type: insight-refutateur`, dont le prompt contient la liste de ces affirmations et rien d'autre. Ne jamais lui passer les comptes rendus complets.

Classement : `manque_tient` autorise l'or. `deja_natif` bascule la trouvaille en argent, avec la preuve citée dans le rapport.

- [ ] **Step 9 : Temps 6, rapport et livraison**

Charger `references/template-rapport.md`. Synthétiser, jamais concaténer. Écrire dans `~/.claude/erom-plugins/insights/<owner>-<repo>-<YYYY-MM-DD>.md`, en `local-<dossier>-<date>.md` si mode local sans remote, suffixe `-2` en cas de collision le même jour.

Récupérer les champs de session via `~/.claude/skills/session-whoami/scripts/*.sh --json` si le script existe, sinon omettre ces champs.

Puis `SendUserFile` en `display: "render"`, et gravure des conclusions durables en mémoire, sous le régime de décision en vigueur : ligne `Battu :` nommant les alternatives écartées, frontmatter `status` daté.

- [ ] **Step 10 : Temps 7, nettoyage**

Mode `remote` uniquement :

```bash
trash "$SCRATCHPAD/insight-<owner>-<repo>"
```

Jamais `rm`. En mode `local`, ne rien supprimer et ne rien écrire dans le dossier cible.

- [ ] **Step 11 : Valider et commit**

```bash
RTK_DISABLED=1 command claude plugin validate /Users/recarnot/dev/erom-agence-insight/plugin --strict
git add plugin/skills/harness/SKILL.md
git commit -m "SKILL.md de harness : deroule en sept temps, deux modes d'entree"
```

---

### Task 5 : Test d'acceptation sur deepseek-harness

**Files:**
- Create: `docs/acceptation-2026-08-15-dsh.md`

**Interfaces:**
- Consumes: le plugin complet des tâches 1 à 4.

Ce rejeu est le test d'acceptation défini par la spec. Le repo de référence a déjà été exploré une fois, donc la bonne réponse est connue : c'est ce qui rend le test discriminant.

- [ ] **Step 1 : Jouer le déroulé**

Le plugin n'étant pas encore installé, lire `plugin/skills/harness/SKILL.md` et l'appliquer littéralement, sans improviser, sur `deepseek-ai/deepseek-harness`. Toute étape ambiguë à l'exécution est un défaut du SKILL.md, pas une liberté d'interprétation : la noter.

- [ ] **Step 2 : Vérifier les quatre critères de la spec**

1. le rapport a la structure et la densité de `docs/fixtures/rapport-deepseek-harness.md`
2. le réfutateur retoque le verrou de version optimiste, preuve à l'appui que Claude Code le fait nativement, et cette trouvaille sort en **argent**, pas en or
3. la section couverture et limites mentionne l'âge du repo et le fait que rien n'a été exécuté
4. le clone a disparu du scratchpad à la fin

- [ ] **Step 3 : Consigner le résultat**

Écrire `docs/acceptation-2026-08-15-dsh.md` : les quatre critères, le verdict de chacun, et la liste des ambiguïtés relevées à l'étape 1.

- [ ] **Step 4 : Corriger les défauts relevés**

Reprendre le SKILL.md ou les agents sur chaque ambiguïté notée. Re-valider. Ne pas passer à la publication tant que le critère 2 échoue : c'est le critère qui justifie l'existence du temps de réfutation.

- [ ] **Step 5 : Commit**

```bash
git add docs/acceptation-2026-08-15-dsh.md plugin/
git commit -m "Test d'acceptation sur deepseek-harness et corrections"
```

---

## Après le plan

La publication sur `erom-marketplace` se fait par la skill `plugin-release`, hors périmètre de ce plan. Ne la déclencher qu'une fois le critère 2 du test d'acceptation vert.

Une suite d'eval `claude plugin eval` (cases sous `evals/**/case.yaml` plus des graders) est possible et serait le vrai filet à long terme. Le format exact n'a pas été vérifié dans cette session, donc rien n'est figé ici : c'est un chantier à part entière, à ouvrir seulement si la skill se met à dériver.
