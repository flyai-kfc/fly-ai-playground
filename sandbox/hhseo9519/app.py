from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 화면에 창을 띄우지 않고 파일로만 저장하는 모드 (웹 서버에선 창이 뜰 수 없음)

import matplotlib.pyplot as plt
import yfinance as yf
from flask import Flask, render_template

from snapshot import TickerLookupError, fetch_snapshot, read_watchlist

app = Flask(__name__)
CHART_PATH = Path(__file__).parent / "static" / "chart.png"


def fetch_history(ticker, period="7d"):
    hist = yf.Ticker(ticker).history(period=period)
    if hist.empty:
        raise TickerLookupError(f"'{ticker}' 과거 데이터를 가져오지 못했습니다")
    return hist["Close"]


def draw_chart(histories):
    plt.figure(figsize=(8, 4))
    for ticker, closes in histories.items():
        plt.plot(closes.index, closes.values, marker="o", label=ticker)
    plt.title("Last 7 Days Closing Price")
    plt.xlabel("Date")
    plt.ylabel("Close Price")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    CHART_PATH.parent.mkdir(exist_ok=True)
    plt.savefig(CHART_PATH)
    plt.close()


@app.route("/")
def index():
    tickers = read_watchlist()
    rows = []
    histories = {}
    errors = []
    for ticker in tickers:
        try:
            rows.append(fetch_snapshot(ticker))
        except TickerLookupError as e:
            errors.append(str(e))
        try:
            histories[ticker] = fetch_history(ticker)
        except TickerLookupError as e:
            errors.append(str(e))
    draw_chart(histories)
    return render_template("index.html", rows=rows, errors=errors)


if __name__ == "__main__":
    app.run(debug=True)
