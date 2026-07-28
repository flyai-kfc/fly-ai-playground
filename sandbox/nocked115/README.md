# 가계부 기록기

개인용 CLI 가계부. 자세한 요구사항은 [SPEC.md](./SPEC.md) 참고.

## 실행 방법

Python이 설치되어 있어야 합니다 (버전 확인: `python --version`).

```
cd sandbox/nocked115
python ledger.py add       # 기록 추가 (대화형으로 하나씩 물어봄)
python ledger.py list      # 전체 내역 조회
python ledger.py summary   # 월별 합계 + 카테고리별 지출 합계
```

`add`를 실행하면 날짜·종류·카테고리·금액·메모를 하나씩 물어보고,
`data/ledger.csv`에 한 줄로 저장합니다. `add`는 입력을 기다리는 대화형 명령이라
실제 터미널에서 실행해야 합니다 (`list`, `summary`는 바로 결과만 출력).

## 참고

- 데이터는 `data/ledger.csv`에 저장되며, 개인 데이터라 Git에 커밋되지 않도록
  `.gitignore`에 등록되어 있습니다.
- 카테고리는 정해진 목록 없이 자유롭게 입력합니다 (예: 식비, 교통, 월급).
- 날짜는 `YYYY-MM-DD` 형식만 허용하며, 비워두면 오늘 날짜로 저장됩니다.

## 구현 상태

- [x] 1단계: 폴더 구조 (`ledger.py`, `data/`, `README.md`)
- [x] 2단계: CSV 읽기/쓰기 기본 함수
- [x] 3단계: `add` 명령 (기록 추가)
- [x] 4단계: `list` 명령 (전체 내역 조회)
- [x] 5단계: `summary` 명령 (월별·카테고리별 합계)
