# 가계부 CLI (ledger)

터미널에서 지출을 한 줄로 기록하고, 찾아보고, 합계를 내는 개인 가계부.

무엇을 왜 만들었는지는 [SPEC.md](SPEC.md)를 보세요.

## 필요한 것

- Python 3.9 이상 (Mac에는 기본으로 있습니다: `python3 --version` 으로 확인)
- 설치할 라이브러리 없음. 표준 라이브러리만 씁니다.

## 실행 방법

```bash
cd sandbox/hyein
python3 ledger.py --help
```

`--help` 는 어느 명령 뒤에도 붙일 수 있습니다.

```bash
python3 ledger.py add --help
```

## 명령어

### 지출 추가

```bash
python3 ledger.py add 8500 식비 --memo "점심 김치찌개"
python3 ledger.py add 39000 생활용품 --date 2026-07-20 --memo "장보기"
```

금액과 카테고리는 필수, 날짜와 메모는 선택입니다. 날짜를 생략하면 오늘 날짜가 들어갑니다.

### 목록 보기

```bash
python3 ledger.py list
```

```
번호  날짜               금액  카테고리  메모
-----------------------------------------------------
   3  2026-07-28      4,800원  카페      아이스아메리카노
   2  2026-07-28      1,550원  교통      지하철
   1  2026-07-28      8,500원  식비      점심 김치찌개
-----------------------------------------------------
합계  3건            14,850원
```

### 수정 / 삭제

번호(맨 왼쪽 열)로 지목합니다.

```bash
python3 ledger.py edit 3 --amount 5000
python3 ledger.py edit 3 --category 식비 --memo "카페라떼"
python3 ledger.py delete 3
```

`delete` 는 지우기 전에 대상을 보여주고 `y/n` 을 물어봅니다.
`edit` 은 준 항목만 바꾸고 나머지는 그대로 둡니다.

### 검색

조건은 자유롭게 조합할 수 있습니다.

```bash
python3 ledger.py search --category 식비
python3 ledger.py search --keyword 커피
python3 ledger.py search --from 2026-07-01 --to 2026-07-15
python3 ledger.py search --category 식비 --from 2026-07-01
```

### 통계

```bash
python3 ledger.py stats              # 이번 달
python3 ledger.py stats --month 2026-06
```

```
[2026-07 지출 요약]

  생활용품    39,000원   72.4%  ██████████████
  식비         8,500원   15.8%  ███
  카페         4,800원    8.9%  ██

  총 지출   53,850원
  기록 건수 4건
  기록한 날 2일
  하루 평균 26,925원
```

### 카테고리 목록

```bash
python3 ledger.py categories
```

카테고리는 자유 입력이라 "식비"와 "밥값"이 따로 집계될 수 있습니다.
이 명령으로 확인하고 `edit` 으로 통일하세요.

## 데이터는 어디에 저장되나

`sandbox/hyein/data.json` 에 저장됩니다. 메모장으로 열어서 내용을 볼 수 있습니다.

이 파일은 `.gitignore` 에 등록되어 있어서 **Git에 올라가지 않습니다.**
이 레포가 public이라 개인 지출 내역이 공개되면 안 되기 때문입니다.

처음 실행하면 자동으로 만들어지므로 미리 준비할 필요는 없습니다.

## 알려진 한계

- 지출만 다룹니다. 수입과 잔액 계산은 없습니다.
- 예산 설정·초과 알림 없음.
- 여러 사람이 같이 쓸 수 없습니다. 한 사람 한 파일입니다.

의도적으로 뺀 것들입니다. 이유는 [SPEC.md](SPEC.md) 7번을 보세요.
