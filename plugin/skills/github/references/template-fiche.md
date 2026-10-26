# Gabarit de fiche

Une fiche par repo, toujours la même forme, pour qu'elles se comparent. Les champs entre chevrons se remplacent ; une ligne dont la donnée manque se garde avec `non trouvé` (ou `aucune`, `non`), jamais supprimée, jamais devinée.

## Listes fermées

Une valeur exactement, prise dans la liste. Rien d'autre n'est accepté.

Format des nombres : les entiers se recopient tels quels depuis `facts.json` ; seules les décimales passent à la virgule française (`88.4` devient `88,4 %`).

| Champ | Valeurs |
|---|---|
| `type` | `app-web`, `app-desktop`, `app-mobile`, `cli-tui`, `framework`, `librairie-sdk`, `plugin-extension` (Raycast, VS Code, navigateur, Obsidian), `serveur-mcp`, `extension-claude-code` (skill, plugin, agents ou hooks pour Claude Code), `template`, `liste-awesome`, `infra-iac`, `dataset`, `doc-tutoriel`, `code-de-reference` (code publié pour être lu, audité ou étudié, pas pour être installé), `autre` |
| `activity` | recopiée de `facts.json` : `actif`, `ralenti`, `abandonne`, `archive` |
| `self_hostable` | `oui` (tout tourne chez soi), `partiel` (une partie exige un service tiers), `non` (SaaS seulement), `sans-objet` (rien ne tourne comme service : librairie, liste, doc, code de référence). Un logiciel local commercial exigé (Hopper, IDA) laisse `oui` et va dans les prérequis |
| `verdict` | `a-tester`, `a-suivre`, `pas-pertinent` |
| `status` | `nouveau`, `a-tester`, `teste`, `adopte`, `ecarte` |

Règle du `type` : le livrable principal que l'on installe ou consomme, pas le langage. Un repo qui mêle plusieurs livrables prend le plus central, et les autres vont dans `secondary_types`. `autre` exige une phrase de justification dans la section 3.

Pas d'avatar, ni dans le corps ni dans le frontmatter, et aucun HTML brut : le lecteur du backlog échappe le HTML et sa CSP bloque les images externes, la balise s'afficherait en texte.

Règle du `status` : une fiche neuve naît `nouveau`. Ensuite, seul Romain le change.

## Le fichier

~~~markdown
---
repo: <owner/name>
owner: <owner>
owner_type: <User|Organization>
url: <html_url>
date: <YYYY-MM-DD, date de l'analyse>
description: "<une phrase en français, ce que fait le projet : elle sert de sujet dans INDEX.md>"
type: <liste fermée>
secondary_types: [<liste fermée>, ...]
language: <langage principal>
license: <recopiée de facts.json : SPDX, `aucune` ou `non-reconnue`>
stars: <entier>
activity: <liste fermée>
self_hostable: <liste fermée>
verdict: <liste fermée>
status: <liste fermée>
tags: [<tags perso>]
skill: erom-insight:github
---

# <owner/name>

**<owner>** (<Utilisateur|Organisation>) · [repo](<url>) · <homepage ou « pas de site »>

> <verdict en une ligne, la même que la section 6>

## 1. Identité

| Champ | Valeur |
|---|---|
| Description GitHub | <description brute, ou « aucune »> |
| Site | <homepage ou « aucun »> |
| Topics | <topics séparés par des virgules, ou « aucun »> |
| Licence | <SPDX ou « aucune »> |
| Créé le | <YYYY-MM-DD> |
| Dernier push | <YYYY-MM-DD> |
| Dernière release | <tag, publiée le YYYY-MM-DD> ou « aucune release » (+ dernier tag git s'il existe) |

## 2. Présentation

<2 à 3 phrases : ce que fait le projet.>

**Problème résolu** : <une phrase>. **Public** : <une phrase>.

**Fonctionnalités clés**

- <jusqu'à 6 puces, au moins une ; README d'abord, manifestes ensuite avec leur source ; aucune inventée pour atteindre un compte>

**Alternatives citées par le README** : <liste, ou « aucune citée »>

## 3. Type et technos

| Champ | Valeur |
|---|---|
| Type | `<type>` (+ `<secondary_types>`) |
| Langages | <Langage 75,1 %, Langage 18,0 %, ... les 4 premiers> |
| Frameworks et libs majeurs | <noms> (source : `<manifeste>`) |
| Plateformes cibles | <macOS, Linux, Windows, navigateur, Node, Docker, iOS...> (source : README ou `<manifeste>`) |
| Services externes requis | <clés API, base, LLM...> avec leur source (README, ou SDK client explicite dans un manifeste), ou « aucun trouvé » |

## 4. Usage et déploiement

| Champ | Valeur |
|---|---|
| Installation | <brew, npm, pip, cargo, Docker, binaire, depuis les sources> |
| Auto-hébergeable | `<self_hostable>` : <une phrase> |
| Prérequis | <liste courte> |
| Docker / compose | <oui ou non, avec le chemin> |
| Doc | <oui si le marqueur `docs` est vrai OU si le README renvoie vers une doc ; dire laquelle des deux, avec le chemin ou le lien> |
| Démo | <lien, ou « aucune »> |

**Exemple minimal**

```bash
<une commande recopiée du README, ou « le README n'en donne pas »>
```

## 5. Maturité et santé

| Métrique | Valeur |
|---|---|
| Étoiles · forks · abonnés | <stars> · <forks> · <watchers> |
| Issues ouvertes · PR ouvertes | <open_issues> · <open_pull_requests> |
| Contributeurs | <contributors> |
| Dernier commit | <YYYY-MM-DD>, il y a <N> j |
| Commits sur 90 j · sur 365 j | <commits_90d> · <commits_365d> |
| Activité | `<activity>` (<activity_rule>) |
| Archivé · fork | <oui/non> · <non, ou « fork de <parent> »> |
| Releases · CI · docs · tests | <oui (N)/non> · <oui/non> · <oui/non> · <oui/non> (marqueurs de l'arbre) |

<Si un fait détonne (étoiles ou forks hors de proportion avec l'âge du repo, chiffre du README qui contredit l'API, PR ouvertes en masse), une ligne **À noter** ici : le fait, sans le corriger ni conclure. Sinon rien.>

## 6. Évaluation pour Romain

**Verdict** : `<verdict>`, <une ligne qui dit pourquoi>.

**Pertinence** : <quels chantiers de Romain il touche, nommés, ou « aucun chantier en cours »>

- **Fort** : <puce>
- **Fort** : <puce>
- **Limite** : <puce>

## Notes de Romain

<vide à la création ; recopié tel quel lors d'une mise à jour>

---
*Faits tirés de l'API GitHub le <fetched_at>. Arbre : <files> fichiers (ajouter « liste tronquée par l'API » si `tree.truncated` vaut true). Manifestes lus : <liste ou « aucun »>.*
~~~
