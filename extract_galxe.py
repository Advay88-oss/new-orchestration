"""Extracts Top 100 Trending Campaigns from Galxe Explore.
Uses in-browser session execution to authenticate against the GraphQL gateway.
"""
import json
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"

GRAPHQL_QUERY = """
query CampaignList($input: ListCampaignInput!, $address: String!) {
  campaigns(input: $input) {
    pageInfo {
      endCursor
      hasNextPage
    }
    list {
      id
      numberID
      name
      type
      rewardName
      status
      chain
      space {
        name
        isVerified
      }
      tokenReward {
        userTokenAmount
        depositedTokenAmount
        tokenSymbol
      }
      rewardInfo {
        luckBasedToken {
          totalAmount
          tokenSymbol
        }
        discordRole {
          roleName
        }
        premint {
          price
          chain
        }
      }
      airdrop {
        rewardType
        rewardAmount
      }
      loyaltyPoints
      participants {
        participantsCount
        bountyWinnersCount
      }
    }
  }
}
"""

def extract_trending_campaigns(target_count=100):
    print("Launching browser with session support...")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to Galxe Explore page...")
        page.goto("https://app.galxe.com/quest/explore/all", timeout=45000, wait_until="domcontentloaded")
        time.sleep(4)

        all_campaigns = []
        after = "-1"

        fetch_js = """
        async ({ query, variables }) => {
            try {
                const resp = await fetch('https://graphigo.prd.galaxy.eco/query', {
                    method: 'POST',
                    headers: {
                        'content-type': 'application/json',
                        'accept': '*/*'
                    },
                    body: JSON.stringify({
                        operationName: 'CampaignList',
                        query: query,
                        variables: variables
                    })
                });
                const txt = await resp.text();
                try {
                    return JSON.parse(txt);
                } catch (e) {
                    return { error: 'parse_error', text: txt, status: resp.status };
                }
            } catch (err) {
                return { error: err.toString() };
            }
        }
        """

        while len(all_campaigns) < target_count:
            batch_size = min(30, target_count - len(all_campaigns))
            variables = {
                "address": "",
                "input": {
                    "listType": "Trending",
                    "first": batch_size,
                    "after": after,
                    "isRecurring": False,
                    "rewardTypes": []
                }
            }

            print(f"Fetching batch: cursor={after}, requesting={batch_size}...")
            res = page.evaluate(fetch_js, {"query": GRAPHQL_QUERY, "variables": variables})

            if not res or "data" not in res:
                print("Error or empty response from GraphQL:", res)
                break

            camp_data = res.get("data", {}).get("campaigns", {})
            clist = camp_data.get("list", [])
            page_info = camp_data.get("pageInfo", {})

            if not clist:
                print("No more campaigns returned.")
                break

            all_campaigns.extend(clist)
            print(f"Collected: {len(all_campaigns)} / {target_count}")

            if not page_info.get("hasNextPage"):
                print("Reached last available page.")
                break

            after = page_info.get("endCursor")
            time.sleep(1)

        browser.close()

    print(f"\nExtraction complete! Total collected: {len(all_campaigns)}")

    # Format into structured items
    structured = []
    for idx, c in enumerate(all_campaigns[:target_count], 1):
        name = c.get("name") or "Unnamed Campaign"
        parts = c.get("participants", {}) or {}
        p_count = parts.get("participantsCount", 0)

        # Parse rewards
        reward_parts = []
        if c.get("rewardName"):
            reward_parts.append(str(c["rewardName"]))
        
        # Token reward
        tr = c.get("tokenReward") or {}
        if tr.get("depositedTokenAmount") and tr.get("tokenSymbol"):
            reward_parts.append(f"{tr.get('depositedTokenAmount')} {tr.get('tokenSymbol')}")
        elif tr.get("tokenSymbol"):
            reward_parts.append(f"{tr.get('tokenSymbol')} Token")

        # Luck-based token
        lbt = (c.get("rewardInfo") or {}).get("luckBasedToken") or {}
        if lbt.get("totalAmount") and lbt.get("tokenSymbol"):
            reward_parts.append(f"{lbt.get('totalAmount')} {lbt.get('tokenSymbol')}")

        # Points
        lp = c.get("loyaltyPoints")
        if lp:
            reward_parts.append(f"{lp} Points")

        # Discord role
        dr = (c.get("rewardInfo") or {}).get("discordRole") or {}
        if dr.get("roleName"):
            reward_parts.append(f"Role: {dr.get('roleName')}")

        # Fallback to type
        if not reward_parts:
            reward_parts.append(c.get("type") or "Custom Reward / OAT")

        structured.append({
            "rank": idx,
            "campaign_name": name,
            "total_participants": p_count,
            "reward": " + ".join(reward_parts),
            "space": (c.get("space") or {}).get("name", "N/A"),
            "chain": c.get("chain", "N/A"),
            "url": f"https://app.galxe.com/quest/{c.get('id')}"
        })

    with open("galxe_top_100_trending.json", "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2)

    return structured

if __name__ == "__main__":
    items = extract_trending_campaigns(100)
    print(f"\nTop 5 Sample Results:")
    for i in items[:5]:
        print(f"#{i['rank']} {i['campaign_name']} | Participants: {i['total_participants']} | Reward: {i['reward']}")
