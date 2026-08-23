# Conventions

Mise à jour : 2026-08-23

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

Une description de skill doit dire aussi ce qu'elle **ne** couvre pas quand une skill voisine existe. La disjonction est à quatre branches depuis le 2026-08-23 : `harness` (harnais concurrents), `tool-claude` (outils branchés sur Claude Code), `skill-claude` (skills et plugins tiers avant installation), `harness-review` (rétro du harnais local, dans le global) ; `skill-claude` renvoie en plus à la commande native `/skill-doctor` pour les skills déjà chargées. Les deux anciennes descriptions n'ont pas encore été mises à jour pour citer `skill-claude`.

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

## Calibrer un détecteur sur du vrai avant de le livrer

Le scanner de `skill-claude` a été passé, avant sa première éval, sur des skills connues saines : le plugin Linear d'Anthropic, `harness`, `tool-claude`, `skill-creator`, `superpowers` entier, trois skills globales. Deux faux rouges sont tombés à ce moment là et nulle part ailleurs : `display:none` dans un vrai HTML d'interface (le HTML caché ne compte désormais que dans les fichiers de consignes), et `font-size:0.8rem` pris pour `font-size:0`. Les lignes fautives sont recopiées telles quelles dans la liste des faux positifs de `secu-scan.test.py`. La règle : un détecteur qui n'a pas vu de corpus sain ne connaît pas son bruit.

## Mesurer un geste repris (skill `tool-claude`, temps 5)

Le candidat vit dans le scratchpad, la cible n'est touchée qu'après accord. La comparaison avant contre après se fait sur le **même corpus réel**, en réimplémentant le regex ou la règle du tiers dans son propre script : le code du dépôt exploré n'est jamais exécuté, la skill l'interdit et la réimplémentation suffit.

La mesure change le patch plus souvent qu'elle ne le confirme. Sur `claude-memory-kit` le 2026-08-16, le détecteur repris tel quel rendait 555 morts sur le corpus local contre 71 pour la version adaptée : le bruit pesait quatre fois le signal. Deux gestes séduisants ont été tués par le chiffre au lieu d'un débat (un triple plafond de mémoire, zéro fichier local au dessus du seuil ; un hook `SessionStart`, une seule référence morte dans la couche réellement injectée).

Lire les cas perdus un par un est ce qui rend la mesure opposable. Rejouer les cas abandonnés contre l'ancienne règle départage « bruit sans enjeu » de « vraie régression » : 484 cas perdus, tous du bruit (identifiants de modèles, branches git, chemins d'exemple), zéro régression.

## Suite de cas d'un patch posé

Convention `<nom>.test.<ext>` à côté du fichier, sur le modèle de `~/.claude/scripts/guard-tools.test.sh`. Deux listes, jamais une seule : ce qui doit se déclencher, et les faux positifs relevés dans le corpus réel, recopiés à l'identique. Les assertions portent sur le comportement, jamais sur un compte figé ni sur le contenu du source testé.

Un patch qui n'écrit rien doit avoir son invariant « n'écrit rien » dans la suite : contenu et liste du répertoire inchangés après exécution. Vérifié en plus hors suite sur le vrai corpus, par comparaison de `mtime`.

## Rédaction

**Vocabulaire :** « reprendre », jamais « voler ». « Rapport de veille », jamais « rapport de pillage ». Le plugin part sur une marketplace publique, le champ lexical du vol y est impubliable même quand il est exact.

Aucun tiret cadratin nulle part : un hook `guard-emdash` bloque tout Edit ou Write qui en contient, y compris recopié dans le `old_string`.

## Tester une skill avant de la livrer

Méthode skill-creator, appliquée à `skill-claude` le 2026-08-23 : les cas d'éval vivent dans `docs/evals/<skill>/evals.json` (prompts réalistes, résultat attendu), l'espace de travail dans le scratchpad de session (`<scratchpad>/<skill>-workspace/iteration-N/<cas>/{with_skill,without_skill}/`), jamais dans `plugin/`. Chaque cas est joué par un subagent `opus` avec la skill (« Base directory for this skill » et `$ARGUMENTS` reproduits dans le prompt, scratchpad et dossier de sortie imposés, consigne de ne poser aucune question) et un autre sans. Le subagent écrit aussi un `journal.md` de frictions : c'est lui qui a produit la quasi-totalité des correctifs, bien plus que les assertions. Les assertions se notent à la main sur preuves (grep, md5, listes de commandes), jamais sur la parole du subagent. Les baselines sans skill se réutilisent d'une itération à l'autre. La note d'acceptation (`docs/acceptation-<date>-<skill>.md`) porte les AC avec leur preuve, le benchmark et les limites du test.

## Documents de décision

Chaque arbitrage porte une ligne `**Battu :**` nommant l'alternative écartée et pourquoi elle a perdu. Le frontmatter porte `status: proposed | implemented | rejected` avec sa date. Régime adopté par Romain le 2026-08-15.

## Commits

Messages en français, sujet court puis corps qui explique le pourquoi. Terminés par `Co-Authored-By` et `Claude-Session`. Une branche de travail par chantier, mergée en fast-forward dans `main`.

Le repo ne porte **aucun commit de merge** (`git log --merges` sort vide), ce qui ne départage pas un merge fast-forward d'un commit direct. Le 2026-08-16, le chantier `tool-claude` a été committé directement sur `main` sur demande de Romain, sans qu'il le reprenne. `[candidat 1x - release erom-insight 0.4.0]` Le 2026-08-23, le chantier `skill-claude` a suivi la convention : branche, deux commits, merge fast-forward sur demande explicite (« merge dans main »), puis `/plugin-release`.

Le repo du plugin ne suit pas la convention `<type>(<portée>):` que la skill `plugin-release` propose ; les sujets y sont en français libre. La marketplace, elle, la suit. Vérifier avec `git log -3 --format='%B'` du repo concerné plutôt que d'appliquer une convention par défaut.
