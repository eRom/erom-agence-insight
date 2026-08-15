# DeepSeek Harness : rapport de veille

Date : 2026-08-15. Source : clone de `deepseek-ai/deepseek-harness` (créé le 13/08, ~100k étoiles, MIT, developer preview). Méthode : 5 lecteurs Sonnet en parallèle sur les docs subsystems, les packages, les skills embarquées et les postmortems, plus lecture directe de AGENTS.md, du système de notes et de la doc governance.

## Verdict en 3 lignes

Ce n'est pas du vaporware. C'est un harness complet type Claude Code, bâti sur Cordis (le framework de plugins de l'écosystème Koishi), avec une discipline d'ingénierie rare : docs machine-gated, postmortems, ~650 notes de décision écrites par leurs agents. Claude Code reste devant sur l'UX et la richesse (marketplace, tool Workflow, permissions, mobile), mais il y a de vraies idées à reprendre, surtout côté discipline d'exploitation.

## Ce que c'est

- `dsh` : CLI + Web UI (port 3080, loopback). « Everything is a plugin » : même la boucle d'agent est un plugin remplaçable, composé en YAML avec hot-reload en session.
- ~45 packages TypeScript, SDK Python, sandbox natif par OS (Landlock/bwrap Linux, Seatbelt macOS, ACL Windows).
- Dogfoodé par leurs propres agents : AGENTS.md racine très dense, 11 skills embarquées, notes de décision obligatoires par PR.
- Ils nous connaissent bien : ponts de compatibilité qui rejouent les hooks.json de Claude Code et Codex tels quels, et un tool `workflow` dont le vocabulaire (`agent()/pipeline()/parallel()/phase()`) est calqué sur celui de Claude Code.

## Or : 5 idées à reprendre, faible coût, gain réel

### 1. Verrou optimiste sur Edit
Source : `docs/subsystems/filesystem.md` (« Write and edit guards »). Chaque écriture porte la version du fichier observée au dernier read. Fichier changé entre-temps : refus net `FS_STALE_VERSION`, jamais d'écrasement silencieux.
Chez nous : un hook PreToolUse sur Edit/Write qui compare mtime ou hash au dernier Read de la session. Ça règle exactement le risque des sessions parallèles sur le même repo, qui repose aujourd'hui sur la seule discipline « relire avant Edit ».

### 2. Garde anti-boucle « repeat-tool-reminder »
Source : `packages/guard/repeat-tool-reminder`. Détecte les appels d'outil consécutifs identiques (args canonicalisés) et injecte un rappel de plus en plus insistant aux seuils 3/5/8. Consultatif, jamais bloquant.
Chez nous : un hook sur le même modèle que guard-tools.sh. Petit, utile sur les longues sessions autonomes.

### 3. Cycle de vie des notes de décision
Source : `.agents/notes/README.md`. Notes classées `proposed/implemented/rejected/archived`, section « Alternatives considered » obligatoire, supersession explicite, archives gelées à jamais. Leur phrase clé : une décision notée sans ce qu'elle a battu invite à re-débattre.
Chez nous : muscler `.claude/notes/` et la mémoire avec ce cycle. Le gate de corroboration existe déjà ; il manque le cycle rejected/archived et les alternatives obligatoires.

### 4. Template de handoff à 8 sections
Source : `packages/compaction/compaction-basic/README.md`. Leur résumé de compaction est forcé dans un template fixe : Primary Request, Key Technical Concepts, Files and Code, Errors and Fixes, Pending Jobs, Current Work, Next Step, Critical Context. Avec la règle « si un résumé précédent existe, fusionne, ne recopie pas ».
Chez nous : standardiser session-handoff et session-end sur ce squelette. Quasi gratuit, juste éditer les deux skills.

### 5. Skill anti-fuite de rédaction (« trim-cot-leakage »)
Source : `.agents/skills/dsh-trim-cot-leakage/SKILL.md`. Traque la prose qui parle depuis la session de rédaction au lieu de l'état actuel : citations mortes (« décision 7 »), narration de changement (« avant on faisait »), justifications adressées à un reviewer absent. Test unique : un lecteur à HEAD, sans le transcript, peut-il tout comprendre ?
Chez nous : une skill d'hygiène à passer sur playbook, gotchas et CLAUDE.md. Complète directement ta doctrine.

## Argent : bonnes idées, à parquer en notes

### 6. Le pattern « ralph » pour les boucles longues
Source : `packages/workflow/tool-ralph/README.md` + `packages/goal/`. Boucle autonome où chaque round est un agent NEUF sans historique. Seul lien entre rounds : un handoff JSON typé (`status: continue|complete|blocked` + résumé + preuves + prochaines étapes). La mémoire longue, c'est le disque. Anti-pourrissement de contexte par construction, pas par compaction.
Trois sous-idées recyclables tout de suite dans nos routines /loop et cron :
- le prompt de round : « inspecte l'état réel, ne fais pas confiance à la narration passée, preuve avant de déclarer complet » (`packages/goal/goal-round-driver/src/prompt.ts`) ;
- le wrap-up forcé : une boucle qui s'arrête doit produire un dernier message ancré sur des faits vérifiés et des artefacts, jamais un arrêt silencieux (`packages/goal/tool-goal/src/wrapup.ts`) ;
- le garde-fou anti-reprise : après redémarrage, un objectif « actif » ne reprend jamais seul, il faut un réarmement explicite (`docs/subsystems/goal.md`).

### 7. Spill-to-disk avec pointeur
Source : `docs/subsystems/spill.md`. Tout output d'outil trop gros est sauvé intégralement sur disque et remplacé en contexte par un aperçu + le chemin + la consigne de récupération. Plus propre que la compression rtk actuelle : rien n'est perdu, tout est récupérable.

### 8. Smoke-test pour erom-memory
Source : `examples/mcp-memory`. Leur protocole de vérification : écrire un fait unique en session A, ouvrir une session B fraîche, vérifier rappel puis usage. Simple, direct, à transposer en test de santé nocturne d'erom-memory.

### 9. Branche assets orpheline pour les GIFs
Source : `.agents/skills/record-browser-gif/SKILL.md`. Toute PR UI embarque un GIF tourné sur un vrai serveur, publié sur une branche orpheline « assets » (médias seulement, jamais mergée, append-only) et référencé en URL brute. L'historique git ne gonfle pas. Pour erom-taste-gate et plugin-release.

### 10. Étendre session-whoami en inspecteur de surface
Source : `packages/extensions/tool-cordis/README.md` (`cordis_inspect`). Leur agent interroge en live ce qui est réellement monté : services, plugins, outils. Chez nous : étendre session-whoami pour lister hooks, skills, MCP et permissions réellement actifs, générés depuis les settings, pas depuis la doc.

### 11. Leçon du postmortem 0003 pour la skill run
Source : `docs/postmortem/0003-web-agent-gui-feedback-loop.md`. Un agent a validé un serveur de remplacement au lieu de la page qu'il devait vérifier. Leçon : établir l'identité de l'instance déjà vivante avant de valider un changement, jamais en relancer une concurrente « pour voir ».

## Bronze : leçons de design, rien à construire

- « Model-visible ⟺ logged » : tout ce qui atteint une requête modèle doit être reconstructible depuis le log de session. Bel invariant.
- Enforcement de sandbox honnête : chaque exécution déclare `full` ou `partial` au lieu d'un booléen menteur.
- Un crash en plein tour ne tronque jamais le log : le tour orphelin est refermé avec un marqueur `interrupted`.
- Rappels planifiés en retard : fusion en UN tour de rattrapage (dernière occurrence seulement), jamais un backlog de N tours.
- Un job de fond est refusé si personne ne peut le lire ou le tuer.
- Doc governance : « one home per fact », budgets de mots vérifiés en CI, slop checklist passée en audit, blocs TypeScript des docs qui doivent compiler.
- Code Mode (le modèle écrit un programme qui appelle les outils, façon Cloudflare) : à suivre, mais pas actionnable localement, ça dépend du harness.

## Déjà-vu : ce qu'on a déjà, parfois en mieux

- Leur tool workflow : le nôtre est plus riche (budget de tokens, resume avec journal, isolation worktree, workflows imbriqués).
- Leurs bundles/patches YAML : la marketplace et `/plugin install` de Claude Code sont plus mûrs.
- Leur approval/sandbox : vocabulaire quasi identique aux permission modes.
- Leur LSP en tool : couvert chez nous par les plugins LSP par répertoire.
- Leur Web UI : loopback ou 0.0.0.0 sans TLS ; serve-dashboard + Tailscale fait mieux, et ils n'ont pas de mobile.
- Leurs subagents continuables et notices de fin : équivalent des teammates + SendMessage de cette session même.
- Leur schedule session-local : plus fragile que launchd + cron cloud.

## Couverture et limites

Lu : les ~40 docs subsystems, les README des packages clés, les 11 skills embarquées, AGENTS.md, le système de notes, les 4 postmortems, la doc governance. Non lu en profondeur : le code source lui-même (les docs de 50 Ko en diagonale), le website, le SDK Python, vendor/cordis. Les mécanismes cités viennent des docs du repo ; rien n'a été exécuté ni testé. Repo à J+2 avec avertissement explicite de casse de compatibilité : ne rien coupler à leurs formats, ne reprendre que les idées.
