---
type: Content Topic
order: 3
title: Unified SDK, CLI, and MCP Rails
description: The developer integrations of Vanna, showcasing how any agent interface can connect to our
  composable credit rails.
topic: developer-experience
angle: Unified SDK, CLI, and MCP Rails
tags:
- content
- taxonomy
status: stable
sources:
- id: marketing-config
  resource: /pipeline/config/marketing_config.json
  title: marketing_config.taxonomy
---

# Unified SDK, CLI, and MCP Rails

The developer integrations of Vanna, showcasing how any agent interface can connect to our composable credit rails.

`topic` is the vocabulary the whole pipeline speaks: the scout must return one of
these values, the conductor selects from them, and `content_history.json` records
which was used so the anti-repetition logic can rotate.

**Renaming `topic` is a breaking change.** The permitted-value list is also
written into the scout prompt in the orchestrator; change one without the other
and runs silently carry an unrecognised topic.
