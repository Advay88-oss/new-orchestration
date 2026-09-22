"""Save verified OpenCLI tweets for Aave and Morpho into cache directory."""
import json
from pathlib import Path

OUT_DIR = Path("D:/temp/opencli_tweets")
OUT_DIR.mkdir(parents=True, exist_ok=True)

aave_tweets = [
    {
        "id": "2097775588555542891",
        "author": "aave",
        "name": "Aave",
        "text": "RT @arc: Capital should not sit still. @aave is bringing efficient onchain credit to Arc. Coming soon.",
        "likes": 0, "retweets": 96, "replies": 0, "views": 4106, "is_retweet": True,
        "created_at": "Wed Sep 09 19:54:09 +0000 2026",
        "url": "https://x.com/aave/status/2097775588555542891"
    },
    {
        "id": "2097719737518080316",
        "author": "aave",
        "name": "Aave",
        "text": "RT @0xKolten: Aave V4 rapidly approaching its first billion deposits.",
        "likes": 0, "retweets": 6, "replies": 0, "views": 4330, "is_retweet": True,
        "created_at": "Wed Sep 09 16:12:13 +0000 2026",
        "url": "https://x.com/aave/status/2097719737518080316"
    },
    {
        "id": "2097687885579194757",
        "author": "aave",
        "name": "Aave",
        "text": "Aave V4 crossed $900 million deposits.",
        "likes": 257, "retweets": 28, "replies": 27, "views": 42826, "is_retweet": False,
        "created_at": "Wed Sep 09 14:05:39 +0000 2026",
        "url": "https://x.com/aave/status/2097687885579194757"
    },
    {
        "id": "2097445054864388338",
        "author": "aave",
        "name": "Aave",
        "text": "The world savings app is now in early access. Anyone need a Ghost Pass to skip the waitlist? Use code AAVEWILLWIN",
        "likes": 275, "retweets": 27, "replies": 72, "views": 54240, "is_retweet": False,
        "created_at": "Tue Sep 08 22:00:44 +0000 2026",
        "url": "https://x.com/aave/status/2097445054864388338"
    },
    {
        "id": "2097372686355734922",
        "author": "aave",
        "name": "Aave",
        "text": "AI tools and agents can now interact with Aave through the official Aave MCP server. Connect it to Claude, ChatGPT, or any MCP-compatible tool to build agents that can read protocol data, manage positions, and prepare transactions across every Aave deployment.",
        "likes": 434, "retweets": 62, "replies": 36, "views": 146064, "is_retweet": False,
        "created_at": "Tue Sep 08 17:13:10 +0000 2026",
        "url": "https://x.com/aave/status/2097372686355734922"
    },
    {
        "id": "2077414474017829232",
        "author": "aave",
        "name": "Aave",
        "text": "Aave V4 is now live on @avax, its first multi-chain expansion.",
        "likes": 776, "retweets": 96, "replies": 34, "views": 144484, "is_retweet": False,
        "created_at": "Wed Jul 15 15:26:21 +0000 2026",
        "url": "https://x.com/aave/status/2077414474017829232"
    },
    {
        "id": "2091964981675704495",
        "author": "aave",
        "name": "Aave",
        "text": "Coinbase Tokenized Stocks, coming soon to Aave V4 on @base. Only available in eligible geos ex U.S.",
        "likes": 493, "retweets": 72, "replies": 18, "views": 124125, "is_retweet": False,
        "created_at": "Mon Aug 24 19:04:53 +0000 2026",
        "url": "https://x.com/aave/status/2091964981675704495"
    },
    {
        "id": "2090802764196548900",
        "author": "aave",
        "name": "Aave",
        "text": "Aave V4 crossed $600 million deposits, a new all-time high.",
        "likes": 386, "retweets": 41, "replies": 15, "views": 43648, "is_retweet": False,
        "created_at": "Fri Aug 21 14:06:38 +0000 2026",
        "url": "https://x.com/i/status/2090802764196548900"
    },
    {
        "id": "2065118776069079441",
        "author": "aave",
        "name": "Aave",
        "text": "Aave V4 crossed $150 million deposits.",
        "likes": 520, "retweets": 38, "replies": 21, "views": 46185, "is_retweet": False,
        "created_at": "Thu Jun 11 17:07:38 +0000 2026",
        "url": "https://x.com/i/status/2065118776069079441"
    },
    {
        "id": "2093363724224463270",
        "author": "aave",
        "name": "Aave",
        "text": "Aave V4 hits a new all-time high in @USDC deposits.",
        "likes": 256, "retweets": 19, "replies": 8, "views": 37750, "is_retweet": False,
        "created_at": "Fri Aug 28 15:42:59 +0000 2026",
        "url": "https://x.com/i/status/2093363724224463270"
    }
]

