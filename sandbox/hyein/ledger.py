# -*- coding: utf-8 -*-
"""


# --- 변경 이력 (Day 2 공동 작업) ---
# 각자 자기 줄을 이 블록 맨 아래에 추가합니다.
# 2026-07-29 hyein: stats 에 '가장 많이 쓴 카테고리' 한 줄 추가

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

# 이 .py 파일이 있는 폴더 안의 data.json 을 가리킨다.
# 이렇게 해두면 어느 폴더에서 실행하든 항상 같은 파일을 쓴다.
DATA_FILE = Path(__file__).parent / "data.json"

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check_date(value):
    """날짜 형식이 YYYY-MM-DD 인지 확인. 아니면 안내하고 종료."""
    if value is None:
        return None
    if not DATE_PATTERN.match(value):
        print(f"날짜 형식이 올바르지 않습니다: '{value}'")
        print("  YYYY-MM-DD 형식으로 써 주세요. 예) 2026-07-28")
        sys.exit(1)
    return value


class Store:
    """data.json 파일 하나를 읽고 쓰는 역할만 담당한다."""

    def __init__(self, path):
        self.path = path

    def load(self):
        if not self.path.exists():
            return {"next_id": 1, "records": []}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            # ensure_ascii=False : 한글이 \uXXXX 로 깨지지 않게
            # indent=2          : 사람이 눈으로 읽을 수 있게 줄 맞춰서
            json.dump(data, f, ensure_ascii=False, indent=2)


class Ledger:
    """기록 목록에 대한 조회·추가·수정·삭제를 담당한다. 저장은 Store에 위임한다."""

    def __init__(self, store):
        self.store = store
        self.data = store.load()

    @property
    def records(self):
        return self.data["records"]

    def save(self):
        self.store.save(self.data)

    def existing_categories(self):
        return sorted({r["category"] for r in self.records})

    def is_first_use(self, category):
        used = [r["category"] for r in self.records]
        return used.count(category) == 1

    def add(self, amount, category, date_str=None, memo=None):
        record = {
            "id": self.data["next_id"],
            "date": check_date(date_str) or date.today().isoformat(),
            "amount": amount,
            "category": category,
            "memo": memo or "",
        }
        self.records.append(record)
        self.data["next_id"] += 1
        self.save()
        return record

    def find(self, target_id):
        for r in self.records:
            if r["id"] == target_id:
                return r
        return None

    def delete(self, target_id):
        record = self.find(target_id)
        if record is None:
            return None
        self.records.remove(record)
        self.save()
        return record

    def edit(self, target_id, **changes):
        record = self.find(target_id)
        if record is None:
            return None, {}
        given = {k: v for k, v in changes.items() if v is not None}
        if not given:
            return record, given
        for key, value in given.items():
            record[key] = value
        self.save()
        return record, given

    def search(self, category=None, keyword=None, from_date=None, to_date=None):
        records = self.records
        if category:
            records = [r for r in records if r["category"] == category]
        if keyword:
            kw = keyword.lower()
            records = [r for r in records if kw in r["memo"].lower()]
        # 날짜는 YYYY-MM-DD 형식이라 문자열끼리 비교해도 순서가 맞다
        if from_date:
            records = [r for r in records if r["date"] >= from_date]
        if to_date:
            records = [r for r in records if r["date"] <= to_date]
        return records

    def month_records(self, month):
        # 날짜가 "2026-07-28" 이므로 앞 7글자가 "2026-07" 이다
        return [r for r in self.records if r["date"].startswith(month)]

    def category_counts(self):
        counts = {}
        for r in self.records:
            counts[r["category"]] = counts.get(r["category"], 0) + 1
        return counts


class Display:
    """터미널 출력(폭 계산, 정렬, 표 그리기)만 담당하는 헬퍼 모음."""

    @staticmethod
    def width(text):
        """터미널에서 이 문자열이 차지하는 칸 수.

        한글·한자는 영문의 두 배 폭으로 그려지는데 파이썬은 한 글자로 세기 때문에,
        len() 을 그대로 쓰면 표가 삐뚤어진다.
        """
        total = 0
        for ch in str(text):
            # 'W'(Wide), 'F'(Fullwidth) 는 두 칸을 차지한다
            total += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        return total

    @classmethod
    def pad(cls, text, n, align="left"):
        """폭 n 칸에 맞춰 공백을 채운다. 한글이 섞여도 맞는다."""
        text = str(text)
        space = " " * max(0, n - cls.width(text))
        return space + text if align == "right" else text + space

    @staticmethod
    def format_record(r):
        """기록 하나를 한 줄 문자열로."""
        memo = f" / {r['memo']}" if r["memo"] else ""
        return f"{r['id']}번: {r['date']} / {r['amount']:,}원 / {r['category']}{memo}"

    @classmethod
    def print_table(cls, records, empty_message="기록이 없습니다."):
        """기록 목록을 표로 찍고 합계를 보여준다. list 와 search 가 같이 쓴다."""
        if not records:
            print(empty_message)
            return

        # 최신 날짜가 위로 오도록 정렬 (날짜가 같으면 나중에 넣은 게 위로)
        records = sorted(records, key=lambda r: (r["date"], r["id"]), reverse=True)

        # 카테고리 열 폭은 가장 긴 카테고리에 맞춘다 (최소 8칸)
        cat_w = max([8] + [cls.width(r["category"]) for r in records])

        print(cls.pad("번호", 4, "right") + "  " + cls.pad("날짜", 11) + " "
              + cls.pad("금액", 11, "right") + "  " + cls.pad("카테고리", cat_w) + "  메모")
        print("-" * (4 + 2 + 11 + 1 + 11 + 2 + cat_w + 2 + 12))

        for r in records:
            print(cls.pad(r["id"], 4, "right") + "  " + cls.pad(r["date"], 11) + " "
                  + cls.pad(f"{r['amount']:,}원", 11, "right") + "  "
                  + cls.pad(r["category"], cat_w) + "  " + r["memo"])

        print("-" * (4 + 2 + 11 + 1 + 11 + 2 + cat_w + 2 + 12))
        total = sum(r["amount"] for r in records)
        print(cls.pad("합계", 4, "right") + "  " + cls.pad(f"{len(records)}건", 11) + " "
              + cls.pad(f"{total:,}원", 11, "right"))


def _new_ledger():
    return Ledger(Store(DATA_FILE))


# ---------- 명령별 동작 ----------

def cmd_add(args):
    ledger = _new_ledger()

    # 오타로 카테고리가 갈라지는 걸 줄이려고, 이미 쓰던 목록을 먼저 보여준다
    existing = ledger.existing_categories()
    if existing:
        print("기존 카테고리: " + ", ".join(existing))

    record = ledger.add(args.amount, args.category, args.date, args.memo)

    print(f"{record['id']}번으로 저장했습니다. "
          f"{record['date']} / {record['amount']:,}원 / {record['category']}")

    # 이 카테고리를 처음 쓰는 거라면 알려준다 (SPEC 6번)
    if ledger.is_first_use(args.category):
        print(f"※ '{args.category}'는 처음 쓰는 카테고리입니다.")


def cmd_list(args):
    ledger = _new_ledger()
    Display.print_table(ledger.records, "아직 기록이 없습니다. add 로 추가해 보세요.")


def cmd_search(args):
    ledger = _new_ledger()
    from_date = getattr(args, "from_date", None)
    records = ledger.search(
        category=args.category,
        keyword=args.keyword,
        from_date=from_date,
        to_date=args.to,
    )

    # 무슨 조건으로 찾았는지 다시 보여준다
    conditions = []
    if args.category:
        conditions.append(f"카테고리={args.category}")
    if args.keyword:
        conditions.append(f"메모에 '{args.keyword}'")
    if from_date:
        conditions.append(f"{from_date} 이후")
    if args.to:
        conditions.append(f"{args.to} 이전")
    print("조건: " + (", ".join(conditions) if conditions else "없음 (전체)"))

    Display.print_table(records, "조건에 맞는 기록이 없습니다.")


def cmd_delete(args):
    ledger = _new_ledger()
    record = ledger.find(args.id)

    if record is None:
        print(f"{args.id}번 기록이 없습니다. list 로 번호를 확인해 보세요.")
        return

    # 지우기 전에 보여주고 확인받는다 (SPEC 5번: 가장 아픈 사고를 막는 절차)
    print("아래 기록을 삭제합니다.")
    print("  " + Display.format_record(record))
    answer = input("정말 지울까요? (y/n) ").strip().lower()

    if answer != "y":
        print("취소했습니다.")
        return

    ledger.delete(args.id)
    print(f"{args.id}번을 삭제했습니다.")


def cmd_edit(args):
    ledger = _new_ledger()
    record = ledger.find(args.id)

    if record is None:
        print(f"{args.id}번 기록이 없습니다. list 로 번호를 확인해 보세요.")
        return

    changes = {
        "amount": args.amount,
        "category": args.category,
        "date": check_date(args.date),
        "memo": args.memo,
    }
    given = {k: v for k, v in changes.items() if v is not None}

    # 바꿀 항목을 하나도 안 줬다면 알려주고 끝낸다
    if not given:
        print("바꿀 내용을 하나 이상 지정해 주세요.")
        print("  예) python3 ledger.py edit 3 --amount 9000")
        return

    print("변경 전: " + Display.format_record(record))
    ledger.edit(args.id, **given)
    print("변경 후: " + Display.format_record(record))


def cmd_stats(args):
    ledger = _new_ledger()

    # 기준 달을 정한다. --month 를 안 주면 이번 달.
    month = args.month or date.today().strftime("%Y-%m")
    target = ledger.month_records(month)

    print(f"[{month} 지출 요약]")

    if not target:
        print("이 달에는 기록이 없습니다.")
        return

    total = sum(r["amount"] for r in target)

    # 카테고리별로 금액을 더한다
    by_category = {}
    for r in target:
        by_category[r["category"]] = by_category.get(r["category"], 0) + r["amount"]

    # 많이 쓴 카테고리가 위로 오게 정렬
    ordered = sorted(by_category.items(), key=lambda pair: pair[1], reverse=True)

    cat_w = max([8] + [Display.width(c) for c, _ in ordered])

    print()
    for category, amount in ordered:
        share = amount / total * 100
        bar = "█" * round(share / 5)   # 5%당 한 칸
        print("  " + Display.pad(category, cat_w) + " " + Display.pad(f"{amount:,}원", 11, "right")
              + f"  {share:5.1f}%  {bar}")

    # 며칠에 걸쳐 썼는지 (기록이 있는 날의 수)
    days_used = len({r["date"] for r in target})

    print()
    print(f"  총 지출   {total:,}원")
    print(f"  기록 건수 {len(target)}건")
    print(f"  기록한 날 {days_used}일")
    print(f"  하루 평균 {round(total / days_used):,}원")

    top_category, top_amount = ordered[0]
    print(f"  최다 지출 {top_category} ({top_amount:,}원)")


def cmd_categories(args):
    ledger = _new_ledger()

    if not ledger.records:
        print("아직 기록이 없어서 카테고리도 없습니다.")
        return

    counts = ledger.category_counts()
    ordered = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
    cat_w = max([8] + [Display.width(c) for c, _ in ordered])

    print("지금까지 쓴 카테고리")
    for category, count in ordered:
        print("  " + Display.pad(category, cat_w) + f" {count}건")
    print()
    print("※ 비슷한 이름이 따로 보이면(예: 식비/밥값) edit 로 통일해 두세요.")
    print("  통일해야 stats 집계가 정확해집니다.")


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

    p_stats = sub.add_parser("stats", help="통계 요약")
    p_stats.add_argument("--month", help="YYYY-MM (생략하면 이번 달)")
    p_stats.set_defaults(func=cmd_stats)

    p_cat = sub.add_parser("categories", help="쓰고 있는 카테고리 목록")
    p_cat.set_defaults(func=cmd_categories)

    args = parser.parse_args()
    args.func(args)