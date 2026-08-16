# Veille technique - DeepSeek V4 Flash-0731 & V4 Pro-0813

État au 16/08/2026. Sources primaires citées systématiquement ; toute affirmation issue de blogs tiers/agrégateurs est marquée **[secondaire]**.

## Résumé exécutif

- Les deux checkpoints existent bel et bien sous ces noms exacts : `deepseek-ai/DeepSeek-V4-Flash-0731` (31/07/2026) et `deepseek-ai/DeepSeek-V4-Pro-0813` (13/08/2026, GA de la branche Pro qui était en preview).
- **`deepseek-chat` et `deepseek-reasoner` sont morts.** Retirés le 24/07/2026 15:59 UTC (annoncé le 24/04/2026, donc préavis de 3 mois). Utiliser `deepseek-v4-flash` / `deepseek-v4-pro`.
- **Le pricing change aujourd'hui même** (16/08/2026, 16:00 UTC) : passage à une grille peak/off-peak. Même l'off-peak est plus cher que l'ancien tarif flat (~+57% sur le cache-miss Flash). Vérifier tout devis fait avant cette date.
- Tool calling : compatible OpenAI **et** compatible Anthropic Messages API nativement (`https://api.deepseek.com/anthropic`), donc branchable sur Claude Code sans adaptateur, juste en changeant `ANTHROPIC_BASE_URL`. Mais sur cet endpoint, **images et documents ne sont pas supportés** : blocage silencieux pour un agent qui screenshote.
- **dsh existe vraiment** : `DeepSeek Harness` officiel, https://github.com/deepseek-ai/deepseek-harness, developer preview, 120k stars, `npx @deepseek-ai/dsh web`. Providers LLM natifs limités à deepseek/pi-ai/replay, pas de retour d'usage communautaire daté (trop récent).
- DeepSeek ne publie **aucun** score SWE-bench Verified / tau-bench officiel pour V4. Les chiffres ~79-80% qui circulent viennent de blogs tiers et se contredisent entre eux (73,7 à 80,6% selon la source), l'un d'eux (`benchlm.ai`) fait partie d'un écosystème de sites spam détecté sur ce sujet précis (voir note méthodologique) : à ne pas utiliser sans re-confirmation.
- Retours de terrain sur l'usage en harnais agentique (Claude Code, Cline) : le modèle est solide sur le fond, mais les intégrations non natives cassent facilement sur la gestion du `reasoning_content` et du streaming des tool calls ; un bug tool-calling quantifié (~11%, GitHub issue officielle) émet parfois l'appel en texte brut plutôt qu'en champ structuré.

---

## Note méthodologique : écosystème de spam SEO sur ce sujet précis

