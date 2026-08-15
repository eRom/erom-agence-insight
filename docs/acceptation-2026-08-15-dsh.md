# Test d'acceptation : rejeu sur deepseek-ai/deepseek-harness

Date : 2026-08-15. Cible : `deepseek-ai/deepseek-harness`, mode `remote`, 102 462 étoiles, 117 Mo annoncés par l'API, 80 Mo sur disque après clone shallow.

Ce rejeu applique `plugin/skills/harness/SKILL.md` littéralement. La bonne réponse est connue d'avance : le repo a déjà été exploré une fois, et cette exploration a produit une erreur documentée.

## Limite du rejeu

Le plugin n'était pas installé au moment du test. Les agents `insight-lecteur` et `insight-refutateur` n'existaient donc pas comme types disponibles : leur contrat a été injecté dans le prompt d'agents `general-purpose`.

Conséquence directe : **la restriction d'outils n'a pas été testée.** Les lecteurs disposaient de tous les outils au lieu de `Read, Grep, Glob`. La lecture seule reposait sur la consigne, ce qui est précisément ce que la définition d'agent est censée remplacer. À rejouer après installation du plugin.

## Défauts du SKILL.md révélés par le rejeu

### 1. La mère n'a pas de consigne sur les traductions

La règle d'ignorer les doublons de traduction vit dans l'agent lecteur. Mais c'est la session mère qui liste les fichiers à la reconnaissance, et le repo cible porte trois variantes par document (`x.md`, `x.zh.md`, `x.i18n.yaml`). Sans consigne, la mère assigne des chemins en triple.

Filtre improvisé pendant le test, à inscrire dans le temps 2 :

```bash
ls docs/subsystems/*.md | grep -v '\.zh\.md'
```

### 2. Le calibrage se contredit sur ce repo

La table de `calibrage.md` donne deux lignes qui s'appliquent toutes les deux ici, sans règle de départage :

- « taille moyenne, dossier `docs/` fourni » vaut 5 lecteurs
- « monorepo large » vaut jusqu'à 7 lecteurs

Le repo a 54 packages et une documentation riche. J'ai tranché à 5 par comparabilité avec le rapport de référence, mais la table doit dire elle-même comment départager. Proposition : c'est le volume de **documentation** qui décide du nombre de lecteurs, pas le nombre de packages, puisque ce sont les documents qui sont lus.

### 3. Les lecteurs ne doivent pas être nommés

Défaut le plus coûteux du rejeu. J'ai donné un nom à chaque lecteur au spawn. Un agent nommé devient un teammate adressable, et **son texte final ne remonte pas automatiquement à la session mère** : il se signale disponible, et son compte rendu reste chez lui tant qu'on ne le lui redemande pas.

Trois lecteurs sur cinq ont dû être relancés par message. Deux n'ont jamais rendu.

Le temps 4 doit dire explicitement : les lecteurs sont des subagents one-shot, on ne leur donne pas de nom, leur texte final est la valeur de retour.

### 4. Rien n'est prévu quand un lecteur ne rend rien

Le SKILL.md ne dit pas quoi faire d'une facette muette : relancer, abandonner, ou la déclarer non couverte. Le rejeu a rencontré le cas, il faut une règle. Proposition : une relance, puis la facette passe en non couverte et la section « couverture et limites » du rapport la nomme.

Dans ce rejeu, les cinq facettes ont fini par rendre, mais deux d'entre elles seulement après relance explicite. Entretemps j'avais respawné ces deux facettes en subagents anonymes, qui ont donc travaillé pour rien. Le coût de ce défaut est double : la relance, puis le doublon.

### 5. La formule `manque supposé :` n'est pas bornée

Elle est définie dans l'agent lecteur comme une capacité qui manque à **Claude Code**. Un lecteur l'a employée pour un manque dans la **doctrine de Romain** (l'absence de recherche de doublon avant une écriture mémoire), qui n'est pas du tout le même objet et ne se réfute pas avec les mêmes preuves.

L'agent doit borner la formule explicitement : elle porte sur une capacité du produit Claude Code, pas sur une pratique, une convention ou un fichier de configuration personnel.

### 6. Personne ne nettoie derrière le réfutateur

Le temps 7 ne prévoit que la suppression du clone. Or le réfutateur, qui a Bash, a produit ses propres fichiers de travail dans le scratchpad : 45,4 Mo de `claude_strings.txt` plus un `big_grep_target.txt`, laissés en place après son verdict.

Le scratchpad est éphémère, donc ce n'est pas grave, mais 45 Mo par exécution méritent une ligne. Le temps 7 doit balayer le scratchpad de la session, pas seulement le répertoire du clone.

## Critères de la spec

| # | Critère | Verdict |
|---|---|---|
| 1 | rapport de structure et densité comparables à la fixture | **atteint** |
| 2 | le verrou de version sort en argent, pas en or, preuve à l'appui | **atteint par un autre chemin**, voir ci-dessous |
| 3 | couverture et limites mentionne l'âge du repo et l'absence d'exécution | **atteint** |
| 4 | le clone a disparu du scratchpad à la fin | **atteint**, scratchpad vide |

### Détail du critère 2

Le résultat visé est obtenu : le verrou de version optimiste ne figure pas en or. Mais pas par le chemin prévu.

Aucun lecteur ne l'a affirmé comme un manque cette fois. Le lecteur de la facette `outils` l'a rangé spontanément en déjà-vu, en le reconnaissant comme le comportement natif de l'outil Edit. Le réfutateur n'a donc jamais eu à le juger.

Le mécanisme de réfutation a bien été exercé, sur huit autres affirmations, et il en a retoqué deux avec preuve exécutée :

- le délestage sur disque des sorties surdimensionnées, réfuté par deux commandes produisant 1,9 Mo puis 336 Ko, qui ont renvoyé `Output too large. Full output saved to: .../tool-results/<id>.txt`
- les packages sandboxés définis à l'exécution, réfutés par la description des capacités d'Artifact, versionnement semver et consentement explicite du lecteur compris

Le filtre fonctionne donc, et il est même plus productif que prévu : 36 appels d'outil, 21 minutes, 8 verdicts sourcés, 2 trouvailles écartées avant d'atteindre Romain.

Conclusion sur ce critère : le libellé de la spec était trop étroit. Il testait un cas particulier plutôt que la capacité. À reformuler en « au moins une affirmation de manque est retoquée avec une preuve exécutée, et sort en argent avec cette preuve citée ».
