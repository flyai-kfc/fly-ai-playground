"""가계부 CLI - 2단계: 실제로 파일에 저장하기

data.json 파일에 기록을 쌓고, list 로 다시 꺼내 봅니다.
"""

import argparse
import json
from datetime import date
from pathlib import Path

# 이 .py 파일이 있는 폴더 안의 data.json 을 가리킨다.
# 이렇게 해두면 어느 폴더에서 실행하든 항상 같은 파일을 쓴다.
DATA_FILE = Path(__file__).parent / "data.json"


# ---------- 저장소 다루기 ----------

def load_data():
    """data.json 을 읽어서 파이썬 딕셔너리로 돌려준다.

    파일이 아직 없으면(맨 처음 실행) 빈 상태를 만들어 준다.
    """
    if not DATA_FILE.exists():
        return {"next_id": 1, "records": []}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    """딕셔너리를 data.json 에 써 넣는다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False : 한글이 \uXXXX 로 깨지지 않게
        # indent=2          : 사람이 눈으로 읽을 수 있게 줄 맞춰서
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- 명령별 동작 ----------

def cmd_add(args):
    data = load_data()

    record = {
        "id": data["next_id"],
        "date": args.date or date.today().isoformat(),
        "amount": args.amount,
        "category": args.category,
        "memo": args.memo or "",
    }

    data["records"].append(record)
    data["next_id"] += 1
    save_data(data)

    print(f"{record['id']}번으로 저장했습니다. "
          f"{record['date']} / {record['amount']:,}원 / {record['category']}")

    # 이 카테고리를 처음 쓰는 거라면 알려준다 (SPEC 6번)
    used = [r["category"] for r in data["records"]]
    if used.count(args.category) == 1:
        print(f"※ '{args.category}'는 처음 쓰는 카테고리입니다.")


def cmd_list(args):
    data = load_data()
    records = data["records"]

    if not records:
        print("아직 기록이 없습니다. add 로 추가해 보세요.")
        return

    # 최신 날짜가 위로 오도록 정렬 (날짜가 같으면 나중에 넣은 게 위로)
    records = sorted(records, key=lambda r: (r["date"], r["id"]), reverse=True)

    print(f"{'번호':>4}  {'날짜':<12} {'금액':>10}  {'카테고리':<10} 메모")
    print("-" * 60)
    for r in records:
        print(f"{r['id']:>4}  {r['date']:<12} {r['amount']:>9,}원  "
              f"{r['category']:<10} {r['memo']}")
    print("-" * 60)

    total = sum(r["amount"] for r in records)
    print(f"{'합계':>4}  {len(records)}건{'':<8} {total:>9,}원")


# ---------- 명령어 해석 ----------

def main():
    parser = argparse.ArgumentParser(
        prog="ledger",
        description="터미널에서 쓰는 개인 가계부",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="지출 추가")
    p_add.add_argument("amount", type=int, help="금액 (원 단위, 정수)")
    p_add.add_argument("category", help="카테고리 (예: 식비, 교통)")
    p_add.add_argument("--date", help="날짜 YYYY-MM-DD (생략하면 오늘)")
    p_add.add_argument("--memo", help="짧은 설명")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="전체 목록 보기")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
