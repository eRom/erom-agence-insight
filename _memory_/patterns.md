# Conventions

Mise à jour : 2026-08-15

## Structure d'un plugin eRom

Vérifié sur `erom-agence-gemini`, `erom-agence-marketing`, `erom-agence-devil`, `erom-agence-deep-research` :

- tout le publiable vit sous `plugin/`, jamais à la racine du repo
- le `name` du manifeste est court (`erom-insight`) même quand le repo porte le préfixe long (`erom-agence-insight`)
- la marketplace pointe dessus en `git-subdir` avec `path: "plugin"`
- `plugin/agents/*.md`, `plugin/skills/<nom>/SKILL.md`, `plugin/scripts/` quand il y a un binaire à piloter

## Frontmatter

Agent : `name`, `description`, `color`, `tools`, `model`.
Skill : `name`, `description` (les triggers sont écrits dedans), `argument-hint`.

Une description de skill doit dire aussi ce qu'elle **ne** couvre pas quand une skill voisine existe. Ici `harness` dit explicitement ne pas couvrir la rétro du harnais local, qui est `harness-review` dans le global.

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
