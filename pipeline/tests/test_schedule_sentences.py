"""How one sentence becomes a schedule: each gap goes to the job named
nearest to it, a count with a word in between still counts, and a named
protocol reaches the scrape.

    .venv/Scripts/python.exe -m pipeline.tests.offline test_schedule_sentences
"""
from __future__ import annotations

import unittest

from pipeline.scheduler import configurable_scheduler_daemon as D


def plan(text: str) -> tuple[dict, int | None]:
    p = D.parse_tell(text)
    return {j["job"]: j.get("interval") for j in p.get("jobs", [])}, p.get("posts_left")


class Sentences(unittest.TestCase):
    def test_each_gap_goes_to_the_nearest_job(self):
        cases = {
            "give me 5 twitter post of Term Finance every 2 min scraping and research":
                ({"research_collect": "2m", "gtm_cycle": None}, 5),
            "give me 5 twitter post of this protocol every 2 min scraping and research":
                ({"research_collect": "2m", "gtm_cycle": None}, 5),
            "post every 20 min and news every 2 min": ({"research_collect": "2m", "gtm_cycle": "20m"}, None),
            "memes every hour and ideas every 2 hours": ({"ideas_panel": "2h", "memes_panel": "1h"}, None),
            "Scrape news and socials every 5 minutes and make posts from it":
                ({"research_collect": "5m", "gtm_cycle": None}, 10),
            "give me fresh news every two minutes": ({"research_collect": "2m"}, None),
            "make 10 posts every 30 min": ({"gtm_cycle": "30m"}, 10),
            "news har 5 minute do": ({"research_collect": "5m"}, None),
            "make 3 posts": ({"gtm_cycle": None}, 3),
            "scrape twitter every minute": ({"research_collect": "1m"}, None),
        }
        for text, want in cases.items():
            self.assertEqual(plan(text), want, text)

    def test_a_named_protocol_reaches_the_scrape(self):
        b = D._research_brief("give me 5 twitter post of Term Finance every 2 min scraping and research")
        self.assertEqual(b["sources"], ["twitter"])
        self.assertIn("term finance", b["names"])
        self.assertIn("morpho", D._research_brief("news on morpho every 5 min")["names"])


if __name__ == "__main__":
    unittest.main()
