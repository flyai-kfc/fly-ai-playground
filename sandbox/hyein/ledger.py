"""가계부 CLI - 4단계: 검색과 필터

data.json 파일에 기록을 쌓고, 번호로 지목해서 지우거나 고칩니다.
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


def print_table(records, empty_message="기록이 없습니다."):
    """기록 목록을 표로 찍고 합계를 보여준다. list 와 search 가 같이 쓴다."""
    if not records:
        print(empty_message)
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


def cmd_list(args):
    data = load_data()
    print_table(data["records"], "아직 기록이 없습니다. add 로 추가해 보세요.")


def cmd_search(args):
    data = load_data()
    records = data["records"]

    # 조건을 하나씩 차례로 걸러낸다.
    # 조건을 안 준 항목은 그냥 건너뛰므로, 여러 조건을 자유롭게 조합할 수 있다.
    if args.category:
        records = [r for r in records if r["category"] == args.category]

    if args.keyword:
        kw = args.keyword.lower()
        records = [r for r in records if kw in r["memo"].lower()]

    # 날짜는 YYYY-MM-DD 형식이라 문자열끼리 비교해도 순서가 맞다
    if getattr(args, "from_date", None):
        records = [r for r in records if r["date"] >= args.from_date]

    if args.to:
        records = [r for r in records if r["date"] <= args.to]

    # 무슨 조건으로 찾았는지 다시 보여준다
    conditions = []
    if args.category:
        conditions.append(f"카테고리={args.category}")
    if args.keyword:
        conditions.append(f"메모에 '{args.keyword}'")
    if getattr(args, "from_date", None):
        conditions.append(f"{args.from_date} 이후")
    if args.to:
        conditions.append(f"{args.to} 이전")
    print("조건: " + (", ".join(conditions) if conditions else "없음 (전체)"))

    print_table(records, "조건에 맞는 기록이 없습니다.")


def find_record(records, target_id):
    """번호로 기록 하나를 찾는다. 없으면 None."""
    for r in records:
        if r["id"] == target_id:
            return r
    return None


def format_record(r):
    """기록 하나를 한 줄 문자열로."""
    memo = f" / {r['memo']}" if r["memo"] else ""
    return f"{r['id']}번: {r['date']} / {r['amount']:,}원 / {r['category']}{memo}"


def cmd_delete(args):
    data = load_data()
    record = find_record(data["records"], args.id)

    if record is None:
        print(f"{args.id}번 기록이 없습니다. list 로 번호를 확인해 보세요.")
        return

    # 지우기 전에 보여주고 확인받는다 (SPEC 5번: 가장 아픈 사고를 막는 절차)
    print("아래 기록을 삭제합니다.")
    print("  " + format_record(record))
    answer = input("정말 지울까요? (y/n) ").strip().lower()

    if answer != "y":
        print("취소했습니다.")
        return

    data["records"].remove(record)
    save_data(data)
    print(f"{args.id}번을 삭제했습니다.")


def cmd_edit(args):
    data = load_data()
    record = find_record(data["records"], args.id)

    if record is None:
        print(f"{args.id}번 기록이 없습니다. list 로 번호를 확인해 보세요.")
        return

    # 바꿀 항목을 하나도 안 줬다면 알려주고 끝낸다
    changes = {
        "amount": args.amount,
        "category": args.category,
        "date": args.date,
        "memo": args.memo,
    }
    given = {k: v for k, v in changes.items() if v is not None}

    if not given:
        print("바꿀 내용을 하나 이상 지정해 주세요.")
        print("  예) python3 ledger.py edit 3 --amount 9000")
        return

    print("변경 전: " + format_record(record))
    for key, value in given.items():
        record[key] = value
    save_data(data)
    print("변경 후: " + format_record(record))


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

    p_del = sub.add_parser("delete", help="번호로 삭제")
    p_del.add_argument("id", type=int, help="삭제할 기록 번호")
    p_del.set_defaults(func=cmd_delete)

    p_edit = sub.add_parser("edit", help="번호로 수정")
    p_edit.add_argument("id", type=int, help="수정할 기록 번호")
    p_edit.add_argument("--amount", type=int, help="새 금액")
    p_edit.add_argument("--category", help="새 카테고리")
    p_edit.add_argument("--date", help="새 날짜 YYYY-MM-DD")
    p_edit.add_argument("--memo", help="새 메모")
    p_edit.set_defaults(func=cmd_edit)

    p_search = sub.add_parser("search", help="검색·필터")
    p_search.add_argument("--category", help="이 카테고리만")
    p_search.add_argument("--keyword", help="메모에 이 단어가 들어간 것만")
    p_search.add_argument("--from", dest="from_date",
                          help="이 날짜부터 YYYY-MM-DD")
    p_search.add_argument("--to", help="이 날짜까지 YYYY-MM-DD")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
