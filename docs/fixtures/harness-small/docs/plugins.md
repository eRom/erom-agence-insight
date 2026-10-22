# Extensions

## Position

Il n'y a pas de systeme de plugins, et ce n'est pas un oubli. Le projet vise la lisibilite : un lecteur doit pouvoir comprendre tout le code en une heure.

## Cout d'un systeme de plugins

Un chargeur, un format de manifeste, une resolution de versions, une surface de securite. Chacun de ces elements est plus gros que la boucle elle-meme.

## Extension en code

Etendre l'agent revient a ecrire un registre d'outils et a le fusionner avec `mergeTools`. Le cout est de recompiler. Le gain est qu'aucun code tiers ne s'execute sans avoir ete lu par celui qui l'integre.

## Extension par la memoire

On peut aussi changer le comportement de l'agent sans code, en editant `AGENTS.md`. C'est le seul point d'extension accessible a un utilisateur non developpeur.

## Piste ecartee

Charger des modules depuis un dossier au demarrage a ete prototype puis abandonne : l'ordre de chargement changeait le resultat de `mergeTools` en cas de collision, et les erreurs d'import etaient difficiles a rattacher a un module.
