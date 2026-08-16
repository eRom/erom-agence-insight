# Chantier : DeepSeek V4 dans Claude Code, leçons du harnais dsh

Ouvert le 2026-08-16. Session Fable 5, effort max.

## Mission (cadrée par Romain)
PAS un insight or/argent/bronze « dsh vs Claude Code ». L'objectif : améliorer l'efficacité
de DeepSeek V4 Flash/Pro quand ils tournent DANS Claude Code (avec le CLAUDE.md commun
fable/opus/sonnet). Hypothèse de Romain : DeepSeek outille/optimise parfaitement ses
propres modèles dans dsh ; on veut transposer ces réglages.

## Objets d'étude
- Modèles : deepseek-ai/DeepSeek-V4-Flash-0731 et DeepSeek-V4-Pro-0813 (versions exactes !)
- Harnais : https://github.com/deepseek-ai/deepseek-harness (dsh)
- À creuser dans dsh : system instructions, guards, agent notes, rules,
  « The model remembers nothing », compact, loop, workflow, tools, permits, shell,
  sandbox, cache system (Ollama serve), etc.
- Tests pratiques : Claude Code branché sur l'API DeepSeek (clé dans l'env, solde ~2,81 $)
  et/ou dsh en direct. Budget API à ménager mais prix DeepSeek très bas.

## Plan
1. [en cours] Vérifs locales : clé env, solde, ollama, clone dsh dans samples/
2. [en cours] Recherche live : agent « modeles-v4 » (specs/pricing/prompting V4) +
   agent « api-deepseek » (endpoint anthropic-compatible, caching, doc dsh, ollama)
3. [ ] Lecture en profondeur du repo dsh (system prompts, guards, mécanique)
4. [ ] Confrontation : ce que dsh fait pour V4 vs ce que Claude Code + CLAUDE.md erom fait
5. [ ] Tests pratiques budgétés (Claude Code sur API DeepSeek, dsh)
6. [ ] Livrable : rapport + réglages concrets recommandés (env, CLAUDE.md variant, etc.)

## État / découvertes

### Environnement local (vérifié)
- DEEPSEEK_API_KEY présente, solde 2,81 $ (endpoint /user/balance OK).
- dsh DÉJÀ installé : /usr/local/bin/dsh, version 0.1.0-rc.6. ollama 0.32.13.
- Repo cloné dans samples/deepseek-harness (80 Mo, gitignoré).

### dsh, faits durs (source : repo)
- Plugin-based sur Cordis, « everything is a plugin ». Doc bilingue en/zh massive.
- System prompt ASSEMBLÉ par sections ordonnées : identité harnais = 1 ligne
  (« You are an AI agent powered by DeepSeek Harness. », order -100), persona
  deployment order 0 (défaut usine : VIDE), tool guidance 100-199.
- Contexte dynamique (date, cwd...) : PAS dans le system prompt. Injecté en
  messages user « runtime context snapshot » avec supersession explicite,
  réinjecté SEULEMENT si changé. But : préfixe système immuable pour le KV-cache.
- Discipline « Model Experience » : chaque package documente What the model
  sees / Token effect / KV Cache effect (gate CI verify-package-readme-model-experience).
- « The model remembers nothing » : PAS texto dans le repo. Les mécanismes
  correspondants : « Model-visible ⟺ logged » (l'historique modèle est dérivé
  du session log à chaque step) + Ralph loop (rounds fresh-agent sans mémoire,
  état porté par workspace + handoff borné). maxRounds Ralph : 64.
