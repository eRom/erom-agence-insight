# Calibrage du swarm

Le nombre de lecteurs et l'orientation des facettes se décident à la reconnaissance, jamais d'avance.

## Table de décision

| Observation à la reconnaissance | Décision |
|---|---|
| moins de 5 packages ou moins de 10 fichiers de documentation | 2 à 3 lecteurs, facettes fusionnées |
| taille moyenne, dossier `docs/` fourni | 5 lecteurs, les 5 facettes |
| monorepo large | jusqu'à 7 lecteurs, jamais plus |
| pas de dossier `docs/` | lecteurs orientés code source, tests et README de packages |
| repo minuscule, quelques fichiers | pas de swarm, lecture directe par la session mère |

Le plafond de 7 n'est pas arbitraire : au delà, les facettes se recouvrent mécaniquement et la synthèse devient une soupe où plus rien ne ressort.

## Fusion des facettes

Quand le repo ne porte pas assez de matière pour 5 lecteurs, fusionner dans cet ordre, qui regroupe les axes les plus proches :

1. `boucle` + `memoire` (ce qui traverse le temps d'une session)
2. `outils` + `extensibilite` (ce qui compose le système)
3. `exploitation` reste seule, ou tombe si le projet n'a ni postmortem ni gouvernance

## Repo sans documentation

C'est le cas qui casse un calibrage naïf. Le déroulé de référence a été validé sur un repo exceptionnellement bien documenté ; ne pas généraliser.

Sans `docs/`, réorienter les chemins de départ vers, dans l'ordre :

1. le fichier d'instructions destiné à leurs propres agents (`AGENTS.md`, `CLAUDE.md`), souvent la source la plus dense du repo
2. les README de packages, qui portent la doc réelle dans un monorepo
3. les tests, qui montrent le comportement attendu mieux que le code
4. les types et interfaces publiques
5. le code source lui-même, en dernier

## Sortie obligatoire de la reconnaissance

Pour chaque facette retenue : trois à huit chemins de départ nommés, existants, et disjoints de ceux des autres facettes.

Une facette sans chemin de départ nommé est une facette qu'on ne lance pas. Un lecteur envoyé sans chemins retombe sur les mêmes README que ses voisins, et son compte rendu ne vaut rien.
