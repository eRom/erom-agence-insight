# Les cinq facettes d'un harnais

Une facette est un axe de lecture confié à un seul lecteur. Ces cinq axes sont ceux qui, sur un harnais ou un agent CLI, produisent des trouvailles plutôt que des résumés.

Les identifiants sont normatifs : ils sont repris tels quels dans le champ `facettes` du frontmatter du rapport.

## `boucle` : boucle d'agent et contexte

**Question centrale.** Comment un tour est construit, et que voit réellement le modèle ?

**Où chercher.** Documentation sur le contexte, la compaction, le résumé de session, le déversement sur disque des sorties trop grosses, le format des logs de session, la reprise après interruption.

**Signaux qui valent de l'or.** Un invariant explicite entre ce qui atteint le modèle et ce qui est tracé. Une stratégie de compaction qui impose un gabarit plutôt qu'un résumé libre. Un traitement des sorties massives qui ne perd rien. Une boucle longue dont chaque tour repart d'un contexte neuf.

## `outils` : outils, permissions, sandbox

**Question centrale.** Quel catalogue d'outils, quel modèle d'approbation, quelle isolation réelle ?

**Où chercher.** Documentation sandbox et permissions, définitions d'outils, garde-fous, mécanismes de confirmation, gestion des secrets.

**Signaux qui valent de l'or.** Un aveu honnête du niveau d'isolation réellement atteint plutôt qu'un booléen rassurant. Un garde-fou consultatif qui alerte sans bloquer. Une protection contre l'écrasement concurrent. Un refus net et nommé plutôt qu'un échec silencieux.

## `memoire` : mémoire, notes, persistance

**Question centrale.** Qu'est-ce qui survit entre deux sessions, et comment on reprend après un crash ?

**Où chercher.** Système de notes ou de décisions, état persisté, mécanismes de reprise et de passation, format des résumés entre sessions.

**Signaux qui valent de l'or.** Un cycle de vie explicite des décisions, avec ce qu'une décision a battu. Un gabarit de passation imposé plutôt que libre. Un objectif interrompu qui ne redémarre jamais tout seul. Une règle disant où chaque fait a son unique domicile.

## `extensibilite` : comment un tiers ajoute une capacité

**Question centrale.** Par où passe quelqu'un qui veut étendre le système sans toucher au cœur ?

**Où chercher.** Plugins, skills, hooks, marketplace, points d'extension, composition de la configuration, rechargement à chaud.

**Signaux qui valent de l'or.** Un cœur lui-même remplaçable par le mécanisme d'extension. Un pont de compatibilité qui rejoue la configuration d'un concurrent telle quelle. Une composition déclarative avec rechargement en session.

## `exploitation` : la discipline que le projet s'impose

**Question centrale.** Que s'imposent-ils à eux-mêmes, et qu'est-ce que ça révèle de leurs cicatrices ?

**Où chercher.** Postmortems, gouvernance de la documentation, dogfooding, CI, conventions de contribution, fichiers d'instructions destinés à leurs propres agents.

**Signaux qui valent de l'or.** Des postmortems écrits, avec la leçon détachée du cas. Des budgets de documentation vérifiés en intégration continue. Une checklist anti-remplissage. Des instructions d'agent denses qui trahissent des erreurs passées.

## Règle de disjonction

Deux facettes ne partagent jamais un chemin de départ. Si un document couvre deux facettes, il est assigné à une seule, et le brief de l'autre lecteur cite ce chemin dans ses chemins interdits.

Sans cette règle, les lecteurs convergent tous sur les mêmes gros documents et la synthèse reçoit cinq fois la même chose.
