import json
import time
import os
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ----------------- Config -----------------
BASE_DIR = Path(__file__).resolve().parent
HOLDINGS_CSV = BASE_DIR / "holdings.csv"
OUTFILE = BASE_DIR / "kite_prices.json"

SCRAPE_EVERY_SEC = 2
REFRESH_EVERY_SEC = 300        # refresh every 5 min
MIN_WRITE_EVERY_SEC = 5        # write heartbeat at least every N sec
WAIT_TIMEOUT_SEC = 20


def load_watchlist_from_holdings(csv_path: Path) -> set[str]:
    df = pd.read_csv(csv_path, skipinitialspace=True)
    df.columns = df.columns.str.strip()
    if "Name" not in df.columns:
        raise ValueError(f"holdings.csv must have a 'Name' column. Found: {list(df.columns)}")
    return set(df["Name"].astype(str).str.strip().tolist())


def atomic_write_json(path: Path, payload: dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)  # atomic replace [web:330]


def deep_scrape_symbol_ltp(driver):
    # Shadow-DOM friendly deep query. If selectors don't exist, returns empty. [web:209][web:210]
    js = r"""
    const deepAll = (selector, root=document) => {
      let out = Array.from(root.querySelectorAll(selector));
      const all = root.querySelectorAll('*');
      for (const el of all) {
        if (el.shadowRoot) out = out.concat(deepAll(selector, el.shadowRoot));
      }
      return out;
    };

    const symEls = deepAll('.tradingsymbol');
    const result = [];

    for (const el of symEls) {
      const sym = (el.textContent || '').trim();
      let row = el.closest('.instrument');
      if (!row) row = el.parentElement;

      let priceEl = null;
      if (row) priceEl = row.querySelector('.last-price');

      const ltp = priceEl ? (priceEl.textContent || '').trim() : null;
      result.push([sym, ltp]);
    }
    return result;
    """
    return driver.execute_script(js)


def wait_for_dashboard(driver):
    """
    We can't guarantee exact Kite selectors because UI may change,
    but we can at least wait for BODY + not being stuck on blank load.
    Also prints URL/title so you know where Selenium is.
    """
    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )  # standard explicit wait pattern [web:332]


def main():
    watchlist = load_watchlist_from_holdings(HOLDINGS_CSV)
    print("Watchlist (from holdings.csv Name column):", watchlist)
    print("Writing JSON to:", str(OUTFILE))

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://kite.zerodha.com/")

    input(
        "Login manually in Chrome (ID+Password+OTP).\n"
        "After login, ensure Marketwatch/watchlist with prices is visible.\n"
        "Then press ENTER here to start scraping...\n"
    )

    # initial wait after login
    try:
        wait_for_dashboard(driver)
    except Exception as e:
        print("Initial page wait failed:", e)

    last_refresh = 0.0
    last_write = 0.0
    consecutive_failures = 0

    while True:
        now = time.time()

        # periodic refresh to keep session alive
        if now - last_refresh > REFRESH_EVERY_SEC:
            try:
                driver.refresh()  # correct in Selenium Python [web:314]
                last_refresh = now
                print("Refreshed Kite tab to keep session alive.")
                wait_for_dashboard(driver)
            except Exception as e:
                print("Refresh failed:", e)

        prices = {}
        error = None

        try:
            print("URL:", driver.current_url)
            print("Title:", driver.title)

            # quick selector counts (to detect DOM mismatch)
            cnt_sym = len(driver.find_elements(By.CSS_SELECTOR, ".tradingsymbol"))
            cnt_price = len(driver.find_elements(By.CSS_SELECTOR, ".last-price"))
            cnt_inst = len(driver.find_elements(By.CSS_SELECTOR, ".instrument"))
            print("counts -> .instrument:", cnt_inst, " .tradingsymbol:", cnt_sym, " .last-price:", cnt_price)  # [web:328]

            pairs = deep_scrape_symbol_ltp(driver)
            print("pairs found:", len(pairs))
            print("sample:", pairs[:10])

            for sym, ltp_txt in pairs:
                if ltp_txt:
                    try:
                        prices[sym] = float(ltp_txt.replace(",", ""))
                    except Exception:
                        pass

            consecutive_failures = 0

        except Exception as e:
            consecutive_failures += 1
            error = str(e)
            print(f"Scrape error (#{consecutive_failures}): {e}")

        # heartbeat write
        if (now - last_write) >= MIN_WRITE_EVERY_SEC:
            payload = {
                "ts": now,
                "prices": prices,
                "ok": error is None,
                "error": error,
                "failures": consecutive_failures,
            }
            try:
                atomic_write_json(OUTFILE, payload)
                last_write = now
                print("kite_prices.json updated:", prices)
            except Exception as e:
                print("JSON write failed:", e)

        time.sleep(SCRAPE_EVERY_SEC)


if __name__ == "__main__":
    main()