morpho_tweets = [
    {
        "id": "2097728290618278096",
        "author": "Morpho",
        "name": "Morpho",
        "text": "RT @3f_xyz: 3F just crossed $30M. Key facts: 3 institutional RWAs live: Bitwise USCC, Pareto Credit x FalconXGlobal private credit...",
        "likes": 0, "retweets": 11, "replies": 0, "views": 1743, "is_retweet": True,
        "created_at": "Wed Sep 09 16:46:13 +0000 2026",
        "url": "https://x.com/Morpho/status/2097728290618278096"
    },
    {
        "id": "2097717592261890210",
        "author": "Morpho",
        "name": "Morpho",
        "text": "Turnkey is evolving with Morpho. Turnkey customers can now embed Morpho Vaults to provide yield within their products, via the wallet infrastructure they already use and trust.",
        "likes": 77, "retweets": 6, "replies": 9, "views": 4478, "is_retweet": False,
        "created_at": "Wed Sep 09 16:03:42 +0000 2026",
        "url": "https://x.com/Morpho/status/2097717592261890210"
    },
    {
        "id": "2097309026052899186",
        "author": "Morpho",
        "name": "Morpho",
        "text": "Morpho Midnight is now live on @ethereum. Access fixed term, fixed rate credit via the Markets App",
        "likes": 204, "retweets": 36, "replies": 27, "views": 38691, "is_retweet": False,
        "created_at": "Tue Sep 08 13:00:12 +0000 2026",
        "url": "https://x.com/Morpho/status/2097309026052899186"
    },
    {
        "id": "2097325974157168979",
        "author": "Morpho",
        "name": "Morpho",
        "text": "Earn on Pulsar, powered by Morpho. Coming soon on @arc mainnet.",
        "likes": 73, "retweets": 6, "replies": 6, "views": 8089, "is_retweet": False,
        "created_at": "Tue Sep 08 14:07:33 +0000 2026",
        "url": "https://x.com/Morpho/status/2097325974157168979"
    },
    {
        "id": "2095863396596109543",
        "author": "Morpho",
        "name": "Morpho",
        "text": "More Spark for borrowers. Markets with liquidity supplied by institutional liquidity providers like Spark Liquidity Layer are now easier to spot.",
        "likes": 115, "retweets": 19, "replies": 14, "views": 16484, "is_retweet": False,
        "created_at": "Fri Sep 04 13:15:47 +0000 2026",
        "url": "https://x.com/Morpho/status/2095863396596109543"
    },
    {
        "id": "2072395963793350687",
        "author": "Morpho",
        "name": "Morpho",
        "text": "Robinhood Earn, powered by Morpho. Millions of eligible @RobinhoodApp users can now earn onchain yield from a Morpho Vault curated by @SteakhouseFi via noncustodial wallets.",
        "likes": 645, "retweets": 82, "replies": 41, "views": 143386, "is_retweet": False,
        "created_at": "Wed Jul 01 19:04:35 +0000 2026",
        "url": "https://x.com/i/status/2072395963793350687"
    },
    {
        "id": "2064317262547525718",
        "author": "Morpho",
        "name": "Morpho",
        "text": "Morpho Association has raised $175M to build the open credit network for the world. Co-led by Paradigm, a16z crypto, Ribbit Capital with strategic participation from Apollo Global, VanEck, Circle Ventures, and Ledger.",
        "likes": 1142, "retweets": 195, "replies": 84, "views": 844161, "is_retweet": False,
        "created_at": "Tue Jun 09 12:02:43 +0000 2026",
        "url": "https://x.com/i/status/2064317262547525718"
    },
    {
        "id": "2079914394381910344",
        "author": "Morpho",
        "name": "Morpho",
        "text": "3 weeks in. $300M+ in total deposits. Morpho on Robinhood Chain has just started to grow.",
        "likes": 132, "retweets": 18, "replies": 12, "views": 8241, "is_retweet": False,
        "created_at": "Wed Jul 22 13:00:09 +0000 2026",
        "url": "https://x.com/i/status/2079914394381910344"
    },
    {
        "id": "2093011054582501792",
        "author": "Morpho",
        "name": "Morpho",
        "text": "MORPHO is now listed on Robinhood App",
        "likes": 313, "retweets": 41, "replies": 22, "views": 17755, "is_retweet": False,
        "created_at": "Thu Aug 27 16:21:36 +0000 2026",
        "url": "https://x.com/i/status/2093011054582501792"
    },
    {
        "id": "2084998612979720314",
        "author": "Morpho",
        "name": "Morpho",
        "text": "Morpho Effect in July: Morpho Midnight just went live. Robinhood integrated Morpho to power Robinhood Earn, with deposits approaching $300M.",
        "likes": 136, "retweets": 15, "replies": 9, "views": 11935, "is_retweet": False,
        "created_at": "Wed Aug 05 13:43:01 +0000 2026",
        "url": "https://x.com/i/status/2084998612979720314"
    }
]

(OUT_DIR / "aave.json").write_text(json.dumps(aave_tweets, indent=2), encoding="utf-8")
(OUT_DIR / "Morpho.json").write_text(json.dumps(morpho_tweets, indent=2), encoding="utf-8")
print(f"✅ Written {len(aave_tweets)} Aave and {len(morpho_tweets)} Morpho tweets to cache files")
