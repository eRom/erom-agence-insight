# Exploitation

## Journalisation

Rien en dehors de la sortie standard. En mode `--verbose` le CLI entoure le resultat de deux lignes de separation. Il n'existe pas de journal structure et pas de niveau de log.

## Garde-fous

Le plafond de 12 tours est la seule protection contre une boucle sans fin. Il a ete atteint une fois en usage reel, quand le modele redemandait le meme outil avec la meme entree a chaque tour.

## Incident de la boucle repetee

Cet incident a coute douze appels modele inutiles. Aucun postmortem formel n'a ete ecrit ; la piste retenue est de detecter la repetition d'un meme appel avec la meme entree et de rendre la main plus tot.

## Budget

Un budget en caracteres existe dans `budget.ts` mais n'est pas lu par la boucle. Il n'y a pas de budget en jetons ni en temps.

## Erreurs du modele

Elles remontent telles quelles au processus. Pas de reprise, pas de nouvelle tentative, pas de repli sur un autre modele.

## Versions

Le `CHANGELOG.md` tient la liste des versions. Il n'y a pas de procedure de publication : le projet n'est pas publie.
