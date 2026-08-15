# Gabarit du rapport de pillage

Le rapport de référence, à imiter en densité et en ton : `docs/fixtures/rapport-deepseek-harness.md` dans le repo du plugin.

## Frontmatter

Valeurs d'exemple réelles, capturées le 2026-08-15 via `gh api repos/deepseek-ai/deepseek-harness`.

```yaml
---
repo: deepseek-ai/deepseek-harness
url: https://github.com/deepseek-ai/deepseek-harness
mode: remote
date: 2026-08-15
repo_cree: 2026-08-13
repo_pousse: 2026-08-13
etoiles: 102269
licence: MIT
langage: TypeScript
facettes: [boucle, outils, memoire, extensibilite, exploitation]
lecteurs: 5
session: <nom de session>
session_id: <id harness>
bridge_url: <url claude.ai>
---
```

`mode` vaut `remote` ou `local`. En mode `local` sans remote GitHub, les champs `url`, `etoiles`, `repo_cree` et `repo_pousse` sont omis plutôt que remplis à vide.

Les trois champs de session viennent de :

```bash
RTK_DISABLED=1 bash ~/.claude/skills/session-whoami/scripts/*.sh --json
```

Ils se lisent dans `.identity.name`, `.identity.session_id` et `.identity.bridge_url`. Si le script est absent, les trois champs sont simplement omis. Aucune erreur, aucune valeur inventée.

## Sections du corps

L'ordre est imposé.

**1. Verdict en trois lignes.** Ce que c'est, ce que ça vaut, ce qu'on en tire. Un lecteur qui s'arrête là doit pouvoir décider.

**2. Ce que c'est.** Le projet en cinq à huit puces factuelles : nature, taille, langages, maturité, qui le fait tourner.

**3. Or.** Faible coût, gain réel, et manque confirmé par le réfutateur. Pour chaque entrée : la source avec son chemin, le mécanisme en deux lignes, et ce que ça donnerait chez Romain concrètement. Une entrée dont le manque a été retoqué ne peut pas figurer ici.

**4. Argent.** Bonnes idées à parquer. C'est aussi ici qu'atterrissent les trouvailles retoquées par le réfutateur, avec la preuve citée et la mention de ce que Claude Code fait déjà.

**5. Bronze.** Leçons de conception, rien à construire. Format court, une puce par leçon.

**6. Déjà-vu.** Ce qu'on a déjà, parfois en mieux. Section honnête, pas de complaisance : elle protège d'un chantier inutile.

**7. Couverture et limites.** Obligatoire, jamais omise. Elle dit :

- ce qui a été lu, et à quelle profondeur
- ce qui n'a pas été lu du tout
- que rien n'a été exécuté ni testé, et que les mécanismes cités viennent de la documentation du repo
- l'âge du repo et l'instabilité qui va avec, si le repo est récent ou porte un avertissement de compatibilité

## Règles de rédaction

- La synthèse n'est jamais une concaténation des comptes rendus de lecteurs. Un classement transversal est le travail attendu.
- Toute affirmation sur un mécanisme porte le chemin qui la fonde.
- Ce qui est déduit est marqué comme déduit.
- Ne pas coupler quoi que ce soit aux formats du repo exploré : voler des idées, pas des interfaces.
