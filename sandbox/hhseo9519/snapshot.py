import csv
import logging
import sys
from datetime import date
from pathlib import Path

import yfinance as yf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)  # 존재하지 않는 티커일 때 yfinance가 찍는 장황한 로그를 숨김


class TickerLookupError(Exception):
    """존재하지 않는 티커거나 네트워크 문제로 데이터를 못 가져왔을 때"""


def read_watchlist(path="watchlist.txt"):
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def fetch_snapshot(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        price = info["lastPrice"]
        prev_close = info["previousClose"]
        volume = info["lastVolume"]
    except Exception as e:
        raise TickerLookupError(
            f"'{ticker}' 데이터를 가져오지 못했습니다 (존재하지 않는 티커이거나 네트워크 문제일 수 있어요)"
        ) from e
    change_pct = (price - prev_close) / prev_close * 100
    return {
        "ticker": ticker,
        "price": price,
        "prev_close": prev_close,
        "change_pct": change_pct,
        "volume": volume,
    }


def print_table(rows):
    print(f"{'티커':<8}{'현재가':>12}{'전일종가':>12}{'등락률(%)':>12}{'거래량':>15}")
    for row in rows:
        print(
            f"{row['ticker']:<8}"
            f"{row['price']:>12.2f}"
            f"{row['prev_close']:>12.2f}"
            f"{row['change_pct']:>+12.2f}"
            f"{row['volume']:>15,}"
        )


def save_csv(rows, folder="data"):
    Path(folder).mkdir(exist_ok=True)
    filepath = Path(folder) / f"snapshot_{date.today().isoformat()}.csv"
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["티커", "현재가", "전일종가", "등락률(%)", "거래량"])
        for row in rows:
            writer.writerow(
                [
                    row["ticker"],
                    round(row["price"], 2),
                    round(row["prev_close"], 2),
                    round(row["change_pct"], 2),
                    row["volume"],
                ]
            )
    return filepath


if __name__ == "__main__":
    tickers = read_watchlist()
    rows = []
    for ticker in tickers:
        try:
            rows.append(fetch_snapshot(ticker))
        except TickerLookupError as e:
            print(f"[경고] {e}")
    print_table(rows)
    if rows:
        saved_path = save_csv(rows)
        print(f"\nCSV로 저장했습니다: {saved_path}")
