# Conventions

Mise à jour : 2026-08-16

## Structure d'un plugin eRom

Vérifié sur `erom-agence-gemini`, `erom-agence-marketing`, `erom-agence-devil`, `erom-agence-deep-research` :

- tout le publiable vit sous `plugin/`, jamais à la racine du repo
- le `name` du manifeste est court (`erom-insight`) même quand le repo porte le préfixe long (`erom-agence-insight`)
- la marketplace pointe dessus en `git-subdir` avec `path: "plugin"`
- `plugin/agents/*.md`, `plugin/skills/<nom>/SKILL.md`, `plugin/scripts/` quand il y a un binaire à piloter

Le manifeste déclare `"skills": "./skills/"`, un **répertoire**, là où `"agents"` est une liste de chemins. Ajouter une skill ne demande donc aucune touche au manifeste : créer `plugin/skills/<nom>/SKILL.md` suffit, elle est découverte. Vérifié le 2026-08-16 en ajoutant `tool-claude` sans modifier le champ. Ajouter un **agent**, lui, oblige à éditer la liste.

## Frontmatter

Agent : `name`, `description`, `color`, `tools`, `model`.
Skill : `name`, `description` (les triggers sont écrits dedans), `argument-hint`.

Une description de skill doit dire aussi ce qu'elle **ne** couvre pas quand une skill voisine existe. La disjonction est à trois branches depuis le 2026-08-16 : `harness` ne couvre ni les outils tiers (`tool-claude`) ni la rétro du harnais local (`harness-review`, dans le global) ; `tool-claude` renvoie aux deux autres de la même façon.

Le nom d'une skill sert d'abord à Romain qui la tape. `tool` a été renommée `tool-claude` juste après sa création, pour cette seule raison : le préfixe `/erom-insight:` ne suffit pas à s'y retrouver dans le sélecteur.

## Gate de vérification

Deux commandes, jamais une seule. La seconde existe parce que la première ne lit pas les frontmatters (voir `gotchas.md`).

```bash
RTK_DISABLED=1 command claude plugin validate <repo>/plugin --strict

RTK_DISABLED=1 command find plugin -name '*.md' \( -path '*/agents/*' -o -name 'SKILL.md' \) -print0 \
  | while IFS= read -r -d '' f; do
      if RTK_DISABLED=1 command head -12 "$f" | RTK_DISABLED=1 command grep -q '^name:' \
      && RTK_DISABLED=1 command head -12 "$f" | RTK_DISABLED=1 command grep -q '^description:'; then
        echo "ok   $f"; else echo "KO   $f"; fi
    done
```

## Rédaction

**Vocabulaire :** « reprendre », jamais « voler ». « Rapport de veille », jamais « rapport de pillage ». Le plugin part sur une marketplace publique, le champ lexical du vol y est impubliable même quand il est exact.

Aucun tiret cadratin nulle part : un hook `guard-emdash` bloque tout Edit ou Write qui en contient, y compris recopié dans le `old_string`.

## Documents de décision

Chaque arbitrage porte une ligne `**Battu :**` nommant l'alternative écartée et pourquoi elle a perdu. Le frontmatter porte `status: proposed | implemented | rejected` avec sa date. Régime adopté par Romain le 2026-08-15.

## Commits

Messages en français, sujet court puis corps qui explique le pourquoi. Terminés par `Co-Authored-By` et `Claude-Session`. Une branche de travail par chantier, mergée en fast-forward dans `main`.

Le repo ne porte **aucun commit de merge** (`git log --merges` sort vide), ce qui ne départage pas un merge fast-forward d'un commit direct. Le 2026-08-16, le chantier `tool-claude` a été committé directement sur `main` sur demande de Romain, sans qu'il le reprenne. `[candidat 1x - release erom-insight 0.4.0]`

Le repo du plugin ne suit pas la convention `<type>(<portée>):` que la skill `plugin-release` propose ; les sujets y sont en français libre. La marketplace, elle, la suit. Vérifier avec `git log -3 --format='%B'` du repo concerné plutôt que d'appliquer une convention par défaut.
