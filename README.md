# fly-ai-playground

> FLY AI 팀 · 에이전트 개발 친숙도 3일 집중 코스용 연습 레포

개발이 처음이어도 괜찮습니다. 이 레포는 **틀려도 되는 공간**입니다.
목표는 멋진 결과물이 아니라, 3일 뒤에 "에이전트로 개발하는 게 더 이상 낯설지 않다"가 되는 것입니다.

## 지금 뭘 하면 되나요

1. **진도 대시보드를 엽니다** → [팀 진도 보기](https://flyai-kfc.github.io/fly-ai-playground/)
   내가 오늘 할 일과 팀원들의 진척이 한 화면에 있습니다.
2. 오늘 날짜에 해당하는 가이드를 읽습니다 → [Day 1](guide/DAY1.md) · [Day 2](guide/DAY2.md) · [Day 3](guide/DAY3.md)
   (동건·정민은 [가이드용 안내](guide/가이드용.md)를 보세요 — 실습은 면제입니다)
3. 막히면 [Git 치트시트](guide/GIT-CHEATSHEET.md)와 [복붙용 프롬프트 모음](guide/PROMPTS.md)을 봅니다.
4. 그래도 30분 넘게 막히면 **팀 채널에 화면을 그대로 붙입니다.** 혼자 오래 헤매지 않는 게 규칙입니다.

## 처음 한 번만 하는 준비

```bash
git clone https://github.com/flyai-kfc/fly-ai-playground.git
cd fly-ai-playground
claude          # 또는 Cowork에서 이 폴더를 열기
```

그리고 Claude에게 이렇게 말해 보세요.

```
이 레포는 에이전트 개발 연습용 샌드박스야. CLAUDE.md를 읽고,
내가 오늘 뭘 해야 하는지 guide/DAY1.md 기준으로 안내해줘.
나는 개발이 처음이니까 한 번에 한 단계씩 알려줘.
```

## 규칙 세 줄

- 자기 폴더(`sandbox/<이름>/`) 안에서 작업하고, 브랜치를 파서 PR로 올립니다.
- PR 본문에 **왜 이렇게 했는지**를 씁니다.
- 이 레포는 public입니다. **키·비밀번호는 절대 커밋 금지.**
