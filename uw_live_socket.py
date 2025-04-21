
import asyncio
import json
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import websockets

load_dotenv()
UW_EMAIL = os.getenv("UW_EMAIL")
UW_PASSWORD = os.getenv("UW_PASSWORD")
UW_FLOW_URLS = os.getenv("UW_FLOW_URLS", "").split(",")

WS_FRONTEND_URI = "wss://flow-terminal.onrender.com"

seen_ids = set()

async def login(page):
    print("🔐 Logging in to Unusual Whales...")
    await page.goto("https://unusualwhales.com/login")
    await page.fill('input[placeholder="name@address.com"]', UW_EMAIL)
    await page.fill('input[type="password"]', UW_PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_url(lambda url: "/dashboard" in url or "/settings" in url)
    print("✅ Logged in!")

async def push_to_frontend(payload):
    try:
        async with websockets.connect(WS_FRONTEND_URI) as websocket:
            await websocket.send(json.dumps(payload))
            print("📤 Sent to frontend.")
    except Exception as e:
        print(f"❌ Failed to push to frontend: {e}")

async def scrape_flow(page, url):
    print(f"🌐 Navigating to {url}")
    await page.goto(url)
    await page.wait_for_selector("table tbody")
    await asyncio.sleep(3)

    while True:
        try:
            rows = await page.locator("table tbody tr").all()
            for row in rows:
                cells = await row.locator("td").all()
                if len(cells) < 15:
                    continue

                values = [await c.inner_text() for c in cells]
                row_id = "|".join(values)
                if row_id in seen_ids:
                    continue
                seen_ids.add(row_id)

                payload = values[:15] + ["True" if "🥃" in values[15] else "False"]
                await push_to_frontend(payload)

            await asyncio.sleep(2)
        except Exception as e:
            print(f"⚠️ Error during scraping: {e}")
            await asyncio.sleep(5)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        login_page = await context.new_page()

        await login(login_page)
        pages = [await context.new_page() for _ in UW_FLOW_URLS]

        await asyncio.gather(*[scrape_flow(p, url.strip()) for p, url in zip(pages, UW_FLOW_URLS)])

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
