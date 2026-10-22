# La boucle

## Role

La boucle est le coeur de l'agent. Elle transforme une tache en une suite d'appels au modele et aux outils, et s'arrete quand le modele n'a plus rien a demander. Tout le reste du projet existe pour la nourrir ou la borner.

## Etat entre deux tours

Il n'y a qu'un etat : l'historique, un tableau de chaines. Chaque entree est prefixee par son emetteur (`user:`, `assistant:`, `tool(nom):`). Ce format est volontairement pauvre : il se lit a l'oeil nu dans un terminal et se rejoue tel quel dans un test.

## Arret

Deux conditions d'arret : une reponse sans appel d'outil, ou le plafond de tours. Le plafond rend le texte fixe `turn limit reached`, sans lever d'erreur, pour que l'appelant n'ait pas a distinguer un echec d'une fin normale. Ce choix a deja cause une confusion : un utilisateur a pris le texte fixe pour une reponse du modele.

## Erreurs d'outil

Un outil inconnu n'arrete rien : la boucle ecrit `unknown tool <nom>` dans l'historique et laisse le modele se corriger. Un outil qui leve une exception, en revanche, remonte jusqu'au CLI et termine le processus. La difference est documentee ici parce qu'elle surprend.

## Parallelisme

Aucun. Les outils d'un meme tour s'executent l'un apres l'autre, dans l'ordre demande par le modele. Le jour ou un outil sera lent, ce sera la premiere optimisation a faire, mais elle change l'ordre des sorties dans l'historique et donc le comportement du modele.

## Compaction

L'historique n'est jamais resume. Sur une tache de plus d'une dizaine de tours, il depasse la fenetre du modele. Le budget de caracteres de `budget.ts` devait servir de declencheur, mais il n'est pas encore branche dans la boucle.
