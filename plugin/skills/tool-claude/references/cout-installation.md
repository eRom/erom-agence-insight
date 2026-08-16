# L'inventaire du coût d'installation

Le tableau se remplit en entier. Un poste non chiffrable se déclare `non chiffré`, avec la raison. Il ne disparaît pas de la liste.

| Poste | Ce qu'il faut nommer | Où le trouver |
|---|---|---|
| Fichiers écrits dans le repo | chaque chemin, et s'il est fusionné ou écrasé | le code d'installation, un mode `--dry-run` s'il existe |
| Fichiers écrits **hors** du repo | chaque chemin absolu, et sa portée | idem, chercher `homedir`, `~`, `os.homedir` |
| Hooks posés | l'événement, le matcher, le timeout, la commande | le fichier qui fusionne les réglages |
| Coût par tour | ce qui s'exécute à chaque prompt et à chaque édition | les entrées `UserPromptSubmit`, `PostToolUse`, `Stop` |
| Tokens par session | ce qui est injecté au démarrage, puis à chaque tour | les fonctions de formatage du contexte injecté |
| Appels réseau | destination, fréquence, déclencheur | chercher `fetch`, `https`, un appel au registre de paquets |
| Ce qui est écrasé | statusline, instructions, permissions, réglages existants | la logique de fusion, et ses avertissements |
| Commande d'installation | passe-t-elle `~/.claude/scripts/guard-tools.sh` ? | la lancer à blanc, lire le code de sortie |
| Dépendances | natives, compilées, scripts de post-installation | le manifeste de paquet |
| Désinstallation | existe-t-elle ? que laisse-t-elle derrière ? | souvent absente, et c'est une réponse |

## Les trois postes qui décident

### Ce qui s'écrit hors du repo courant

Un outil qui touche `~/.codex/`, `~/.claude/settings.json` ou tout fichier de configuration utilisateur ne s'installe pas « pour ce projet ». Il s'installe pour **tous** les projets, y compris ceux où personne ne l'a demandé.

Cas de référence, graft : sélectionner l'hôte `agents` fait écrire dans `~/.codex/config.toml`, `~/.codex/hooks.json` et pose un shim, pour tout dépôt ouvert avec Codex.

### Ce qui est imposé au modèle à chaque tour

C'est le coût invisible, et souvent le plus élevé. Deux natures très différentes, à ne jamais additionner :

- **Injecté au démarrage de session** : payé une fois, mis en cache par le préfixe. Relativement bon marché.
- **Injecté à chaque prompt** : entrée fraîche à plein tarif, à chaque tour, pour toute la session.

Compte les caractères réels, divise par quatre pour une estimation de tokens, et multiplie par un nombre de tours plausible. Le résultat surprend.

Le second point à regarder n'est pas le volume mais **la nature de la consigne** : un outil qui injecte « prends mon outil en premier » entre en concurrence avec la doctrine déjà en place. Un texte impératif dans le contexte de session n'est pas un complément, c'est un concurrent.

### La latence par tour

Un hook `UserPromptSubmit` qui lance un processus fils s'exécute avant **chaque** message. Note son budget déclaré et ce qu'il fait vraiment. Un budget de quinze secondes sur chaque prompt, y compris « lance les tests », se paie en attente réelle.

## Le verdict de proportion

Après le tableau, une seule question, écrite dans le rapport : **est-ce que le coût est proportionné à la taille de nos dépôts et à notre usage ?**

Un outil d'indexation dont le bénéfice croît avec la taille du dépôt est une mauvaise affaire sur cent fichiers, quel que soit le soin de son code. Dis-le comme ça, sans détour.
