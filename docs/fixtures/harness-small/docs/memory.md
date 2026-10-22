# La memoire

## Principe

La memoire de projet est un fichier texte, `AGENTS.md`, a la racine du dossier de travail. Il est lu en entier a chaque lancement et passe au modele avant la tache. L'agent ne l'ecrit jamais.

## Chargement

`loadMemory` rend une chaine vide si le fichier est absent, et coupe a 20000 caracteres sinon. La coupe est brutale : elle peut tomber au milieu d'une phrase, voire d'une regle. Un test devrait verifier au moins que la coupe ne leve pas d'erreur.

## En-tete

`memoryHeader` compte les lignes non vides et rend une ligne de resume. Elle est affichee en mode `--verbose` pour que l'utilisateur voie si son fichier a bien ete lu.

## Portee

Une seule portee : le projet courant. Pas de memoire globale a l'utilisateur, pas de memoire d'equipe, pas de memoire par session. Tout ce qui n'est pas dans `AGENTS.md` est perdu a la fin du processus.

## Oubli

Aucun mecanisme. Le fichier croit tant que l'utilisateur ne l'elague pas, et le plafond de 20000 caracteres finit par couper les regles les plus recentes, qui sont en bas du fichier. C'est un defaut connu, non corrige.

## Pourquoi si simple

Un fichier texte se versionne, se relit, se corrige a la main et se diffe. Les alternatives envisagees, une base de vecteurs ou un fichier JSON structure, ajoutaient une dependance et rendaient la memoire opaque pour l'utilisateur.
