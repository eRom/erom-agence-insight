# Mesurer un geste volé sur le corpus local

Un geste volé à un outil tiers vise un fichier de la configuration locale. Avant d'y toucher, on mesure. La mesure change le patch dans la majorité des cas.

## Les corpus disponibles

| Corpus | Chemin | Ce qu'il répond |
|---|---|---|
| Transcripts de session | `~/.claude/projects/*/*.jsonl` | ce que Romain écrit vraiment, à quelle fréquence |
| Hooks installés | `~/.claude/settings.json` | ce qui s'exécute, sur quel événement |
| Scripts de hook | `~/.claude/hooks/`, `~/.claude/scripts/` | ce que chacun injecte, et à quel coût |
| État des hooks | `~/.claude/hooks/state/` | la convention de persistance à imiter |

## Le piège qui fausse tout : les faux prompts utilisateur

Un transcript contient beaucoup d'enregistrements `"type": "user"` qui ne sont **pas** des prompts tapés par Romain, et sur lesquels un hook `UserPromptSubmit` ne se déclenche jamais :

- les chargements de skill (`Base directory for this skill: ...`), marqués `isMeta`
- les notifications de fin de tâche (`<task-notification>`)
- les messages entre sessions (`<teammate-message>`)
- les tours de sous-agents, marqués `isSidechain`
- les résultats d'outil, qui arrivent en liste plutôt qu'en chaîne
- les reprises après compaction et les relances système

Compter sans filtrer gonfle tout. Mesure du 2026-08-16 : **57 %** de taux de déclenchement sans filtre, **20 %** avec. Le premier chiffre aurait justifié un chantier trois fois plus gros que nécessaire.

Le filtre vérifié, à reprendre tel quel :

```python
if d.get("type") != "user":
    continue
if d.get("isMeta") or d.get("isSidechain") or d.get("agentName") or d.get("teamName"):
    continue
c = d.get("message", {}).get("content")
if not isinstance(c, str) or not c.strip():   # un vrai prompt tape est une chaine brute
    continue
if c.startswith(("<task-notification", "<teammate-message", "<local-command",
                 "[Request interrupted")):
    continue
```

Les commandes slash (`/eff`, `/harness`) **sont** de vrais prompts et déclenchent bien le hook. Ne les filtre pas.

Avant de croire un chiffre, sors une dizaine d'exemples de déclenchement et lis-les. Si des lignes qui ne ressemblent pas à Romain apparaissent, le filtre est encore percé.

## Les quatre nombres à produire

Pour l'état actuel comme pour le candidat :

1. **Volume** : combien de fois sur combien d'occasions réelles, en pourcentage.
2. **Coût** : caractères injectés divisés par quatre, sommés sur le corpus.
3. **Concentration** : le pire cas. Une moyenne acceptable peut cacher une session qui encaisse soixante-six fois le même bloc.
4. **Cause dominante** : quel déclencheur produit quelle part du total. C'est ce nombre qui désigne le vrai problème, souvent différent du geste volé.

Le quatrième est le plus rentable. Au 2026-08-16, le geste volé était un plafond d'injections. La mesure a montré que 89 % des déclenchements venaient d'un seul motif trop large, qui matchait des mots français ordinaires. Le plafond seul aurait laissé le bruit intact.

## La simulation avant contre après

Charge l'ancien et le nouveau module côte à côte, rejoue le même corpus dans les deux, rapporte les deux séries. Le candidat vit dans le scratchpad, jamais sur la cible.

Rejoue en simulant l'état par session, sinon un plafond ou une porte de nouveauté ne se voient pas : ils dépendent de ce qui a déjà été émis dans **cette** session.

## Le jeu de cas écrit à la main

Deux listes, jamais une seule. Dix cas chacune suffisent.

- **Doivent se déclencher** : les cas que le mécanisme existe pour attraper, formulés comme Romain les écrirait.
- **Doivent rester muets** : les faux positifs constatés dans le corpus, recopiés à l'identique.

Ces cas assertent un **comportement**. Ils ne comptent pas d'entrées, ne figent pas de version, et ne lisent jamais le source du fichier testé. Un test qui vérifie qu'une implémentation contient une chaîne échoue sur un refactor correct et passe sur une implémentation cassée.

## Lire les cas perdus, un par un

Tout cas qui se déclenchait avant et plus après doit tomber dans une de ces trois cases :

| Case | Décision |
|---|---|
| bruit, aucun enjeu | tant mieux, c'est le but |
| trou qui existait déjà avant | le nommer dans le rapport, ne pas le boucher au passage |
| vraie régression | corriger le candidat, tout remesurer |

Vérifie la deuxième case en rejouant le cas contre l'**ancien** module. S'il ne se déclenchait pas non plus, ce n'est pas ta régression, et il n'entre pas dans le périmètre.

## Ce qu'on ne mesure jamais

Pas de métrique auto-calculée. On ne reproduit pas chez soi le défaut qu'on vient de reprocher au tiers. Un gain se mesure en rejouant deux états sur le même corpus réel, jamais en estimant « ce qu'on aurait consommé sinon ».
