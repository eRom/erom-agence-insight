# Les chantiers de Romain

La grille de la section 6. Un repo est pertinent s'il touche l'un de ces chantiers de façon nommable : « remplace X », « s'ajoute à Y », « donne une idée pour Z ». Sinon, sa pertinence est « aucun chantier en cours », et c'est une réponse honnête, pas un échec.

À tenir à jour à la main : cette liste vieillit plus vite que la skill.

| Chantier | Ce qui compte |
|---|---|
| Harnais Claude Code | skills, plugins, hooks, sous-agents, garde-fous (`guard-tools`), routage des modèles |
| Serveurs MCP | Caserne (Linear, Slack, mail), erom-memory, erom-context ; tout MCP auto-hébergeable |
| Mémoire des agents | erom-memory-system : capture des sessions, consolidation, rappel sémantique |
| Store et veille | erom-agence-store, RAG `agence-rag`, rapports d'insight, deep research multi-moteurs |
| IdemA | IDE terminal macOS pour piloter des agents |
| Raycast | extensions et automatisations du poste |
| Agents locaux | modèles locaux (Ollama, fine-tune 4B), agents CLI concurrents (opencode, goose, crush) |
| Infra perso | Mac, VPS, tailnet Tailscale, launchd, auto-hébergement |
| Image, vision, voix | génération d'images, juge vision des rendus UI, synthèse vocale en français |

Préférences qui pèsent sur le verdict :

- **Auto-hébergé** d'abord : un SaaS obligatoire baisse le verdict d'un cran, sauf s'il n'existe aucune alternative locale.
- **Stack** : TypeScript avec bun, Python avec uv, Rust pour la performance, macOS en premier.
- **Anti-surcharge** : un outil qui double ce qui existe déjà chez Romain est `pas-pertinent`, même s'il est bon.
