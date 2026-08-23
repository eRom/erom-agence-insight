# Architecture

Mise à jour : 2026-08-23

## Objectif

Plugin Claude Code `erom-insight` (repo `erom-agence-insight`). Il explore un repo GitHub tiers et en extrait ce qui vaut d'être repris dans une config Claude Code.

Trois skills, trois questions distinctes :

| Skill | Cible | Question |
|---|---|---|
| `harness` | harnais et agents CLI concurrents | qu'est-ce qu'ils ont que je n'ai pas ? |
| `tool-claude` | outils qui se branchent sur Claude Code | est-ce que je l'installe ? |
| `skill-claude` | skills et plugins Claude Code tiers | est-ce que je peux l'installer sans risque, et ça vaut quoi ? |

## Stack

Markdown, plus un seul script exécutable depuis le 2026-08-23 : `skills/skill-claude/scripts/secu-scan.py` (Python 3 stdlib, lecture seule, sa suite de cas à côté). Les dépendances externes sont `gh` (authentifié), `git`, `trash`, `python3`, et les agents Claude Code.

## Découpage

**Par nature de la cible, pas par étape de pipeline.** `harness` couvre les harnais et agents CLI (dsh, opencode, crush, goose), `tool-claude` les outils qui se branchent sur Claude Code (indexeur, MCP, optimiseur de contexte).

```
plugin/                      tout le publiable, envoyé sur la marketplace
  .claude-plugin/plugin.json
  agents/                    2 agents, partagés par les deux skills
  skills/harness/            1 skill + 3 références
  skills/tool-claude/        1 skill + 4 références
  skills/skill-claude/       1 skill + 2 références + 1 script et sa suite de cas
docs/                        hors plugin publié
  fixtures/                  rapport de référence de harness, skill piégée inerte pour skill-claude
  evals/skill-claude/        les 3 cas d'éval de skill-claude (méthode skill-creator)
  superpowers/{specs,plans}/
_memory_/
```

**Le socle commun n'a toujours pas été extrait**, et la troisième famille est arrivée le 2026-08-23. Les trois skills dupliquent l'étape 0 (résolution du mode remote / local, vérification `gh api`, clone) et le bloc anti-injection, à quelques phrases près ; `skill-claude` ajoute à l'étape 0 le sous-chemin `tree/<branche>/<chemin>` et la reconnaissance skill / plugin / catalogue. Duplication maintenue sciemment : chaque étape 0 diverge un peu (seuils, sous-chemin, nature de la cible), un socle partagé n'a pas d'emplacement naturel dans un plugin, et la dérive entre trois copies d'un bloc de 20 lignes coûte moins qu'une indirection de plus au chargement. `[candidat 1x - chantier skill-claude 2026-08-23]`

`tool-claude` réutilise `insight-lecteur` pour la lecture d'une zone sur un gros repo, mais n'a pas de swarm ni de réfutateur : sa charge de preuve est le `fichier:ligne`, pas le vote d'un agent isolé.

## Flux de `harness`

Sept temps, un seul arrêt utilisateur, placé juste avant la dépense :

1. **vérification** `gh api repos/<owner>/<repo>`, s'arrête net si le repo n'existe pas
2. **reconnaissance** clone shallow dans le scratchpad, la session mère lit elle-même et assigne des chemins de départ disjoints par facette
3. **arrêt** brief de 10 lignes, Romain valide ou corrige l'intention
4. **swarm** N agents `insight-lecteur`, spawnés séquentiellement
5. **réfutation** 1 agent `insight-refutateur` reçoit les seules affirmations de manque et doit les détruire
6. **rapport** synthèse, écriture dans `~/.claude/erom-store/insights/`, `SendUserFile`
7. **nettoyage** `trash` du clone et du scratchpad

## Flux de `tool-claude`

Sept temps aussi, un seul arrêt, mais placé ailleurs : **juste avant d'écrire dans la configuration locale**, pas avant la dépense. Le coût d'analyse est jugé acceptable, l'écriture chez Romain ne l'est pas sans accord.

1. **brochure gelée** les affirmations vérifiables sont extraites du README **avant** toute lecture de code, sinon on note sur une courbe
2. **confrontation** chaque affirmation reçoit `confirmé` / `gonflé` / `invérifiable`, `fichier:ligne` obligatoire
3. **coût d'installation** inventaire chiffré, dont ce qui s'écrit hors du repo et ce qui est imposé au modèle à chaque tour
4. **butin trié** ce qu'on vole (avec un fichier cible nommé) et ce qu'on refuse
5. **mesure** chaque geste volé est mesuré sur le corpus local avant qu'une ligne de patch soit écrite
6. **rapport puis arrêt** verdict d'installation parmi `installer`, `ne-pas-installer`, `installer-partiellement`, `surveiller`
7. **application** sauvegarde, patch, suite de test installée à côté du fichier, résultat rapporté brut

## Flux de `skill-claude`

Cinq temps, zéro arrêt hors sécurité : la skill n'écrit jamais dans la configuration, donc rien n'attend Romain, sauf l'arrêt de sécurité qui, lui, arrête tout.

1. **étape 0** mode remote / local, sous-chemin `tree/<branche>/<chemin>`, reconnaissance skill / plugin / catalogue (un catalogue arrête : une cible est une skill ou un plugin)
2. **sécurité** scanner `secu-scan.py` puis lecture de chaque rouge à sa ligne, de chaque script, hook, serveur MCP et fichier de consignes en entier ; `ok` ou `stop` ; sur `stop` : message en chat dans une forme imposée, rapport minimal `stop-secu`, `trash`, fin
3. **pourquoi et comment** finalité, tableau (où ça tourne, authentification, prérequis, ce qui sort, pour quel harnais), mécanisme réel
4. **véracité** promesses de la description contre le corps, ce qu'elle nomme existe-t-il, un fait d'API vérifié contre la doc officielle, les scripts contre la prose
5. **verdict** déjà-vu local d'abord (skills chargées, disque, MCP), puis `installer` / `trash` / `refaire` avec la condition qui le changerait ; rapport dans le store, `SendUserFile`, `trash` du clone

**Décision structurante, temps 2 (scanner avant lecture).** Le scanner existe parce que l'oeil et le modèle sautent la même chose : caractères invisibles, HTML caché, blobs encodés, contenu des scripts. Il est le plancher, pas le plafond : `references/secu.md` liste ce qu'il ne voit pas (sémantique, bombes logiques, assemblage de chaînes, consignes réparties) et impose la lecture intégrale des scripts et des consignes.

## Deux modes d'entrée

| Entrée | Mode | Clone | Nettoyage |
|---|---|---|---|
| URL ou slug GitHub | `remote` | oui, scratchpad | `trash` |
| chemin d'un dossier | `local` | non | rien, dossier jamais touché |

## Décisions structurantes

**`harness`, temps 5 (réfutation).** Il existe à cause d'une erreur réelle : une trouvaille avait été classée or sur un manque de Claude Code jamais vérifié, et le chantier lancé puis annulé. La charge de la preuve remonte donc avant le classement.

**`tool-claude`, temps 5 (mesure).** Même famille de garde-fou, autre mécanisme : aucun patch sans mesure, aucune mesure sans un fichier cible nommé. Il vient aussi d'un cas réel, le 2026-08-16 sur `nanonets/graft` : le geste repris était un plafond d'injections, et la mesure a montré que 89 % du problème venait d'ailleurs (un motif de détection trop large). Appliquer le geste volé sans mesurer aurait laissé le vrai défaut intact.
