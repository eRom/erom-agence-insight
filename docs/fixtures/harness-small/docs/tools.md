# Les outils

## Contrat

Un outil est une fonction `(input: string) => Promise<string>`. Entree et sortie sont du texte, sans schema. Le modele choisit un nom et fournit une chaine ; l'outil la parse comme il l'entend.

## Registre

Le registre est un objet indexe par nom. `mergeTools` en fusionne plusieurs, le dernier gagnant en cas de collision. Ce comportement permet a l'appelant de surcharger un outil fourni, mais masque aussi les fautes de frappe dans les noms.

## Outils fournis

`echo`, `length` et `upper` n'ont aucun effet de bord. Ils existent pour tester la boucle et pour montrer la forme d'un outil. Aucun outil de fichier, de shell ou de reseau n'est livre, par choix de securite.

## Decouverte

`describeTools` rend la liste triee des noms. Elle est destinee au prompt du modele. Aucune description n'accompagne les noms : le modele devine l'usage d'un outil a son nom, ce qui marche pour `echo` et pas au-dela.

## Ajouter un outil

Declarer la fonction dans un registre, passer le registre a `runLoop`. Pas d'enregistrement global, pas de decouverte par dossier. Une idee evoquee : charger un fichier par outil depuis un dossier `tools/`, avec le nom du fichier pour nom d'outil.

## Securite

Tout outil declare est executable sans confirmation. Voir `permissions.md` pour la piste d'une liste d'autorisations.
