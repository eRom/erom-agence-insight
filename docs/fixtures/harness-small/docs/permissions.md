# Permissions

## Etat actuel

Aucun outil n'est soumis a permission. Tout ce qui est declare dans le registre s'execute des que le modele le demande.

## Pourquoi c'est acceptable aujourd'hui

Les trois outils fournis n'ont aucun effet de bord. Le risque apparait au premier outil qui touche un fichier, un processus ou le reseau.

## Piste : liste d'autorisations

Une fonction `allow(call)` evaluee avant chaque execution, avec trois etats : autorise, refuse, a confirmer. Le CLI poserait la question a l'utilisateur pour le troisieme.

## Piste : bac a sable

Executer les outils dans un processus separe aux droits reduits. Plus sur, mais cela introduit un protocole entre processus et ruine la simplicite du projet.

## Decision en attente

Aucune des deux pistes n'est retenue. La regle provisoire est de ne declarer que des outils sans danger.
