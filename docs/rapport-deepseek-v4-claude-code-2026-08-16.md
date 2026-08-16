# DeepSeek V4 dans Claude Code : rapport et réglages

Chantier du 2026-08-16. Objets : les modèles `deepseek-v4-flash` (checkpoint Flash-0731) et `deepseek-v4-pro` (checkpoint Pro-0813), le harnais officiel dsh (deepseek-harness, cloné et disséqué), et des tests réels de Claude Code 2.1.233 branché sur l'API DeepSeek avec la clé du compte (solde 2,81 $, quasi intact après tous les tests).

Sources : repo dsh lu en direct (samples/deepseek-harness), doc officielle DeepSeek vérifiée par fetch direct, tests headless mesurés, session log dsh autopsié. Veille modèles détaillée : `docs/veille-deepseek-v4-flash-pro-2026-08.md`. Notes de chantier : `.claude/notes/2026-08-16-deepseek-v4-dsh.md`.

Complément indissociable : l'insight harness du 2026-08-15 (`~/.claude/erom-plugin-artefacts/insights/deepseek-ai-deepseek-harness-2026-08-15.md`) répond à l'autre question, « qu'est-ce que dsh apprend à NOTRE harnais » (5 gestes or : supersession mémoire, exit codes du guard, anti-fuite de rédaction, postmortem avec test, presets de sécurité). Ce rapport-ci n'en recopie pas la matière. Contexte utile qu'il apporte : le repo dsh a été créé le 2026-08-13, il avait DEUX JOURS au moment de l'analyse (102k étoiles déjà), sandbox natif par OS (Landlock/bwrap Linux, Seatbelt macOS, ACL Windows), et leur doc reconnaît elle-même Claude Code comme source du vocabulaire de leur outil workflow.

## TL;DR

