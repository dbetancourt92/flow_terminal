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
LOCAL_WS = os.getenv("WS_SERVER", "wss://flow-terminal.onrender.com")

seen_ids = set()

async def login_and_get_context(playwright):
    browser = await playwright.chromium.launch(headless=False)  # set True if deploying
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto("https://unusualwhales.com/login")
    await page.fill('input[placeholder="name@address.com"]', UW_EMAIL)
    await page.fill('input[type="password"]', UW_PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_url(lambda url: "/dashboard" in url or "/settings" in url)

    print("✅ Logged in and authenticated")
    return context

async def push_to_socket(data):
    try:
        async with websockets.connect(LOCAL_WS) as ws:
            await ws.send(json.dumps(data))
            print(f"📤 Sent flow: {data[1]} | {data[4]} | {data[11]}")
    except Exception as e:
        print(f"❌ Failed to send to frontend: {e}")

async def scrape_and_push(page, url):
    print(f"🌐 Navigating to: {url}")
    await page.goto(url)
    await page.wait_for_selector("table tbody")
    await asyncio.sleep(5)

    while True:
        rows = await page.locator("table tbody tr").all()
        print(f"🧪 Rows found: {len(rows)}")
        for row in rows:
            cells = await row.locator("td").all()
            if len(cells) < 15:
                continue
            values = [await c.inner_text() for c in cells]
            row_id = "|".join(values)
            if row_id in seen_ids:
                continue
            seen_ids.add(row_id)
            entry = values[:15] + ["True" if "🥃" in values[15] else "False"]
            await push_to_socket(entry)
        await asyncio.sleep(3)

async def main():
    async with async_playwright() as pw:
        context = await login_and_get_context(pw)
        pages = [await context.new_page() for _ in UW_FLOW_URLS]
        await asyncio.gather(*[
            scrape_and_push(p, url.strip()) for p, url in zip(pages, UW_FLOW_URLS)
        ])

if __name__ == "__main__":
    asyncio.run(main())
