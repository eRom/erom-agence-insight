# Architecture

## Deux packages

`packages/core` ne depend de rien et porte la boucle, les outils, la memoire et le budget. `packages/cli` depend de `core` et porte les arguments, le chargement de la memoire et l'affichage.

## Flux d'une execution

Le CLI lit la tache, charge `AGENTS.md`, construit un modele et un registre d'outils, appelle `runLoop`, puis affiche le resultat.

## Choix de style

Des fonctions et des types, pas de classes, pas d'injection de dependances. Le modele est une fonction, ce qui permet de le remplacer par un faux dans les tests.

## Frontieres

`core` n'ecrit jamais sur la sortie standard et ne lit que le fichier de memoire qu'on lui nomme. Toute interaction avec l'utilisateur vit dans `cli`.

## Dette connue

Le budget n'est pas branche, l'historique n'est pas compacte, les outils n'ont pas de schema. Chacun de ces points a sa page dans `docs/`.