Ça marche, et bien. Claude Code sur V4 est un chemin officiel documenté par DeepSeek, pas un hack : leurs outils sont des quasi-clones des nôtres (mêmes exemples mot pour mot dans les descriptions), leurs modèles sont entraînés sur ce format. Testé ce matin : outils, thinking, multi-tour, français du CLAUDE.md, tout passe. Le vrai enseignement de dsh n'est pas un réglage magique : c'est une discipline. System prompt de ~900 tokens (contre ~36 000 de préambule chez nous), rien ne casse jamais le préfixe du cache (même la compaction est cache-alignée), et les garde-fous sont mécaniques (rappels anti-boucle injectés, résultats d'outils rabotés) plutôt que prêchés dans la prose système.

## 1. La config prête à coller

C'est la config du guide officiel DeepSeek pour Claude Code, vérifiée variable par variable (doc env-vars Claude Code 2.1.x), testée ce matin :

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=$DEEPSEEK_API_KEY
export ANTHROPIC_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export ANTHROPIC_SMALL_FAST_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432
```

Lecture :
- Doctrine DeepSeek assumée : **Pro au volant, Flash pour les sous-agents** et les tâches d'arrière-plan. Pour une session pur digest ou exploration, `--model deepseek-v4-flash` suffit et coûte des miettes.
- `EFFORT_LEVEL=max` : les deux modèles ont 3 niveaux de thinking (low, high, max). dsh tourne en high par défaut, ton `~/.dsh/settings.yaml` est déjà en max. Le thinking est actif par défaut via l'endpoint (vérifié dans les transcripts), `budget_tokens` est ignoré (on/off seulement).
- `AUTO_COMPACT_WINDOW=786432` : reco DeepSeek. Claude Code plafonne un modèle inconnu à 200k sans recours officiel, donc l'effet réel est borné. Pas grave : V4 a une rétention stable jusqu'à ~128k puis décline progressivement (arXiv 2606.19348). Le plafond de Claude Code tombe pile dans la zone de confort du modèle.
- Ne JAMAIS mettre ces variables dans l'env global : session dédiée uniquement (prefix `env VAR=... claude` ou un profil shell séparé). `ANTHROPIC_API_KEY`/`AUTH_TOKEN` posé globalement débranche les connecteurs claude.ai de tes sessions normales.

Piège de vérification : un nom de modèle inconnu bascule **silencieusement** sur Flash. Contrôle en headless : `jq '.modelUsage | keys'` sur la sortie JSON.

## 2. Ce que les tests ont montré

Tous les tests du matin, sur ta clé, mesurés :

| Test | Résultat |
|---|---|
| Curl direct endpoint anthropic | OK, bloc thinking signé + cache accounting au format Anthropic |
| `claude -p` simple (2+3) | OK en 2 s, 1 tour. 36 034 tokens d'input à vide (harnais + CLAUDE.md) |
| Tool calling (Write) | OK, 2 tours, fichier créé conforme, réponse en français (CLAUDE.md respecté) |
| Thinking | Actif par défaut, blocs présents dans tous les transcripts (le compteur `thinking_tokens: 0` est un artefact d'affichage, DeepSeek ne remplit pas ce champ) |
| Tâche de code complète (script bun + CSV + run + fix), Flash | Réussite du 1er coup, 4 tours, 19 s, sortie 1 946 tokens |
| Même tâche, Pro | Réussite du 1er coup, 4 tours, 19 s, sortie 1 345 tokens, ET auto-vérification spontanée des résultats (tri, somme, médiane recalculés) |
| Même tâche, dsh headless (Flash, effort max) | Réussite du 1er coup, **11,6 s** |
| Cache intra-session | OK : 36k puis ~75k tokens lus du cache aux steps suivants |
| Cache inter-sessions | KO sur nos essais : les ~36k du harnais sont repayés à chaque session neuve |

Le différentiel dsh vs Claude Code (11,6 s vs 19 s) s'explique presque entièrement par le poids mort : ~900 tokens de système chez eux, ~36 000 chez nous. La qualité du travail était identique sur cette tâche.

Sur le cache inter-sessions : le caching DeepSeek est automatique, par préfixe, sans `cache_control` (ignoré par l'endpoint). Nos runs séparés n'ont jamais réutilisé le préfixe d'une session précédente. Cause non tranchée (durée de vie floue côté doc, best-effort serveur, ou un élément variable dans le préfixe de requête de Claude Code). Impact réel faible : en session interactive, l'essentiel des requêtes sont des steps successifs, et là le cache prend.

## 3. Les modèles, l'essentiel

| | V4-Flash-0731 | V4-Pro-0813 |
|---|---|---|
| Architecture | MoE 284B total, 13B actifs | MoE 1.6T total, 49B actifs |
| Contexte | 1M (stable ~128k, dégradation progressive au-delà) | idem |
| Sortie max | 384k (en effort high/max) | idem |
| Terminal-Bench 2.1 (officiel) | 82.7 | 87.9 |
| Rôle recommandé | Sous-agents, digests, mécanique | Main loop, arbitrages |

- Les noms API `deepseek-v4-flash` / `deepseek-v4-pro` sont stables ; les checkpoints (0731, 0813) glissent dessous à chaque release. `deepseek-chat` et `deepseek-reasoner` sont morts depuis le 24/07/2026.
- Prompting officiel : température 1.0, top_p 0.95 en agentique. Claude Code est déjà aligné. Aucun guide de prompting officiel au-delà.
- Aucun SWE-bench Verified officiel. Les chiffres qui circulent viennent de blogs tiers contradictoires, dont un réseau de sites spam SEO identifié pendant la veille (liste dans le rapport de veille). Méfiance par défaut sur ce sujet.
- Poids ouverts (MIT) sur HF, mais 304B/1.7T : aucun run local possible. Ollama ne les sert qu'en tags `:cloud`. Le « cache Ollama » du brief initial était une fausse piste : zéro occurrence d'Ollama dans tout le repo dsh.

### Pricing : hausse CE SOIR 18h (heure française)

Passage en peak/off-peak le 16/08 à 16:00 UTC. Même l'off-peak est plus cher que l'ancien flat (+57 % sur le cache-miss Flash). En heures françaises : **peak 3h-6h et 8h-12h, off-peak tout le reste**, dont l'après-midi et la soirée. Par million de tokens, en off-peak : Flash 0,22 $ entrée / 0,66 $ sortie ; Pro 0,66 $ / 1,98 $. Cache-hit à 0,007 $ (Flash) et 0,022 $ (Pro) : le cache est 30 fois moins cher que le miss, la discipline de préfixe paie directement en dollars.

## 4. Les leçons de dsh (ce qu'on transpose, ce qu'on admire)

Le system prompt de production complet de dsh, extrait verbatim du session log d'un run réel (leur log enregistre tout ce que le modèle voit, doctrine « Model-visible means logged », la vraie racine de ton « the model remembers nothing » qui n'existe pas texto dans le repo) :

1. `You are an AI agent powered by DeepSeek Harness.`
2. `You are a coding agent powered by the {{model}} model. Your working directory is {{cwd}}.`
3. Douze paragraphes de guidance outil, un par outil, style : « Use the read tool, not shell commands like cat » ; « Check the [exit code: N] marker on every bash result » ; « do not busy-poll or sleep on a job » ; « Use the workflow tool ONLY when the user explicitly asks ».

Total ~900 tokens. Le reste du comportement vient de mécanismes :

- **Anti-boucle mécanique** : au 3e appel d'outil identique consécutif, injection d'un rappel doux (« Carefully analyze the previous result before calling again... try a different approach »). Aux seuils 5 et 8, rappel détaillé : outil, compteur, arguments cités, « The repeated calls are not making progress ».
- **Résultats d'outils rabotés** : au-delà de 8 192 caractères, un vieux résultat est réduit à 4 096 de tête + 1 024 de queue avant même la compaction. Au-delà de 50 Ko, l'output part sur disque (spill) et le modèle reçoit le chemin. Nuance : Claude Code a DÉJÀ un spill disque natif (« Output too large. Full output saved to: ... », prouvé par le réfutateur de l'insight du 15/08) ; le manque réel côté Claude Code est le rabotage des VIEUX résultats en cours de session.
- **Compaction cache-alignée** : la requête de résumé rejoue la conversation telle quelle et ajoute la directive de compaction comme dernier message user. Elle est donc un préfixe exact de la dernière requête : payée au prix cache-hit. Le checkpoint replanté est du Markdown à sections fixes entre balises, avec « continue sans mentionner ce checkpoint ».
- **Le cache dicte l'architecture** : en plan mode, les outils d'écriture restent listés (le texte du mode dit de les ignorer) pour ne pas changer le catalogue et invalider le cache. Le fork de sous-agent reste one-shot pour préserver le préfixe du parent. Le contexte dynamique (date, cwd, policy sandbox) vit en messages user en queue de contexte, renvoyé seulement s'il a changé.
- **Escalade sandbox outillée** : un refus sandbox se rejoue une seule fois avec `sandbox_permissions` + `justification` en paramètres du même appel bash ; c'est ce retry qui déclenche le prompt d'approbation humain. Pas de détour conversationnel.
- **Instructions projet** : AGENTS.md/CLAUDE.md chargés en messages user durables framés `<system-reminder>` (pattern décrit chez eux comme « familiar », copié de Claude Code), budget dur 64 Ko, dédup par empreinte, le fichier le plus spécifique gagne, `</system-reminder>` échappé dans le contenu (anti-injection).
- **Discipline « Model Experience »** : chaque package du repo doit documenter « What the model sees / Token effect / KV Cache effect », avec un gate CI. L'expérience du modèle est un objet de design revu comme du code.

Transposition honnête : le gros de ces mécanismes appartient au harnais, pas à l'utilisateur. Côté Claude Code on ne peut pas raboter le system prompt de base. Les leviers réellement à notre main : le choix des modèles par tier (fait, section 1), l'effort (fait), la charge de la session (MCP coupés, profil de plugins minimal pour les sessions DeepSeek : chaque token de préambule est repayé à chaque session), et les patterns de prompt (les principes « Model Experience » et la compaction cache-alignée sont des idées à garder pour l'atelier, chantier_gate oblige).

## 5. Les pièges, par gravité

1. **Pas d'images ni de documents via l'endpoint anthropic.** Un agent qui screenshote ou lit un PDF est aveugle. Rédhibitoire pour le travail UI/design ; sans impact pour digests, veille, critique de code.
2. **Hausse tarifaire ce soir 18h** et fenêtres peak le matin (8h-12h). Les gros volumes se planifient l'après-midi, le soir, la nuit avant 3h.
3. **Fallback silencieux** vers Flash sur nom de modèle inconnu. Toujours vérifier `modelUsage`.
4. **Bug tool calls V4-Pro** (issue officielle, endpoint OpenAI, ~11 % en texte brut au lieu du champ structuré). Jamais observé sur nos runs via l'endpoint anthropic, mais nos volumes sont faibles. Si un jour Pro « décrit » un appel d'outil au lieu de l'exécuter, c'est ça.
5. **36k tokens repayés à chaque session neuve** (cache inter-sessions muet). Privilégier les sessions longues aux rafales de sessions courtes ; en headless répété, préférer `--resume`.
6. Divergence mineure : le mapping par défaut de l'endpoint route sonnet vers Flash, mais le guide officiel force sonnet vers Pro. Notre config (section 1) suit le guide.

## 6. Place dans la doctrine erom

La doctrine reste inchangée : les moteurs externes critiquent et rapportent, ils ne produisent pas d'artefacts mergés. Dans ce cadre, DeepSeek V4 dans Claude Code est le moteur externe le moins cher et le mieux intégré du marché :

- **Flash** : digests, synthèses de transcripts, veille, exploration de gros corpus, critique de premier passage. En off-peak avec cache chaud, le coût est de l'ordre de quelques centimes par heure de travail agentique.
- **Pro** : second avis d'architecture, revue adversariale d'un plan, rapport de recherche. Son réflexe d'auto-vérification observé en test est exactement le profil « devil » recherché.
- **dsh lui-même** : à garder comme instrument de mesure (son session log zstd est le meilleur banc d'observation de ce que voit un modèle), pas comme harnais de production ici : developer preview, breaking changes annoncés, et notre outillage vit dans Claude Code.

## 7. Non couvert, incertitudes

- Comportement en très long contexte (>150k) dans Claude Code : non testé (coût en temps, pas en argent).
- Le bug tool calls Pro sur l'endpoint anthropic : pas de volume suffisant pour le quantifier.
- La cause exacte du cache inter-sessions muet : non tranchée.
- Les Agent Notes et postmortems internes du repo dsh : mes deux explorateurs délégués se sont perdus, mais l'insight du 15/08 les avait déjà lus (4 postmortems, système de notes, 11 skills maison), dont la leçon « trust the trace, not the theory ». Le trou est comblé par ce rapport-là ; le repo reste cloné dans `samples/deepseek-harness` pour aller plus loin.
- `CLAUDE_CODE_EFFORT_LEVEL` : la traduction exacte de l'effort Claude Code en `reasoning_effort` DeepSeek côté endpoint n'est documentée nulle part ; le thinking est actif dans tous les cas observés.
