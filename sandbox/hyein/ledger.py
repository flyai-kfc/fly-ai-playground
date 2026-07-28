"""가계부 CLI - 1단계: 명령어를 받아들이는 뼈대

아직 저장은 하지 않습니다. 입력을 제대로 받았는지 화면에 찍어보기만 합니다.
"""

import argparse
from datetime import date


def cmd_add(args):
    """add 명령이 들어왔을 때 실행되는 함수."""
    # 날짜를 안 주면 오늘 날짜를 쓴다
    when = args.date or date.today().isoformat()

    print("[add] 이렇게 받았습니다:")
    print(f"  날짜     : {when}")
    print(f"  금액     : {args.amount:,}원")
    print(f"  카테고리 : {args.category}")
    print(f"  메모     : {args.memo or '(없음)'}")
    print("\n※ 아직 저장 기능은 없습니다. 2단계에서 붙입니다.")


def cmd_list(args):
    """list 명령이 들어왔을 때 실행되는 함수."""
    print("[list] 아직 저장된 게 없습니다. 2단계에서 붙입니다.")


def main():
    # 프로그램 전체를 설명하는 파서(해석기)를 만든다
    parser = argparse.ArgumentParser(
        prog="ledger",
        description="터미널에서 쓰는 개인 가계부",
    )

    # add, list 처럼 여러 하위 명령을 두겠다고 선언
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- add 명령 ----
    p_add = sub.add_parser("add", help="지출 추가")
    p_add.add_argument("amount", type=int, help="금액 (원 단위, 정수)")
    p_add.add_argument("category", help="카테고리 (예: 식비, 교통)")
    p_add.add_argument("--date", help="날짜 YYYY-MM-DD (생략하면 오늘)")
    p_add.add_argument("--memo", help="짧은 설명")
    p_add.set_defaults(func=cmd_add)

    # ---- list 명령 ----
    p_list = sub.add_parser("list", help="전체 목록 보기")
    p_list.set_defaults(func=cmd_list)

    # 실제로 터미널에서 들어온 값을 해석한다
    args = parser.parse_args()
    # 위에서 set_defaults로 지정해둔 함수를 호출한다
    args.func(args)


# 이 파일을 직접 실행했을 때만 main()을 돌린다
if __name__ == "__main__":
    main()
