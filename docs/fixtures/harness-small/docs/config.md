# Configuration

## Etat

Aucun fichier de configuration. Les reglages sont le budget par defaut, fixe dans `budget.ts`, et les arguments du CLI.

## Arguments

`args.ts` reconnait `--verbose` et prend le reste comme tache. Il n'y a ni `--help` ni validation : une tache vide est acceptee.

## Variables d'environnement

Aucune n'est lue aujourd'hui. `AGENTLET_MAX_TURNS` est evoquee dans la feuille de route sans exister.

## Decision

Pas de fichier de configuration tant qu'il n'y a que deux reglages. Le seuil retenu pour en introduire un est cinq reglages.

## Modele

Le CLI utilise un modele factice qui rend la tache et la longueur de la memoire. Brancher un vrai modele est le prochain chantier et fixera la premiere vraie option de configuration.
