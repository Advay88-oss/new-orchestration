#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Ensure we use the ms-playwright path on D:
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:/ms-playwright"

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright not found in virtualenv.")
    sys.exit(1)

def main():
    print("=== Launching Fast Headless Chrome with Profile 6 ===")
    user_data_dir = "C:/Users/Advay Anand/AppData/Local/Google/Chrome/User Data"
    screenshot_path = Path("D:/new orchestration/pipeline/state/twitter_test.png")
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        try:
            # Launch persistent Chrome in headless mode using the exact executable path
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
                headless=True,
                args=[
                    "--profile-directory=Profile 6",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            
            page = context.pages[0] if len(context.pages) > 0 else context.new_page()
            page.set_viewport_size({"width": 1280, "height": 720})
            
            print("\nNavigating to Twitter/X Home...")
            # Use 'domcontentloaded' to prevent networkidle hangs on dynamic Twitter analytics
            page.goto("https://x.com/home", timeout=30000, wait_until="domcontentloaded")
            print("🎉 Navigated successfully!")
            
            # Wait for 10 seconds for the react app to completely render the feed
            print("Waiting 10 seconds for the React app and session to render...")
            page.wait_for_timeout(10000)
            
            # Take a screenshot to verify login status
            print(f"Taking a screenshot to verify your logged-in feed...")
            page.screenshot(path=str(screenshot_path))
            print(f"✅ Screenshot saved successfully to: {screenshot_path}")
            
            context.close()
            print("Chrome context closed successfully.")
            
        except Exception as e:
            print(f"\n❌ Failed to launch or automate Chrome: {e}")

if __name__ == "__main__":
    main()
