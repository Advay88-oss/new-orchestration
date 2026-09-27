"""The Postgres brain: row-level security, hybrid search, per-tenant versions.

Runs against the database in pipeline/.env (BRAIN_PG_APP_URL / _ADMIN_URL,
from `python -m pipeline.brand_brain.pg setup`); skipped without one. Uses
two throwaway tenants and removes them afterwards.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_brain_postgres -v
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["OPS_ALERTS"] = "0"      # tests never page the owner

import unittest
from unittest import mock

from pipeline.brand_brain import store as S
from pipeline.brand_brain.chunking import chunk_markdown

APP = S._env_file("BRAIN_PG_APP_URL")
ADMIN = S._env_file("BRAIN_PG_ADMIN_URL")
A, B = "pgtest-alpha", "pgtest-beta"


def _reachable() -> bool:
    if not (APP and ADMIN):
        return False
    try:
        import psycopg
        with psycopg.connect(APP, connect_timeout=3):
            return True
    except Exception:                               # noqa: BLE001
        return False


@unittest.skipUnless(_reachable(), "no Postgres brain configured")
class PostgresBrainTest(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"BRAIN_DATABASE_URL": APP, "BRAIN_BACKEND": ""})
        self.env.start()
        self.emb = mock.patch("pipeline.brand_brain.embed.texts", side_effect=RuntimeError("offline"))
        self.emb.start()
        self._cleanup()
        from pipeline.brand_brain.client import Brain
        self.a, self.b = Brain(A, create=True), Brain(B, create=True)

    def tearDown(self):
        self._cleanup()
        self.emb.stop()
        self.env.stop()

    def _cleanup(self):
        import psycopg
        with psycopg.connect(ADMIN, autocommit=True) as con:
            for t in S.PG_TABLES:
                con.execute(f"DELETE FROM {t} WHERE tenant_id IN (%s, %s)", (A, B))
            con.execute("DELETE FROM tenants WHERE id IN (%s, %s)", (A, B))

    def test_rows_never_cross_tenants(self):
        self.a.save_profile({"company": {"name": "Alpha"}}, status="approved")
        self.b.save_profile({"company": {"name": "Beta"}}, status="approved")
        self.a.meta("k", "alpha-secret")
        self.assertEqual(self.a.get_brand_profile()["company"]["name"], "Alpha")
        self.assertEqual(self.b.get_brand_profile()["company"]["name"], "Beta")
        self.assertIsNone(self.b.meta("k"))
        # Even raw SQL without a WHERE clause sees only the bound tenant.
        con = S.connect(B)
        try:
            n = con.execute("SELECT COUNT(*) FROM meta WHERE value = 'alpha-secret'").fetchone()[0]
            self.assertEqual(n, 0)
            with self.assertRaises(Exception):   # and cannot write into another tenant
                con.execute("INSERT INTO meta(tenant_id, key, value) VALUES (?, ?, ?)", (A, "x", "y"))
                con.commit()
            con.rollback()
        finally:
            con.close()

    def test_versions_count_per_tenant(self):
        self.assertEqual(self.a.save_profile({"v": 1}), 1)
        self.assertEqual(self.a.save_profile({"v": 2}), 2)
        self.assertEqual(self.b.save_profile({"v": 1}), 1)

    def test_keyword_search_finds_product_terms(self):
        md = ("## Liquidation\n\nA position is liquidated when its health factor falls below one.\n\n"
              "## Deployment\n\nThe margin engine runs on Soroban testnet.")
        self.a.upsert_page("docs:a", chunk_markdown(md, title="Docs", company="Alpha", source_label="docs"),
                           source="docs", authority=2)
        hits = self.a.search_knowledge("Soroban margin engine", k=3)
        self.assertTrue(hits and "Soroban" in hits[0]["text"])
        self.assertEqual(hits[0]["mode"], "keyword-only")
        self.assertEqual(self.b.search_knowledge("Soroban", k=3), [])


if __name__ == "__main__":
    unittest.main()
