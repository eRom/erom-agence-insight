# Tests

## Etat

Un seul test, `tests/loop.test.ts`, qui verifie le plafond de tours avec un modele qui redemande toujours un outil. Il s'execute directement avec bun, sans cadre de test.

## Pourquoi ce test d'abord

Le plafond est le seul garde-fou de la boucle. Si une modification le casse, l'agent peut tourner sans fin et consommer du quota.

## Faux modeles

Un modele est une fonction, donc un test en ecrit un en trois lignes : une reponse scriptee par tour. Aucune bibliotheque de mocks n'est necessaire.

## A ajouter

Collision de noms dans `mergeTools`, fichier de memoire absent et fichier trop long dans `loadMemory`, `parseArgs` avec et sans `--verbose`.

## Ce qu'on ne teste pas

Le texte exact des messages, qui change souvent. On teste les comportements : l'arret, le choix des outils, la coupe de la memoire.
