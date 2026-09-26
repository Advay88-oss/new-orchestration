"""The pluggable brand brain — one isolated brain per company (tenant).

Agents never read company files or Notion directly. They ask the brain,
through `Brain(tenant)` in-process or the Brain MCP server, for exactly six
things (the contract in "Pluggable Brand Brain — Architecture", 2026-09-25):

  get_brand_profile()              the whole versioned brand profile, every run
  get_whats_new(since)             dated events since the last run
  search_knowledge(query, ...)     hybrid BM25 + vector search, with sources
  get_visual_refs(topic, n)        brand images that match a topic
  get_competitor_patterns(topic)   competitor post patterns, summaries only
  log_post_outcome(post_id, ...)   a post's metrics, back into the brain

Vanna is tenant #1, not a hardcoded brain. A new company is onboarded by
filling its brain, never by changing an agent.

Agents reach these calls over the Brain MCP server (mcp_client.py), never
by reading files, Notion or the database themselves.

Storage: Postgres + pgvector when BRAIN_DATABASE_URL is set — one database,
tenant_id on every row, isolation enforced by row-level security below the
application code. Without it, one SQLite file per tenant at
pipeline/brain/tenants/<id>/brain.db. See store.py and pg.py.
"""
from pipeline.brand_brain.client import Brain, current_tenant

__all__ = ["Brain", "current_tenant"]
