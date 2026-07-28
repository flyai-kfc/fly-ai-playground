# 관심 종목 일일 스냅샷 도구

`watchlist.txt`에 적어둔 해외 종목들을 조회해서 현재가/전일 종가/등락률/거래량을 보여주는 도구예요.
CLI로도 볼 수 있고, 웹 브라우저로 접속해서 최근 7일 가격 추이 그래프까지 볼 수도 있어요.

자세한 기획 배경은 [SPEC.md](SPEC.md) 참고.

## 설치

```bash
pip install -r requirements.txt
```

## 관심 종목 설정

`watchlist.txt`에 한 줄에 티커 하나씩 적으면 돼요 (해외 종목만 지원).

```
AAPL
TSLA
MSFT
```

## 실행 방법

### 1) CLI로 조회 (터미널 출력 + CSV 저장)

```bash
python snapshot.py
```

- 터미널에 표로 결과가 출력돼요
- `data/snapshot_YYYY-MM-DD.csv`로 결과가 저장돼요 (날짜별로 파일이 생겨요)

### 2) 웹으로 조회 (표 + 최근 7일 그래프)

```bash
python app.py
```

실행 후 브라우저에서 `http://127.0.0.1:5000` 접속. 종료하려면 터미널에서 `Ctrl+C`.

## 주의사항

- 존재하지 않는 티커를 넣으면 그 종목만 건너뛰고 경고 메시지가 뜨고, 나머지는 정상 조회돼요
- `data/`, `static/chart.png`는 실행할 때마다 새로 생기는 결과물이라 git에는 안 올라가요 (`.gitignore` 처리됨)