- « ollama » : ZÉRO occurrence dans le repo. Le lien Ollama⇄dsh n'existe pas.
- Adapter DeepSeek (packages/llm/llm-deepseek) : modèles défaut deepseek-v4-flash
  et deepseek-v4-pro, contexte 1 000 000 tokens, maxTokens output 256 000,
  thinking enabled + reasoningEffort high par défaut (off|high|max),
  reasoning passback : reasoning_content resérialisé en historique sur les tours
  AVEC tool calls (exigé par l'API en thinking mode), jeté sinon.
  EMPTY_RESPONSE (stream fini sans contenu) = erreur retryée. Retry backoff
  500ms vers 10s. Titres de session : thinking forcé OFF, 64 tokens max.
- Modèle par défaut du produit : deepseek-v4-flash (bundle/base/cordis.patch.yml:67).
- Défauts notables : maxParallelToolCalls 10, bash timeout 60s, sandbox
  workspace-write + approval ask, spill >50 Ko sur disque, tool-result-pruner
  8192 vers head 4096 + tail 1024, repeat-tool-reminder seuils [3,5,8],
  agent-instructions maxBytes 65536, web fetch DÉSACTIVÉ (SSRF), search via
  API DeepSeek 60s.
- Plan mode : outils de mutation RESTENT listés (stabilité du cache de requête),
  le texte du mode dit de les ignorer. Fork subagent one-shot pour préserver le
  prefix cache du parent. Le cache dicte l'architecture.
- Instructions projet : AGENTS.md/CLAUDE.md + variantes .local, messages
  user-role framés <system-reminder> (« familiar pattern », copié de Claude
  Code), dédup SHA-1, budget dur, anti-injection (</system-reminder> échappé).
- dsh embarque des subagent providers Claude Code et Codex (dormants) : leur
  harnais peut déléguer à Claude Code.

### Tests pratiques Claude Code sur API DeepSeek (vérifié aujourd'hui)
- Endpoint anthropic-compatible CONFIRMÉ : https://api.deepseek.com/anthropic
  (/v1/messages, x-api-key, renvoie blocs thinking signés + cache accounting).
- Branchement : ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
  ANTHROPIC_API_KEY=$DEEPSEEK_API_KEY, --model deepseek-v4-flash.
  claude -p headless : FONCTIONNE (réponse correcte, 2s).
- Poids du harnais : 36 034 tokens d'input pour un « 2+3 » (system prompt CC
  + tools + CLAUDE.md user). À chaque session neuve : repayé.
- Claude Code affiche contextWindow 200 000 pour ce modèle inconnu (réel : 1M)
  donc compaction 5x trop tôt. Piste : CLAUDE_CODE_CONTEXT_WINDOW ?
- Coût affiché par CC (0,18 $) : FAUX (grille interne). Solde réel DeepSeek
  inchangé (2,81) après ~110k tokens : prix Flash dérisoire.
- Tool calling : OK (Write exécuté proprement, 2 turns, 0 denial). Réponse en
  français : CLAUDE.md user respecté par V4 Flash.
- Cache : inter-sessions = 0 (36k repayés) ; intra-session = OK (step 2 :
  cache_read 36 224). Hypothèses inter-sessions : metadata.user_id de CC dans
  le body ? cache best-effort côté serveur ? À creuser si important.
- thinking_tokens: 0 est un artefact d'affichage : les transcripts headless
  contiennent bien des blocs thinking dans TOUS les runs (vérifié par grep).
  Le thinking V4 est actif par défaut via l'endpoint anthropic.

### Rapport agent api-deepseek (sources primaires vérifiées, 2026-08-16)
- HAUSSE TARIFAIRE DeepSeek le 2026-08-16 à 16:00 UTC (18h CEST) : passage
  peak/off-peak. Peak = 01-04 UTC et 06-10 UTC ; off-peak = moitié du peak.
  Flash : cache-hit 0.007/0.014, cache-miss 0.22/0.44, output 0.66/1.32 $/M
  (off-peak/peak). Pro : 0.022/0.044, 0.66/1.32, output 1.98/3.96 $/M.
  Ancien flat : Flash 0.0028/0.14/0.28 ; Pro 0.003625/0.435/0.87.
  Off-peak pour Romain : 12h-03h CEST + 06h-08h CEST (le soir français est
  off-peak, bien).
