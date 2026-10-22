# harness-mini

Un faux agent en ligne de commande, utilise comme fixture de test. Il boucle sur un modele et quelques outils, avec un fichier `AGENTS.md` comme memoire de projet.

## Idees

- Boucle d'agent minimale dans `src/loop.ts`, bornee a 20 tours.
- Instructions de projet dans `AGENTS.md`, relues a chaque lancement.
- Les outils sont declares en une ligne chacun, sans framework.

## Utilisation

```
harness-mini "ma tache"
```

## Licence

MIT.
