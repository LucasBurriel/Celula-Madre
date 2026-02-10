"""Market data loader for Célula Madre V5.

Loads historical BTC/ETH data and creates prediction examples.
Each example: agent sees N days of history, predicts next day direction.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class MarketExample:
    """A single prediction example."""
    date: str  # Date being predicted
    context: str  # Market context (last N days formatted)
    direction: str  # Actual direction: "UP" or "DOWN"
    change_pct: float  # Actual % change
    price_open: float  # Price at prediction time
    price_close: float  # Price at end of period


def load_daily_prices(filepath: str) -> list[tuple[str, float]]:
    """Load daily prices from CoinGecko JSON.
    
    Returns: [(date_str, price), ...]
    """
    with open(filepath) as f:
        data = json.load(f)
    
    prices = []
    for ts_ms, price in data["prices"]:
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        prices.append((date_str, round(price, 2)))
    
    return prices


def format_price_context(prices: list[tuple[str, float]], lookback: int = 30) -> str:
    """Format last N days of prices as context string."""
    recent = prices[-lookback:]
    
    lines = ["Date       | Price USD  | Change"]
    lines.append("-" * 42)
    
    for i, (date, price) in enumerate(recent):
        if i == 0:
            change = ""
        else:
            prev_price = recent[i-1][1]
            pct = ((price - prev_price) / prev_price) * 100
            arrow = "↑" if pct > 0 else "↓" if pct < 0 else "→"
            change = f"{arrow} {pct:+.1f}%"
        
        lines.append(f"{date} | ${price:>10,.2f} | {change}")
    
    # Add summary stats
    prices_only = [p for _, p in recent]
    high = max(prices_only)
    low = min(prices_only)
    avg = sum(prices_only) / len(prices_only)
    volatility = (high - low) / avg * 100
    
    # Trend
    first_price = prices_only[0]
    last_price = prices_only[-1]
    trend_pct = ((last_price - first_price) / first_price) * 100
    
    lines.append("")
    lines.append(f"Period: {recent[0][0]} to {recent[-1][0]}")
    lines.append(f"High: ${high:,.2f} | Low: ${low:,.2f} | Avg: ${avg:,.2f}")
    lines.append(f"Volatility: {volatility:.1f}% | Trend: {trend_pct:+.1f}%")
    
    return "\n".join(lines)


def create_examples(
    filepath: str,
    asset: str = "BTC",
    lookback: int = 30,
    min_move_pct: float = 0.0,
) -> list[MarketExample]:
    """Create prediction examples from historical data.
    
    Args:
        filepath: Path to CoinGecko JSON
        asset: Asset name for context
        lookback: Days of history to show
        min_move_pct: Minimum % move to include (filter flat days)
    
    Returns:
        List of MarketExample
    """
    all_prices = load_daily_prices(filepath)
    examples = []
    
    for i in range(lookback, len(all_prices) - 1):
        history = all_prices[:i+1]  # Everything up to today
        tomorrow_date, tomorrow_price = all_prices[i+1]
        today_date, today_price = all_prices[i]
        
        change_pct = ((tomorrow_price - today_price) / today_price) * 100
        
        if abs(change_pct) < min_move_pct:
            continue
        
        direction = "UP" if change_pct > 0 else "DOWN"
        
        context = f"Asset: {asset}/USD\n"
        context += f"Current date: {today_date}\n"
        context += f"Current price: ${today_price:,.2f}\n\n"
        context += f"Last {lookback} days:\n"
        context += format_price_context(history, lookback)
        context += f"\n\nQuestion: Will {asset} go UP or DOWN in the next 24 hours?"
        
        examples.append(MarketExample(
            date=tomorrow_date,
            context=context,
            direction=direction,
            change_pct=round(change_pct, 2),
            price_open=today_price,
            price_close=tomorrow_price,
        ))
    
    return examples


def split_examples(
    examples: list[MarketExample],
    train_ratio: float = 0.4,
    val_ratio: float = 0.3,
) -> tuple[list[MarketExample], list[MarketExample], list[MarketExample]]:
    """Split examples chronologically (no shuffle — temporal order matters).
    
    Returns: (train, val, test)
    """
    n = len(examples)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    return examples[:train_end], examples[train_end:val_end], examples[val_end:]


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    
    btc_examples = create_examples(
        os.path.join(data_dir, "btc_daily_365.json"),
        asset="BTC",
        lookback=30,
    )
    
    train, val, test = split_examples(btc_examples)
    
    print(f"BTC examples: {len(btc_examples)} total")
    print(f"  Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    print(f"  Date range: {btc_examples[0].date} to {btc_examples[-1].date}")
    
    # Stats
    up = sum(1 for e in btc_examples if e.direction == "UP")
    down = len(btc_examples) - up
    print(f"  UP: {up} ({up/len(btc_examples)*100:.0f}%) | DOWN: {down} ({down/len(btc_examples)*100:.0f}%)")
    
    # Show one example
    print(f"\n--- Example #{len(train)} (first val) ---")
    print(f"Context (truncated):\n{val[0].context[:500]}...")
    print(f"\nAnswer: {val[0].direction} ({val[0].change_pct:+.2f}%)")
