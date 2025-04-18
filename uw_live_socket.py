import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import json
import websockets

load_dotenv()

UW_EMAIL = os.getenv("UW_EMAIL")
UW_PASSWORD = os.getenv("UW_PASSWORD")
UW_FLOW_URLS = os.getenv("UW_FLOW_URLS", "").split(",")

clients = set()

# Send flow to local websocket server
async def push_to_local_ws(row):
    uri = "ws://127.0.0.1:8888"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(row))
    except Exception as e:
        print(f"❌ Failed to push to frontend: {e}")

async def auto_login(page, email, password):
    print("\n🔐 Logging in...")
    await page.goto("https://unusualwhales.com/login")
    await page.wait_for_selector('input[placeholder="name@address.com"]')
    await page.fill('input[placeholder="name@address.com"]', email)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_url(lambda url: "/dashboard" in url or "/settings" in url)
    print("✅ Login successful!")

async def scrape_page(page, url):
    print(f"📡 Watching live flow: {url}")
    await page.goto(url)
    await page.wait_for_selector("table tbody")
    await asyncio.sleep(3)

    seen_ids = set()

    while True:
        rows = await page.locator("table tbody tr").all()
        for row in rows:
            cells = await row.locator("td").all()
            if len(cells) < 15:
                continue
            values = [await c.inner_text() for c in cells]
            row_id = "|".join(values)
            if row_id in seen_ids or not values[0].strip():
                continue
            seen_ids.add(row_id)

            # Build structured row to match ws_client.js expectations
            payload = {
                "time": values[0],
                "ticker": values[1],
                "side": values[2],
                "strike": values[3],
                "type": values[4],
                "expiry": values[5],
                "dte": values[6],
                "stock": values[7],
                "bidask": values[8],
                "spot": values[9],
                "size": values[10],
                "premium": values[11],
                "volume": values[12],
                "oi": values[13],
                "chain_pct": values[14],
                "multi": "True" if "🥃" in values[15] else "False"
            }

            await push_to_local_ws(payload)
        await asyncio.sleep(2)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        login_page = await context.new_page()

        await auto_login(login_page, UW_EMAIL, UW_PASSWORD)
        pages = [await context.new_page() for _ in UW_FLOW_URLS]

        await asyncio.gather(*[
            scrape_page(p, u.strip()) for p, u in zip(pages, UW_FLOW_URLS)
        ])

if __name__ == "__main__":
    asyncio.run(main())