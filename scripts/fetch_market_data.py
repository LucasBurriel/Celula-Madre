#!/usr/bin/env python3
"""Fetch BTC/ETH daily OHLCV from CoinGecko (free, no auth).

Usage: python scripts/fetch_market_data.py [--days 365]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

COINS = {
    "bitcoin": "btc_daily_365.json",
    "ethereum": "eth_daily_365.json",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_coin(coin: str, days: int = 365) -> dict:
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Fetch market data for Célula Madre V5")
    parser.add_argument("--days", type=int, default=365, help="Days of history")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    for coin, filename in COINS.items():
        print(f"Fetching {coin}...", end=" ")
        data = fetch_coin(coin, args.days)
        path = os.path.join(DATA_DIR, filename)
        with open(path, "w") as f:
            json.dump(data, f)
        
        n = len(data["prices"])
        last_ts = data["prices"][-1][0]
        last_date = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        print(f"{n} days, last={last_date}")

    # Verify pipeline works
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.market_data import create_examples, split_examples

    for asset, fname in [("BTC", "btc_daily_365.json"), ("ETH", "eth_daily_365.json")]:
        examples = create_examples(os.path.join(DATA_DIR, fname), asset=asset)
        train, val, test = split_examples(examples)
        up = sum(1 for e in examples if e.direction == "UP")
        print(f"\n{asset}: {len(examples)} examples (Train:{len(train)} Val:{len(val)} Test:{len(test)})")
        print(f"  UP:{up} ({up/len(examples)*100:.0f}%) DOWN:{len(examples)-up}")
        print(f"  Range: {examples[0].date} to {examples[-1].date}")


if __name__ == "__main__":
    main()