Constat fait pendant cette recherche (et recoupé avec un autre passage de recherche indépendant sur le même sujet dans la même fenêtre) : le mot-clé "DeepSeek V4" / "dsh" génère actuellement un volume anormal de sites satellites qui se citent entre eux, avec des noms plausibles (`deepseekai.guide`, `chat-deep.ai`, `deepseekv4pro.com`, `deepseekv4.network`, `benchlm.ai`, `costgoat.com`, `verdent.ai`, `deepseekdocs.com`, `dshdocs.com`, `open-harness.net`, `deepseekagent.io`, et d'autres). Perplexity search les cite parfois comme des sources faisant autorité, y compris pour des chiffres qui se contredisent d'un site à l'autre. Dans ce rapport, tout chiffre dont la seule source est un domaine de cette liste est marqué **[secondaire, faible confiance]** plutôt que présenté comme fait. Les affirmations non marquées reposent sur un fetch direct de `api-docs.deepseek.com`, `huggingface.co/deepseek-ai/*`, `github.com/deepseek-ai/*`, ou `arxiv.org`.

---

## 1. Versions et checkpoints

### Checkpoints publiés
| Checkpoint | Date | Statut |
|---|---|---|
| `deepseek-ai/DeepSeek-V4-Flash-0731` | 31/07/2026 | GA, re-post-training agentique de la preview d'avril 2026, même architecture |
| `deepseek-ai/DeepSeek-V4-Pro-0813` | 13/08/2026 | GA, "supersedes the preview version", sort la branche Pro de la preview |
| `deepseek-ai/DeepSeek-V4-Pro` (sans suffixe) | - | Fiche famille versionless, décrit les 3 variantes (Flash / Pro-Base / Pro) architecturalement, pas un checkpoint daté |

Sources primaires : HF `deepseek-ai/DeepSeek-V4-Pro-0813` (https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813), HF `deepseek-ai/DeepSeek-V4-Pro` (https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro), changelog officiel (https://api-docs.deepseek.com/updates/), annonce GA Pro (https://api-docs.deepseek.com/news/news260813).

### Alias API et migration
Confirmé par fetch direct de l'annonce officielle de dépréciation (https://api-docs.deepseek.com/news/news260424) :

- `deepseek-chat` et `deepseek-reasoner` **retirés et inaccessibles depuis le 24/07/2026 15:59 UTC**.
- Pendant la période de transition, les deux alias routaient vers **`deepseek-v4-flash`** (mode non-thinking pour `deepseek-chat`, mode thinking pour `deepseek-reasoner`), donc jamais vers Pro, même avant retrait.
- Migration : garder le même `base_url`, changer juste `model` vers `deepseek-v4-pro` ou `deepseek-v4-flash`.
- Ces deux noms d'alias API (`deepseek-v4-flash`, `deepseek-v4-pro`) sont stables dans le temps ; c'est le checkpoint réel derrière qui évolue à chaque release (0731 pour Flash aujourd'hui, 0813 pour Pro aujourd'hui, remplacera silencieusement en cas de future release).

### Flash vs Pro : comparatif architecture

| | V4-Flash-0731 | V4-Pro-0813 |
|---|---|---|
| Total params (annoncé famille) | 284B | 1.6T |
| Params activés/token | 13B | 49B |
| Params listés sur HF (avec module DSpark attaché) | 304B | ~1.7T |
| Couches (`num_hidden_layers`) | 43 | 61 |
| `hidden_size` | 4096 | 7168 |
| `num_attention_heads` | 64 | 128 |
| `num_key_value_heads` | 1 | 1 |
| Experts routés | 256 | 384 |
| Experts actifs/token | 6 | 6 |
| `moe_intermediate_size` | 2048 | 3072 |
| Contexte natif | 1M tokens | 1M tokens (YaRN, `rope_scaling factor=16` confirmé config.json) |
| Précision | FP4+FP8 mixte | FP4+FP8 mixte (config top-level montre FP8 e4m3 dynamique pour attention/non-MoE, cohérent avec le pattern Flash) |
| Sortie max (effort high/max) | 384K tokens | 384K tokens |
| Licence | MIT | MIT |

Écart HF-listé vs annoncé (304B vs 284B pour Flash, ~1.7T vs 1.6T pour Pro) : même explication documentée pour Flash dans notre veille précédente, le repo HF inclut le module de spéculative decoding DSpark attaché, gonflant le compte de paramètres. Pas re-vérifié explicitement pour Pro mais le pattern est identique, donc traité comme la même cause probable plutôt que confirmé au mot près.

Sources primaires : config.json brut Pro-0813 (https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813/raw/main/config.json), fiche famille (https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro), config.json Flash déjà vérifié en veille précédente.

### Reasoning / thinking mode
- Les deux modèles supportent 3 niveaux d'effort : **low / high / max**, confirmé par le changelog officiel du 13/08 : *"Thinking modes of V4-Pro and V4-Flash now support three thinking effort levels."*
- Support natif de l'**OpenAI Responses API**, "adapté pour Codex" (one-click setup), pour les deux modèles, annoncé dans le même changelog du 13/08.

---

## 2. Pricing API officiel (vérifié par fetch direct de api-docs.deepseek.com/quick_start/pricing)

### Tarif actuel (jusqu'au 16/08/2026 16:00 UTC)
| Modèle | Input cache hit | Input cache miss | Output | (par 1M tokens, USD) |
|---|---|---|---|---|
| deepseek-v4-flash | $0.0028 | $0.14 | $0.28 | |
| deepseek-v4-pro | $0.003625 | $0.435 | $0.87 | |

### Nouveau tarif peak/off-peak, effectif **aujourd'hui 16/08/2026 16:00 UTC**
| Modèle | Période | Cache hit | Cache miss | Output |
|---|---|---|---|---|
| deepseek-v4-flash | Off-peak | $0.007 | $0.22 | $0.66 |
| deepseek-v4-flash | Peak | $0.014 | $0.44 | $1.32 |
| deepseek-v4-pro | Off-peak | $0.022 | $0.66 | $1.98 |
| deepseek-v4-pro | Peak | $0.044 | $1.32 | $3.96 |

Off-peak = exactement 50% du tarif peak (confirmé texte officiel : *"off-peak prices set at half of the peak-hour prices"*). Fenêtres peak citées par une source secondaire concordante mais pas re-vérifiées sur la page officielle elle-même : 01:00-04:00 et 06:00-10:00 UTC **[à confirmer directement sur la doc au moment de facturer]**.

**Point à signaler à l'équipe** : même l'off-peak est plus cher que l'ancien flat rate. Flash cache-miss passe de $0.14 à $0.22 off-peak (+57%), $0.44 en peak (+214%). Ce n'est pas une baisse de prix malgré la présentation "off-peak = moitié prix", c'est une hausse généralisée avec une fenêtre moins chère.

### Tiers (secondaire, non vérifié par fetch direct)
Together AI et Fireworks pratiquent des tarifs plus élevés que l'API officielle et n'exposent pas la distinction cache-hit/cache-miss (un seul tarif input/output). OpenRouter n'a pas de route DeepSeek V4 native identifiée dans mes sources. Ces chiffres tiers n'ont pas été vérifiés par fetch direct des pricing pages respectives, à re-vérifier avant tout arbitrage de coût qui en dépendrait.

Source primaire : https://api-docs.deepseek.com/quick_start/pricing (fetch direct), https://api-docs.deepseek.com/news/news260813.

### Context caching (mécanique du cache-hit ci-dessus)
Confirmé par une recherche parallèle sur le même sujet, source primaire https://api-docs.deepseek.com/guides/kv_cache/ : le caching est **automatique, aucun code requis**. Granularité par unités de préfixe (pas de taille de bloc fixe) : créées aux limites de requêtes, aux préfixes communs détectés, et à intervalles de tokens fixes pour les contenus longs. Durée de vie du cache formulée vaguement côté doc officielle ("quelques heures à quelques jours" selon usage), pas de garantie chiffrée. Sur l'endpoint Anthropic-compatible, le paramètre `cache_control` (breakpoints explicites façon Anthropic) est ignoré, mais le caching automatique par préfixe de DeepSeek continue de s'appliquer en arrière-plan indépendamment (déduction logique, pas une phrase officielle qui le confirme mot pour mot).

---

## 3. Tool calling

### Format et compatibilité (vérifié par fetch direct de api-docs.deepseek.com/guides/tool_calls)
- **OpenAI-compatible** : `POST /chat/completions`, tools définis en JSON Schema standard (`type: "function"`, `function.name/description/parameters`), retour dans `message.tool_calls`.
- **Anthropic Messages API également supportée nativement**, confirmé par fetch direct de deux pages officielles distinctes (https://api-docs.deepseek.com/guides/anthropic_api/ et https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/) :
  - `base_url = https://api.deepseek.com/anthropic`, endpoint `POST /v1/messages`.
  - Doc officielle Claude Code : *"Claude Code, GitHub Copilot, or OpenCode, you can use DeepSeek as the backend model directly, no code required."*
  - Pour brancher Claude Code : `export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, garder son client Anthropic tel quel, utiliser `deepseek-v4-flash` ou `deepseek-v4-pro` comme nom de modèle.
  - C'est un vrai second format natif (pas un simple proxy communautaire), point notable pour toute intégration Claude Code / harnais Anthropic-first.

**Détail issu d'une recherche parallèle sur le même sujet (primaire, mêmes pages officielles)** : le guide Claude Code recommande un jeu d'env vars plus riche que le simple base_url : `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL=deepseek-v4-pro`, `ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro`, `ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro`, `ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash`, `CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash`, `CLAUDE_CODE_EFFORT_LEVEL=max`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432`. Point à noter : ceci force Sonnet vers **Pro** (pas Flash), alors que le mapping *par défaut* de l'endpoint (sans ces overrides) route `claude-sonnet*`/`claude-haiku*` vers Flash et seulement `claude-opus*` vers Pro. Les deux pages officielles divergent sur ce point, ce n'est pas une erreur, juste deux stratégies de mapping différentes selon qu'on utilise le guide Claude Code dédié ou l'endpoint générique.

**Matrice de compatibilité de l'endpoint Anthropic** (primaire, page `guides/anthropic_api/`) : `thinking` supporté mais `budget_tokens` ignoré ; `tool_use` entièrement supporté ; `stop_sequences`/`stream`/`system`/`temperature`/`top_p`/`max_tokens` supportés ; headers `anthropic-beta` et `anthropic-version` ignorés ; `mcp_servers`, `container`, `cache_control`, `top_k` ignorés. **Point d'attention majeur non documenté dans ma première passe : images et documents ne sont PAS supportés** sur cet endpoint. Pour un agent Claude Code qui screenshote ou lit des PDF, c'est un blocage silencieux à anticiper, pas juste une limitation mineure.

### Strict mode
- Nécessite `base_url = https://api.deepseek.com/beta` + `strict: true` sur chaque fonction.
- Validation JSON Schema côté serveur ; toute violation ou feature JSON Schema non supportée renvoie une erreur avant exécution.
- Contrainte notée : en strict mode, toutes les propriétés d'objet doivent être `required` et `additionalProperties: false`.
- Types JSON Schema supportés : object, string, number, integer, boolean, array, enum, anyOf, $ref, $def.

### Ce qui N'EST PAS confirmé officiellement (important, contredit ce que disent les blogs tiers)
La doc officielle `guides/tool_calls` **ne documente explicitement ni `tool_choice` ni le nombre de tool calls parallèles supportés**, vérifié par lecture directe de la page. Des guides tiers **[secondaire]** (macaron.im, floatboat.ai) avancent des chiffres précis (128 tools définissables, 128 tool calls parallèles par tour) et un comportement `tool_choice` façon OpenAI (auto/force/none), plausible par analogie avec la compatibilité OpenAI générale, mais **non retrouvé dans la documentation officielle elle-même**. À vérifier empiriquement avant de s'appuyer dessus pour un design d'agent.

### Quirks connus
- **Thinking mode + tool calls** : en interne le modèle utilise un format DSML (`<｜DSML｜tool_calls>`, `<｜DSML｜invoke>`), et le raisonnement doit être intégralement clos dans `<think>...</think>` avant tout tool call, source primaire : README d'encodage du HF model card Pro (https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/encoding/README.md). Sur l'API OpenAI-compatible standard, ce détail interne n'est normalement pas exposé tel quel, mais explique pourquoi le modèle peut sembler verbeux avant d'émettre l'appel d'outil effectif.
- **Tool calls émis en texte brut au lieu du champ structuré, taux mesuré** : issue GitHub officielle non résolue, https://github.com/deepseek-ai/DeepSeek-V3/issues/1244, ~11% des complétions sur un échantillon de 19 (donc échantillon faible, mais c'est un ticket du tracker officiel du repo, pas un blog) renvoient `finish_reason: stop` avec l'appel d'outil en texte libre dans `content`, au lieu de `finish_reason: tool_calls` avec le champ structuré. Non confirmé si ce comportement touche spécifiquement l'endpoint Anthropic ou seulement l'OpenAI-compatible. Implication pratique : un harnais qui ne parse QUE `tool_calls` et ignore `content` en cas de `finish_reason: stop` peut silencieusement rater un appel d'outil.
- **Streaming cassé sur passerelles non natives** : un thread du forum développeur NVIDIA (https://forums.developer.nvidia.com/t/deepseek-v4-pro-v4-flash-on-nvidia-nim-streaming-tool-calls-do-not-continue-in-claude-code-anthropic-compatible-agent-workflow/368085) documente un cas précis où, via NIM avec un pont Anthropic-compatible custom, les tool calls streamés ne relancent pas la conversation vers le résultat d'outil, la session reste bloquée après l'appel. Cause suspectée : mauvaise conversion du format DSML vers `tool_calls` standard, ou mauvais typage de `tool_calls[].function.arguments` (doit être une string JSON, pas un objet). **Ce bug concerne un pont tiers (NIM), pas l'endpoint Anthropic officiel de DeepSeek testé ci-dessus**, mais il illustre la classe de bug à surveiller sur toute passerelle maison.
- **`reasoning_content` doit survivre intégralement au multi-tour** : un billet détaillé **[secondaire, cnblogs.com]** sur l'intégration Claude Code CLI et DeepSeek V4 rapporte des erreurs HTTP 400 répétées quand une session mélange plusieurs vendeurs ou perd le champ `reasoning_content` entre deux tours. Recommandation : ne pas mélanger vendeurs dans une même session, réinitialiser la conversation après une 400, ou désactiver le thinking mode si le pont ne préserve pas `reasoning_content` correctement.
- **Historique de boucles sur function calling** : un post communautaire n8n (2025, modèle `deepseek-chat` pré-V4) documente des boucles d'appels d'outils ou réponses vides, avec DeepSeek reconnaissant le bug à l'époque. **Daté et sur un modèle antérieur à V4**, à traiter comme un signal de vigilance générique (mettre un garde-fou anti-boucle côté harnais), pas comme un bug confirmé sur V4.

---

## 4. Recommandations officielles de prompting

**Constat important : aucun "guide de prompting" officiel structuré équivalent à ceux d'Anthropic/OpenAI n'a été localisé chez DeepSeek dans cette recherche.** Ce qui suit distingue ce qui est réellement officiel de ce qui vient de wikis communautaires.

### Confirmé officiel (HF model card Pro-0813, fetch direct)
- **Température** : 1.0
- **top_p** : **0.95 en usage agentique, 1.0 sinon**, cette distinction figure explicitement sur la model card et recoupe notre veille précédente sur Flash (même recommandation). Une source secondaire (deepwiki communautaire) affirme au contraire "toujours 1.0/1.0, ne jamais baisser" ; je retiens la version de la model card officielle comme prioritaire sur ce point précis.
- **Longueur de sortie** : prévoir `max_tokens` large (jusqu'à 384K) en mode thinking effort high/max, sous peine de troncature du raisonnement ou de la réponse finale.
- Existence d'un guide officiel dédié aux agents de code : https://api-docs.deepseek.com/guides/coding_agents/ (référencé mais pas entièrement extrait dans cette passe, à consulter directement si un système prompt de coding agent est en cours de conception).

### Contexte long / "context rot"
- Le papier arXiv (2606.19348, https://arxiv.org/abs/2606.19348) et des benchmarks indépendants de rétention (MRCR, needle-in-haystack) convergent sur : **rétention stable jusqu'à ~128K tokens, dégradation progressive au-delà, mais performance encore significative à 1M**. Pas de chiffre officiel DeepSeek retrouvé au-delà de cette source secondaire d'interprétation du papier.
- **Aucune déclaration officielle DeepSeek trouvée** affirmant une dégradation spécifique de l'instruction-following sur de très longs system prompts, ni de différence documentée Flash vs Pro sur ce point précis. L'inférence raisonnable (Pro = modèle plus gros = probablement plus robuste sur instructions denses) n'est **pas** une affirmation officielle testée, à ne pas présenter comme un fait établi.

### Structure de system prompt (communautaire, PAS officiel, à ne pas relayer comme "le guide DeepSeek")
Un wiki communautaire (deepwiki.com/noya21th/awesome-deepseek-v4) propose un pattern en 4 blocs (Role / Goal / Format / Constraints) + un bloc Reference (schémas d'outils, exemples) + bloc Task, avec recommandation de garder le system prompt stable/réutilisable pour bénéficier du cache. C'est plausible et cohérent avec les bonnes pratiques générales de prompt caching, mais **ce n'est pas une publication officielle DeepSeek**, je le mentionne comme piste méthodologique, pas comme recommandation sourcée.

---

## 5. Benchmarks agentiques

### Officiels (HF model cards + changelog api-docs.deepseek.com, primaire)

| Benchmark | V4-Flash-0731 | V4-Pro-0813 |
|---|---|---|
| Terminal-Bench 2.1 | 82.7 | **87.9** |
| DSBench-FullStack | 68.7 | **71.1** |
| DSBench-Hard | 59.6 | **67.2** |
| Toolathlon-Verified | 70.3 | **74.1** |
| HLE | non publié dans mes sources | 42.7 / 60.0 (deux chiffres, probablement deux réglages d'effort ou deux protocoles, non désambiguïsé dans les sources retrouvées) |
| NL2Repo | 54.2 | non retrouvé pour Pro-0813 dans cette passe |
| Cybergym | 76.7 | non retrouvé pour Pro-0813 dans cette passe |
| DeepSWE | 54.4 | non retrouvé |
| Agents' Last Exam | 25.2 | non retrouvé |
| AutomationBench Public | 25.1 | non retrouvé |

Pro-0813 devance Flash-0731 sur les 4 métriques où les deux sont publiées (+5.2 à +7.6 points). La page d'annonce officielle (https://api-docs.deepseek.com/news/news260813) contient un tableau de benchmarks complet mais rendu en image, non extractible en texte par fetch, se référer à la page directement pour le tableau intégral.

**DeepSeek ne publie ni SWE-bench Verified, ni tau-bench/tau2-bench, ni Aider Polyglot, ni LiveCodeBench officiellement pour V4**, confirmé par deux passes de recherche indépendantes (celle-ci et la veille précédente sur Flash).

### Chiffres tiers non officiels, à traiter avec scepticisme
Plusieurs blogs d'agrégation **[secondaire, faible confiance]** (morphllm.com, benchlm.ai, dev.to, codingfleet.com) citent des scores SWE-bench Verified :
- "V4-Pro-Max" ≈ 80.6%, "V4-Flash-Max" ≈ 79.0% sur des leaderboards indépendants agrégés.
- Une des mêmes sources cite en parallèle un chiffre de 73.7% pour Flash "issu du rapport technique DeepSeek lui-même", contradiction non résolue entre 79.0 et 73.7 pour le même modèle selon la source.
- Le suffixe "-Max" dans ces noms n'est probablement pas un checkpoint distinct mais fait référence au réglage `reasoning_effort=max` documenté officiellement, hypothèse raisonnable, non confirmée explicitement par ces sources.
- Aucun score tau-bench/tau2-bench trouvé nulle part pour V4, officiel ou tiers.
- **`benchlm.ai` est un des domaines identifiés dans la note méthodologique en tête de ce rapport comme faisant partie d'un écosystème de sites qui se citent entre eux sans ancrage primaire vérifié sur le sujet DeepSeek/dsh.** Ça ne prouve pas que ce chiffre précis est faux, mais ça déclasse ce point de "à vérifier" à "à ne pas utiliser sans re-confirmation indépendante".

**Recommandation** : ne pas citer ces 79-80% comme des faits établis dans un document destiné à une décision. Si un score SWE-bench Verified est nécessaire pour arbitrer, le faire tourner soi-même ou attendre une entrée sur le leaderboard officiel SWE-bench (https://www.swebench.com/) plutôt que de relayer des blogs.

### Comparatif face aux frontières fermées
Seule comparaison retrouvée avec des sources tant soit peu traçables (veille précédente) : Claude Opus 4.8 devant V4-Flash sur Terminal-Bench (85.0 vs 82.7), NL2Repo (69.7 vs 54.2), Cybergym (83.1 vs 76.7), quasi à égalité sur Agents' Last Exam (25.7 vs 25.2). **Aucune comparaison retrouvée face à Opus 5, Sonnet 5, GPT-5.x ou Gemini 3.x pour Flash-0731 ou Pro-0813**, absence à signaler, pas à combler par extrapolation.

---

## 6. Retours de terrain en harnais agentique

### Ce qui marche
- Rapport r/LocalLLaMA sur Flash : ~100 tool calls sur un gros changement de code multi-fichiers "sans une seule erreur", gestion de contexte et traces de raisonnement jugées solides (anecdotique, un seul témoignage, mais précis et vérifiable dans son détail).
- Doc officielle confirme un usage "sans code" de DeepSeek comme backend dans Claude Code, GitHub Copilot et OpenCode via changement de `base_url` uniquement (section 3 ci-dessus).

### Ce qui casse
- **Claude Code / passerelles Anthropic-compatibles maison** : 400 errors si `reasoning_content` n'est pas rejoué à l'identique entre les tours, ou si on mélange vendeurs dans une session **[secondaire, détaillé mais non officiel]**. Sur des passerelles tierces (NIM), tool calls streamés qui ne relancent pas vers le résultat, bug documenté sur le forum NVIDIA, spécifique à ce pont, pas reproduit sur l'endpoint Anthropic officiel DeepSeek dans mes sources.
- **Cline** : plainte communautaire explicite (r/DeepSeek, titre "Searching for a stable coding agent for DeepSeek V4 Flash after a frustrating time with Cline"), instabilité rapportée par au moins un utilisateur, contournement suggéré = utiliser le CLI/web direct plutôt que le routing plugin de Cline.
- **opencode** : aucun retour d'expérience spécifique et daté retrouvé sur DeepSeek V4 dans ce harnais précis lors de cette recherche, lacune à signaler plutôt qu'à combler.
- **dsh existe réellement, ce n'est pas qu'une mention de protocole d'éval** : `dsh` = **DeepSeek Harness**, le harnais agentique officiel de DeepSeek, https://github.com/deepseek-ai/deepseek-harness. Confirmé par fetch direct du repo (120 000 stars, licence MIT, 12 300+ commits) : statut **developer preview** explicite, avec l'avertissement du repo lui-même *"THERE WILL BE COMPATIBILITY-BREAKING CHANGES"*. Architecture "Agent = Model + Harness" sur un noyau nommé Cordis, doctrine "Everything is a plugin" (modèles, outils, sessions, sandbox, storage, UI tous swappables). Installation rapide : `npx @deepseek-ai/dsh web` (UI sur `127.0.0.1:3080`). **Limite importante pour un choix d'architecture** : les seuls providers LLM natifs documentés sont `llm-deepseek`, `llm-pi-ai`, `llm-replay` (test), donc pas de provider Ollama ni générique OpenAI-compat prêt à l'emploi listé dans la doc à ce stade (le système de plugins permettrait en théorie d'en écrire un). Package `guard/` dédié "loop-hygiene + tool-timeout plugins", pertinent si le garde-fou anti-boucle de la section 3 doit être outillé. Pas de retour d'expérience communautaire daté trouvé sur dsh en usage réel (cohérent avec son statut très récent de developer preview), seulement sa documentation propre.
- **Historique de boucles sur les tool calls** : signal ancien (n8n, modèle pré-V4) mentionné en section 3, à traiter comme un rappel de garde-fou générique plutôt qu'un bug confirmé sur V4.

### Différences comportementales Flash vs Pro documentées
Rien d'officiel au-delà de : Pro = plus gros, plus lent probablement (non chiffré dans mes sources), meilleur sur les 4 benchmarks agentiques comparables (section 5), tarif ~3x plus cher (section 2). Aucune différence de robustesse ou de style de raisonnement documentée officiellement entre les deux tailles.

---

## Sources primaires consolidées
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813 (model card)
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813/raw/main/config.json
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro (fiche famille)
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/encoding/README.md
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 (veille précédente)
- https://api-docs.deepseek.com/quick_start/pricing
- https://api-docs.deepseek.com/guides/tool_calls
- https://api-docs.deepseek.com/guides/anthropic_api/
- https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/
- https://api-docs.deepseek.com/guides/coding_agents/ (référencé, pas entièrement extrait)
- https://api-docs.deepseek.com/guides/thinking_mode/
- https://api-docs.deepseek.com/updates/
- https://api-docs.deepseek.com/news/news260813 (annonce GA Pro)
- https://api-docs.deepseek.com/news/news260424 (annonce dépréciation deepseek-chat/reasoner)
- https://arxiv.org/abs/2606.19348 (tech report)
- https://www.swebench.com/ (leaderboard officiel, non consulté directement pour une entrée V4)
- https://api-docs.deepseek.com/guides/kv_cache/ (mécanique du context caching)
- https://github.com/deepseek-ai/deepseek-harness (dsh, existence + statut confirmés par fetch direct)
- https://github.com/deepseek-ai/DeepSeek-V3/issues/1244 (bug tool-calling quantifié, ~11%/19 complétions)

## Secondaire (cité mais non vérifié par fetch direct, à revérifier avant usage décisionnel)
forums.developer.nvidia.com (thread NIM), reddit.com/r/LocalLLaMA + r/DeepSeek, cnblogs.com (intégration Claude Code CLI), deepwiki.com/noya21th/awesome-deepseek-v4 (wiki communautaire), community.n8n.io, morphllm.com / dev.to / codingfleet.com (scores SWE-bench tiers, contradictoires entre eux).

## Domaines à écarter (écosystème de spam SEO détecté sur ce sujet précis, cf. note méthodologique)
`deepseekv4pro.com`, `deepseekai.guide`, `chat-deep.ai`, `deepseek-usa.ai`, `costgoat.com`, `ofox.ai`, `benchlm.ai`, `therouter.ai`, `devtk.ai`, `findskill.ai`, `deepseekv4.network`, `localaimaster.com`, `codegenes.net`, `aiprofitboardroom.com`, `skywork.ai`, `agentconn.com`, `computeleap.com`, `verdent.ai`, `digitalapplied.com`, `deepseekdocs.com`, `dshdocs.com`, `open-harness.net`, `deepseekagent.io`. Toute affirmation dont c'est la seule source doit être traitée comme non fiable par défaut, pas juste "à vérifier".
