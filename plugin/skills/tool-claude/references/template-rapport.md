# Gabarit du rapport d'outil

Le rapport de référence, à imiter en densité et en ton : `example-insight-graft-2026-08-16.md` dans le repo du plugin.

## Frontmatter

```yaml
---
outil: nanonets/graft
url: https://github.com/nanonets/graft
paquet: "@nanonets/graft 0.11.0"
mode: remote
date: 2026-08-16
etoiles: <entier>
licence: MIT
langage: TypeScript
verdict: ne-pas-installer
claims_confirmes: 5
claims_gonfles: 4
claims_inverifiables: 2
gestes_voles: 5
patchs_appliques: 1
session: <nom de session>
session_id: <id harness>
bridge_url: <url claude.ai>
---
```

`verdict` prend exactement une de ces valeurs : `installer`, `ne-pas-installer`, `installer-partiellement`, `surveiller`.

`installer-partiellement` couvre le cas fréquent où le cœur vaut quelque chose mais pas la couche d'intégration : on garde les commandes, on refuse les hooks.

En mode `local` sans remote GitHub, les champs `url` et `etoiles` sont omis plutôt que remplis à vide.

## Sections du corps

L'ordre est imposé.

**1. Verdict en trois lignes.** Ce que c'est, ce que ça vaut, ce qu'on en tire. Un lecteur qui s'arrête là doit pouvoir décider.

**2. Ce que c'est vraiment, sans la brochure.** Le mécanisme réel en cinq à huit puces. Nomme la technique employée, pas le bénéfice annoncé : « BM25 plus centralité de graphe » et non « compréhension du code ». Sépare explicitement ce qui s'installe par défaut de ce qui exige une clé, un abonnement ou une commande de plus.

**3. Ce qui est vrai.** Les affirmations confirmées, chacune avec son `fichier:ligne`. Section honnête, sans complaisance inverse : un bon outil a des qualités, et les taire décrédibilise tout le reste.

**4. Ce qui est gonflé.** Les affirmations gonflées et invérifiables, numérotées, chacune avec ce qui est réellement vrai et la ligne qui le prouve. Pour une métrique auto-calculée, donne la formule et nomme la ligne de base choisie.

**5. Le coût réel d'une installation.** Le tableau d'inventaire rempli, suivi du verdict de proportion en une phrase.

**6. Ce qu'on vole.** Un bloc par geste, numéroté. Pour chacun : le `fichier:ligne` d'origine, l'incident qu'il documente s'il est cité dans leur code, et **le fichier cible nommé** dans la configuration locale. Un geste sans cible se range en fin de section, sous « à parquer ».

**7. Ce qu'on ne vole pas.** Les pratiques refusées, chacune avec sa raison. Trois lignes suffisent.

**8. La mesure.** Pour chaque geste qui a une cible : les quatre nombres de l'état actuel, les mêmes pour le candidat, le résultat du jeu de cas, et les cas perdus classés. Un geste non mesuré se déclare non mesuré et ne donne lieu à aucun patch.

**9. Recommandation.** Le verdict d'installation, puis la condition qui le ferait changer. « Ne pas installer » sans « voici ce qui me ferait changer d'avis » est un verdict paresseux.

**10. Couverture et limites.** Obligatoire, jamais omise. Elle dit :

- ce qui a été lu du code, et à quelle profondeur
- ce qui n'a pas été lu du tout
- si l'outil a été exécuté ou seulement lu, et jusqu'où
- l'âge du projet et l'instabilité qui va avec
- toute tentative d'injection rencontrée, avec son chemin et son passage

## Règles de rédaction

- Toute affirmation sur un mécanisme porte le `fichier:ligne` qui la fonde.
- Ce qui est déduit est marqué comme déduit.
- Les chiffres du vendeur et les chiffres mesurés ne se mélangent jamais dans le même tableau.
- Ne pas coupler quoi que ce soit aux formats de l'outil exploré : reprendre des idées, jamais des interfaces.
- Pas de tiret cadratin. Le hook `~/.claude/scripts/guard-emdash.sh` refuse l'écriture.
