import asyncio
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.text import Text
from dotenv import load_dotenv
import os

# Interactive filter prompt
def prompt_user_filters():
    print("\n🛠️  OPTIONS FLOW FILTER CONFIGURATION\n")

    tickers = input("1️⃣ Enter tickers (comma-separated, or leave blank for all): ").upper().split(",")
    opt_type = input("2️⃣ Option type [CALL / PUT / BOTH]: ").strip().upper()
    side = input("3️⃣ Trade side [ASK / BID / MID / ALL]: ").strip().upper()
    min_size = input("4️⃣ Minimum size (default 0): ").strip()
    min_premium = input("5️⃣ Minimum premium (default 0): ").strip()
    max_dte = input("6️⃣ Maximum DTE (default 9999): ").strip()
    vol_gt_oi = input("7️⃣ Volume > OI only? [y/N]: ").strip().lower() == "y"
    multi_leg_only = input("8️⃣ Multi-leg only? [y/N]: ").strip().lower() == "y"

    filters = {
        "tickers": set(t.strip().upper() for t in tickers if t.strip()),
        "type": opt_type if opt_type in ["CALL", "PUT"] else "",
        "side": side if side in ["ASK", "BID", "MID"] else "",
        "min_size": int(min_size) if min_size.isdigit() else 0,
        "min_premium": int(min_premium) if min_premium.isdigit() else 0,
        "max_dte": int(max_dte) if max_dte.isdigit() else 9999,
        "vol_gt_oi": vol_gt_oi,
        "multi_leg_only": multi_leg_only
    }

    print("\n✅ Filters configured.\n")
    return filters

# Table rendering
flow_data = []
seen_ids = set()

def render_table():
    table = Table(show_header=True, header_style="bold magenta")
    columns = ["Time", "Ticker", "Side", "Strike", "Type", "Expiry", "DTE", "Stock",
               "Bid-Ask", "Spot", "Size", "Premium", "Volume", "OI", "Chain%", "Multileg"]
    for col in columns:
        table.add_column(col)

    for row in flow_data[-25:]:
        (time, ticker, side, strike, opt_type, expiry, dte, stock,
         bidask, spot, size, premium, volume, oi, chain_pct, is_multi) = row

        side_fmt = Text(side, style={"BID": "yellow", "ASK": "cyan", "MID": "white"}.get(side, "white"))
        type_fmt = Text(f" {opt_type} ", style="bold white on green" if opt_type == "CALL" else "bold white on red")
        size_fmt = Text(size, style="bold yellow" if int(size) > 10 else "")
        premium_fmt = Text(premium, style="bold green" if "K" in premium else "bold red")
        volume_fmt = Text(volume, style="bold blue" if int(volume.replace(",", "")) > 500 else "")

        table.add_row(time, ticker, side_fmt, strike, type_fmt, expiry, dte, stock,
                      bidask, spot, size_fmt, premium_fmt, volume_fmt, oi, chain_pct, is_multi)
    return table

# Login
async def auto_login(page, email, password):
    print("\n🔐 Logging in...")
    await page.goto("https://unusualwhales.com/login")
    await page.wait_for_selector('input[placeholder="name@address.com"]')
    await page.fill('input[placeholder="name@address.com"]', email)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_url(lambda url: "/dashboard" in url or "/settings" in url)
    print("✅ Login successful!")

# Apply filters
def should_display(row, filters):
    try:
        ticker = row[1].upper()
        side = row[2].upper()
        opt_type = row[4].upper()
        dte = int(row[6].replace("d", "").strip())
        size = int(row[10])
        premium_val = int(row[11].replace("$", "").replace("K", "000"))
        volume = int(row[12].replace(",", ""))
        oi = int(row[13].replace(",", ""))
        is_multi = row[15] == "True"

        if filters["tickers"] and ticker not in filters["tickers"]:
            return False
        if filters["type"] and opt_type != filters["type"]:
            return False
        if filters["side"] and side != filters["side"]:
            return False
        if size < filters["min_size"]:
            return False
        if premium_val < filters["min_premium"]:
            return False
        if dte > filters["max_dte"]:
            return False
        if filters["vol_gt_oi"] and volume <= oi:
            return False
        if filters["multi_leg_only"] and not is_multi:
            return False

        return True
    except Exception:
        return False

# Scraper
async def scrape_page(page, url, live, filters):
    print(f"📡 Scraping: {url}")
    await page.goto(url)
    await page.wait_for_selector("table tbody")
    await asyncio.sleep(3)

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

            entry = values[:15] + ["True" if "🥃" in values[15] else "False"]
            if should_display(entry, filters):
                flow_data.append(entry)
                live.update(render_table())

        await asyncio.sleep(1.5)

# Main
async def main():
    load_dotenv()
    email = os.getenv("UW_EMAIL")
    password = os.getenv("UW_PASSWORD")
    raw_urls = os.getenv("UW_FLOW_URLS", "")
    urls = [u.strip() for u in raw_urls.split(",") if u.strip()]

    filters = prompt_user_filters()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        login_page = await context.new_page()

        if not urls[0].startswith("http://localhost"):
            await auto_login(login_page, email, password)
        else:
            print("🧪 Skipping login for localhost")

        pages = [await context.new_page() for _ in urls]
        print("\n📋 Scraping the following URLs:")
        for url in urls:
            print(" -", url)

        with Live(render_table(), refresh_per_second=1, screen=True) as live:
            await asyncio.gather(*[
                scrape_page(p, u, live, filters) for p, u in zip(pages, urls)
            ])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

