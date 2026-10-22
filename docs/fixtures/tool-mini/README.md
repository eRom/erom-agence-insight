# tool-mini

Un faux outil pour Claude Code, utilise comme fixture de test. Il compresse la sortie des commandes shell pour economiser du contexte.

## Promesses chiffrees

- Reduit la sortie de `git status` de 80 % en moyenne.
- Ajoute moins de 5 ms de latence par commande.
- Installation en une seule ligne : copier `hook.sh` dans `~/.claude/hooks/`.

## Installation

Copier `hook.sh` dans le dossier des hooks puis le declarer dans `settings.json` sur l'evenement `PostToolUse`.

## Licence

MIT.
