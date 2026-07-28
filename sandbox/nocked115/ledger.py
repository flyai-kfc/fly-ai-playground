"""가계부 기록기 (CLI)

사용법: python ledger.py add   (list/summary는 다음 단계에서 추가됩니다)
"""
import csv
import datetime
import os
import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "ledger.csv")
FIELDNAMES = ["date", "type", "category", "amount", "memo"]


def ensure_data_file():
    """데이터 파일이 없으면 헤더와 함께 새로 만든다."""
    if not os.path.exists(DATA_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def read_records():
    """CSV에 저장된 모든 기록을 딕셔너리 리스트로 읽어온다."""
    ensure_data_file()
    with open(DATA_FILE, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def append_record(record):
    """새 기록 한 줄을 CSV 끝에 추가한다."""
    ensure_data_file()
    with open(DATA_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(record)


def ask_type():
    """income 또는 expense 중 하나가 입력될 때까지 반복해서 물어본다."""
    value = input("종류 (income=수입 / expense=지출): ").strip()
    while value not in ("income", "expense"):
        value = input("income 또는 expense만 입력해주세요: ").strip()
    return value


def ask_amount():
    """양의 정수가 입력될 때까지 반복해서 물어본다."""
    while True:
        value = input("금액 (숫자만, 원 단위): ").strip()
        if value.isdigit() and int(value) > 0:
            return value
        print("금액은 0보다 큰 숫자로 입력해주세요.")


def ask_date():
    """빈 값(오늘 날짜) 또는 YYYY-MM-DD 형식이 입력될 때까지 반복해서 물어본다."""
    value = input("날짜 (YYYY-MM-DD, 그냥 Enter면 오늘 날짜): ").strip()
    while value:
        try:
            return datetime.date.fromisoformat(value).isoformat()
        except ValueError:
            value = input("날짜 형식이 올바르지 않아요. YYYY-MM-DD로 입력하거나 그냥 Enter를 눌러주세요: ").strip()
    return datetime.date.today().isoformat()


def cmd_add():
    """사용자에게 하나씩 물어봐서 기록 한 줄을 추가한다."""
    record = {
        "date": ask_date(),
        "type": ask_type(),
        "category": input("카테고리 (예: 식비, 교통, 월급): ").strip(),
        "amount": ask_amount(),
        "memo": input("메모 (선택, 그냥 Enter 가능): ").strip(),
    }
    append_record(record)
    print(f"저장했습니다: {record['date']} | {record['type']} | {record['category']} | {record['amount']}원 | {record['memo']}")


def cmd_list():
    """저장된 모든 기록을 날짜순으로 표처럼 출력한다."""
    records = sorted(read_records(), key=lambda r: r["date"])
    if not records:
        print("아직 기록이 없습니다. python ledger.py add 로 먼저 추가해보세요.")
        return

    print(f"{'날짜':<12}{'종류':<8}{'카테고리':<10}{'금액':>10}  메모")
    print("-" * 50)
    for r in records:
        type_kr = "수입" if r["type"] == "income" else "지출"
        amount = f"{int(r['amount']):,}"
        print(f"{r['date']:<12}{type_kr:<8}{r['category']:<10}{amount:>10}  {r['memo']}")


def cmd_summary():
    """월별 수입/지출 합계와, 카테고리별 지출 합계를 출력한다."""
    records = read_records()
    if not records:
        print("아직 기록이 없습니다. python ledger.py add 로 먼저 추가해보세요.")
        return

    monthly = {}
    category_expense = {}
    for r in records:
        month = r["date"][:7]
        amount = int(r["amount"])
        monthly.setdefault(month, {"income": 0, "expense": 0})
        monthly[month][r["type"]] += amount
        if r["type"] == "expense":
            category_expense[r["category"]] = category_expense.get(r["category"], 0) + amount

    print("== 월별 합계 ==")
    for month in sorted(monthly):
        income = monthly[month]["income"]
        expense = monthly[month]["expense"]
        print(f"{month}  수입 {income:,}원 / 지출 {expense:,}원")

    print()
    print("== 카테고리별 지출 합계 ==")
    for cat, total in sorted(category_expense.items(), key=lambda item: -item[1]):
        print(f"{cat:<10}{total:,}원")


def main():
    if len(sys.argv) < 2:
        print("사용법: python ledger.py [add|list|summary]")
        return

    command = sys.argv[1]
    if command == "add":
        cmd_add()
    elif command == "list":
        cmd_list()
    elif command == "summary":
        cmd_summary()
    else:
        print(f"알 수 없는 명령입니다: {command} (add / list / summary 중 하나를 입력해주세요)")


if __name__ == "__main__":
    main()