- Guide officiel DeepSeek pour Claude Code
  (api-docs.deepseek.com/quick_start/agent_integrations/claude_code) :
  ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN + ANTHROPIC_MODEL=deepseek-v4-pro
  + ANTHROPIC_DEFAULT_OPUS/SONNET_MODEL=deepseek-v4-pro
  + ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
  + CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
  + CLAUDE_CODE_EFFORT_LEVEL=max + CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432.
  Doctrine DeepSeek : Pro au volant, Flash pour les subagents, effort max.
- Endpoint anthropic : thinking supporté mais budget_tokens IGNORÉ (on/off
  seulement) ; cache_control ignoré (le cache par préfixe automatique
  s'applique quand même, confirmé par nos mesures intra-session) ;
  anthropic-beta/version ignorés ; PAS d'images ni de documents (pas de
  vision !) ; top_k ignoré.
- Fallback SILENCIEUX vers deepseek-v4-flash si nom de modèle inconnu :
  toujours vérifier modelUsage dans la sortie.
- Bug connu V4-Pro (issue GitHub DeepSeek-V3#1244, ouverte) : ~11 % de tool
  calls émis en texte brut dans content (finish stop) sur endpoint OpenAI.
  Pas de rapport équivalent sur l'endpoint anthropic. À surveiller.
- Ollama : V4 uniquement en tags :cloud (Flash 304B params, Pro 1.65T/49B
  actifs, MoE). AUCUN poids local. Le « cache Ollama » du brief était une
  fausse piste, close.
- Méfiance sources : nuée de sites satellites fabriquant de fausses URLs sur
  ce sujet (liste dans le rapport agent). Perplexity a inventé 2 sources.

### Duel Flash vs Pro (tâche code réelle, Claude Code, 2026-08-16 matin)
Tâche : script bun stats.ts + CSV + exécution + correction. Les deux : 4 turns,
19 s, réussite du premier coup, français respecté, cache intra-session ~75k lus.
- Flash : output 1 946 tokens, réponse correcte, un peu bavard.
- Pro : output 1 345 tokens, ET auto-vérification spontanée des résultats
  (tri, somme, médiane recalculés à la main). Qualité de comportement au-dessus.
- modelUsage confirme le bon modèle servi dans chaque run (pas de fallback).
- contextWindow affiché reste 200000 avec ou sans CLAUDE_CODE_AUTO_COMPACT_WINDOW
  ou CLAUDE_CODE_CONTEXT_WINDOW : champ d'affichage figé. Effet réel du seuil
  auto-compact : question posée à l'agent claude-code-guide.

### Rapport agent modeles-v4 (sources primaires, 2026-08-16)
Rapport complet : docs/veille-deepseek-v4-flash-pro-2026-08.md
- deepseek-chat et deepseek-reasoner RETIRÉS depuis le 2026-07-24. Noms API
  stables : deepseek-v4-flash / deepseek-v4-pro ; les checkpoints glissent
  dessous (aujourd'hui Flash-0731 et Pro-0813, GA du 13/08).
- Architecture : Flash 284B total / 13B actifs / 43 couches / 256 experts ;
  Pro 1.6T / 49B actifs / 61 couches / 384 experts. Contexte 1M (YaRN x16).
  Sortie max 384K en effort high/max. Licence MIT. FP4+FP8.
- Effort officiel : low / high / max (changelog 13/08) + disabled.
- Prompting officiel : température 1.0, top_p 0.95 en agentique (model card
  Pro-0813). Pas de guide de prompting structuré officiel (le « 4 blocs » qui
  circule est communautaire, non officiel).
- Contexte long : rétention stable ~128K puis dégradation progressive vers 1M
  (arXiv 2606.19348). Le 1M est utilisable, pas magique.
- Benchmarks OFFICIELS : Terminal-Bench 2.1 Flash 82.7 / Pro 87.9 ;
  DSBench-Hard 59.6 / 67.2 ; Toolathlon 70.3 / 74.1. AUCUN SWE-bench Verified
  officiel (les ~79-80 % qui circulent : blogs tiers contradictoires, dont un
  du réseau spam).
- Thinking + tools : format interne DSML, reasoning clos avant tool call.
  reasoning_content à rejouer en multi-tour (des 400 sinon, secondaire) ;
  nos tests multi-tours via endpoint anthropic : aucun 400 (géré côté serveur
  via les blocs thinking signés que Claude Code renvoie nativement).
- Strict mode tools : base_url /beta + strict: true (validation serveur).
- Réseau de sites spam SEO sur ce sujet : liste dans le rapport, à écarter.

### Rapport agent cc-guide (doc Claude Code, fiabilité mixte, 2026-08-16)
- Variables confirmées en 2.1.x (doc env-vars officielle) :
  ANTHROPIC_DEFAULT_OPUS/SONNET/HAIKU/FABLE_MODEL (aliases),
  CLAUDE_CODE_SUBAGENT_MODEL (modèle des subagents, surcharge frontmatter),
  ANTHROPIC_SMALL_FAST_MODEL (tâches background).
- CLAUDE_CODE_AUTO_COMPACT_WINDOW : seuil auto-compact en tokens, effectif =
  min(variable, fenêtre modèle). Sources faibles (repo tiers) pour la formule.
- Modèle inconnu via BASE_URL custom : plafond 200k interne, PAS de moyen
  officiel de déclarer une fenêtre custom (pas de CLAUDE_CODE_CONTEXT_WINDOW).
- MAX_THINKING_TOKENS : selon cc-guide, pas documentée en 2.1.x ; de toute
  façon l'endpoint DeepSeek ignore budget_tokens (on/off seulement).
- LECTURE PRATIQUE : le plafond 200k de CC tombe dans la zone de rétention
  stable de V4 (~128k puis déclin). La « limitation » est bénigne en vrai.
  Mettre AUTO_COMPACT_WINDOW=786432 (reco DeepSeek) : inoffensif, aligné doc.

### Run dsh headless + autopsie du session log (2026-08-16 matin)
- Même tâche stats.ts dans dsh headless : 11,6 s (vs 19 s Claude Code),
  réussite premier coup, auto-vérification spontanée (sur Flash).
- Romain avait déjà onboardé dsh le 2026-08-13 : ~/.dsh/settings.yaml
  contient reasoningEffort: max, preset default code, + skill hyperframes.
- Session logs dsh : ~/.dsh/sessions/<slug-cwd>/session-<uuid>/session.jsonl.zstd
  (zstdcat pour lire). Copie décompressée du run :
  scratchpad/dsh-session.jsonl.
- SYSTEM PROMPT VERBATIM dsh (~900 tokens) : identité 1 ligne + persona
  1 ligne + ~12 paragraphes de tool guidance (read pas cat, glob pas find,
  grep pas rg shell, exit codes, jobs sans busy-poll, web_search avec
  citations, goals, workflow/ralph SEULEMENT sur demande explicite,
  subagents background par défaut). Aucune autre prose.
- request/header : reasoningEffort max, maxTokens 256000.
  request/context : contextWindow 1000000 (la vraie fenêtre, déclarée).
- Escalade sandbox = PARAMÈTRE de l'outil bash (sandbox_permissions +
  justification, une fois, seulement après refus réel) : le retry outillé
  déclenche le prompt d'approbation humain. Pas de détour conversationnel.
- Ordre de requête : system → historique → prompt user → runtime snapshot
  (file policy + approval policy déclarées au modèle) → catalogue skills en
  <system-reminder>. Dynamique en queue, resend seulement si changé.

## Pièges connus
- Freshness : cutoff 2026-01, V4 et dsh sont post-cutoff → tout vérifier en live.
- Ne pas cramer le solde : ~2,81 $. Vérifier pricing avant gros tests.
- samples/ est gitignoré (commit 203dec9), le clone dsh y vit.
