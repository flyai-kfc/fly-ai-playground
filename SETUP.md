# 운영자용 셋업 (동건님 전용)

한 번만 하면 됩니다. 전부 합쳐 10~15분.

---

## 1. 설정 확인 — 대부분 이미 채워져 있습니다

**`docs/index.html`** 맨 위 `course-config` 블록에 조직명과 팀원 5명이 이미 들어가 있습니다.

```json
{
  "owner": "flyai-kfc",
  "repo": "fly-ai-playground",
  "startDate": "2026-07-28",
  "members": [
    { "login": "nocked115",  "name": "이수현", "role": "learner", "aliases": [] },
    { "login": "hyeineom12", "name": "엄혜인", "role": "learner", "aliases": [] },
    { "login": "hhseo9519",  "name": "서현호", "role": "learner", "aliases": [] },
    { "login": "GunderGie",  "name": "김동건", "role": "guide", "skip": true, "aliases": [] },
    { "login": "mintoly31",  "name": "정민",   "role": "guide", "skip": true, "aliases": [] }
  ]
}
```

**바꿔야 할 것은 하나뿐입니다 — `startDate`를 실제 시작일로.** 지금은 2026-07-28로 잡혀 있습니다.
이 날짜를 기준으로 "오늘이 Day 몇인지"와 페이스 판정(빠름/느림)이 계산됩니다.

- `role: "guide"` + `skip: true` → 동건·정민은 **실습 면제**입니다. 진도판에서 역량 미터 대신
  리뷰·이슈·커밋 수만 보여주고, 팀 전체 진도와 평가 대상에서 빠집니다.
  직접 참여하고 싶으면 `"skip": false`로 바꾸면 됩니다.
- `aliases`는 각자 `git config user.name` 값입니다. 지금은 비어 있어도 됩니다 —
  GitHub 로그인으로 매칭되고, 안 맞는 사람이 있으면 점검 보고가
  "매칭되지 않은 커밋 작성자"로 알려줍니다. 그때 채우면 됩니다.
- **이 블록이 팀원 정보의 단일 소스**입니다. 대시보드·Actions·점검 스크립트가 전부 여기만 읽습니다.

---

## 2. 레포를 만들고 올립니다

```bash
cd fly-ai-playground
git init -b main
git add -A
git commit -m "chore: 연습 레포 초기 셋업"

# public으로 생성 (샌드박스라 시크릿이 없고, Pages와 진도 스냅샷이 무료로 동작합니다)
gh repo create flyai-kfc/fly-ai-playground --public --source=. --push
```

`gh`가 없다면 GitHub 웹에서 빈 public 레포를 만든 뒤:

```bash
git remote add origin https://github.com/flyai-kfc/fly-ai-playground.git
git push -u origin main
```

---

## 3. GitHub Pages를 켭니다

레포 **Settings → Pages → Source: Deploy from a branch → Branch: `main` / 폴더: `/docs`** → Save.

1~2분 뒤 `https://flyai-kfc.github.io/fly-ai-playground/` 에서 진도판이 열립니다.

---

## 4. Actions 쓰기 권한 (셋 중 하나만 하면 됩니다)

진도 스냅샷 워크플로우가 `docs/activity.json`을 커밋해야 해서 쓰기 권한이 필요합니다.

### 방법 A — 조직 설정에서 허용 (권장)

**레포 설정이 아니라 조직 설정입니다.** 조직 기본값이 읽기 전용이면 레포 화면의 라디오 버튼이
회색으로 비활성화되어 아무리 눌러도 안 바뀝니다. GitHub 문서에 명시된 동작입니다 —
*"조직 기본값을 제한적으로 두면 조직 내 저장소에도 같은 옵션이 선택되고 허용적인 옵션은 비활성화된다."*

→ https://github.com/organizations/flyai-kfc/settings/actions
→ **Workflow permissions → "Read and write permissions"** 선택 → Save

그다음 레포 Settings → Actions → General에서 같은 옵션이 선택 가능해집니다.

### 방법 B — PAT로 우회 (조직 정책을 못 바꿀 때)

조직 소유자가 아니거나 정책이 상위에서 강제되는 경우입니다. 워크플로우가 `SNAPSHOT_TOKEN`
시크릿이 있으면 그걸 먼저 쓰도록 되어 있습니다. PAT는 조직의 GITHUB_TOKEN 정책과 무관합니다.

1. https://github.com/settings/personal-access-tokens/new 에서 **fine-grained PAT** 생성
   - Resource owner: `flyai-kfc`
   - Repository access: **Only select repositories** → `fly-ai-playground`
   - Repository permissions: **Contents → Read and write** (이것 하나면 충분)
   - 만료일은 코스 기간보다 조금 길게 (예: 30일)
2. 레포 **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `SNAPSHOT_TOKEN`
   - Secret: 방금 만든 토큰
3. Actions 탭에서 워크플로우를 다시 실행

### 방법 C — 그냥 건너뛰기

둘 다 안 되면 **워크플로우를 꺼도 됩니다.** 진도판이 스냅샷이 없는 걸 감지하면
GitHub API를 직접 읽는 모드로 자동 전환됩니다. 기능은 똑같습니다.

다만 인증 없는 조회는 **IP당 시간당 60회** 제한이 있고, 한 번 열 때 8회를 씁니다.
같은 사무실 WiFi를 쓰면 5명이 IP 하나를 공유하니 빠듯할 수 있어서, 이 모드에서는
자동 새로고침 간격이 20분으로 늘어나고 탭이 안 보일 때는 아예 쉽니다.
한도에 걸리면 안내와 함께 토큰 입력칸이 나타납니다(브라우저 메모리에만 두고 저장하지 않습니다).

---

권한이 준비되면 **Actions 탭 → "진도 스냅샷" → Run workflow**로 한 번 수동 실행하세요.
성공하면 `docs/activity.json`이 커밋되고 진도판에 팀원 카드가 뜹니다.

> 이 워크플로우가 진도판의 심장입니다. 30분마다, 그리고 PR·이슈·리뷰가 생길 때마다 돌면서
> 팀원별 활동을 모아둡니다. 대시보드는 이 파일 하나만 읽으므로 조회 한도 걱정이 없습니다.
> push에 실패하면 워크플로우 로그에 위 해결책이 그대로 출력됩니다.

---

## 5. 팀원을 초대하고 진도 이슈를 만듭니다

조직이니까 **팀(Team)으로 한 번에 초대하는 게 낫습니다.** 나중에 본 프로덕션 레포가
생기면 팀에 레포만 추가하면 되고, 사람이 바뀌어도 한 곳만 고치면 됩니다.

1. https://github.com/orgs/flyai-kfc/new-team 에서 팀 생성 (예: `fly-ai`)
2. 팀 페이지 → **Add a member**로 4명 초대 — 초대받은 사람이 **조직 초대를 먼저 수락**해야 팀에 들어옵니다
3. 레포 **Settings → Collaborators and teams → Add teams** → `fly-ai` → 권한 **Write**

개인별로 붙이려면 같은 화면의 **Add people**를 쓰면 됩니다. 어느 쪽이든 동작은 같습니다.

**진도 이슈는 학습자 본인이 만들게 하세요.** 절차는 6번의 초대 메시지에 들어 있습니다.
첫 GitHub 조작 경험이 되고, 제목 형식을 맞추면서 "규칙대로 쓰면 시스템이 알아본다"는 감각도 생깁니다.

- 제목이 `[진도] nocked115` 형식이어야 대시보드가 체크박스를 읽습니다. 첫날 아침에 세 명 것을 한 번 확인해 주세요.
- 가이드 2명은 실습 면제라 진도 이슈가 필요 없습니다.
- 급하면 운영자가 대신 만들어도 됩니다: Issues → New issue → "진도 체크리스트" 템플릿.

---

## 6. 팀원에게 공유할 메시지 (그대로 복사해서 쓰세요)

```
내일부터 3일간 에이전트 개발에 익숙해지는 시간을 갖습니다.
개발 경험 없어도 전혀 문제 없어요. 오히려 그런 분들을 위한 시간입니다.

진도판: https://flyai-kfc.github.io/fly-ai-playground/
레포:   https://github.com/flyai-kfc/fly-ai-playground

시작 전 준비 (15분):

1. GitHub 조직 초대 메일을 수락해주세요 (제목: flyai-kfc)

2. git이 설치돼 있는지 확인 — 터미널에 git --version
   없으면 https://git-scm.com 에서 설치

3. 레포를 내 컴퓨터로 복사
   git clone https://github.com/flyai-kfc/fly-ai-playground.git

4. 그 폴더에서 claude 실행 (또는 Cowork에서 폴더 열기)

5. 내 진도 체크리스트 이슈 만들기 ← 이것도 꼭 해주세요
   - 레포 → 위쪽 Issues 탭 → 초록색 New issue 버튼
   - "진도 체크리스트" 옆의 Get started 클릭
   - 제목을 [진도] 내깃허브아이디 로 바꾸기
     예) [진도] nocked115
     ※ 대괄호와 아이디 철자가 정확해야 진도판이 인식합니다
   - 본문은 그대로 두고 Create 클릭

   3일 동안 항목을 끝낼 때마다 이 이슈에서 [ ]를 [x]로 바꾸시면 됩니다.
   (이슈 우측 상단 연필 아이콘 → 체크박스 클릭 → Save)
   진도판에 바로 반영됩니다.

첫날 목표는 딱 하나입니다 — 아주 작은 걸 하나 만들어서 올려보기.
막히면 30분 넘기지 말고 바로 채널에 화면 붙여주세요. 그게 규칙입니다.
```

> 이슈를 본인이 직접 만들게 하는 게 좋습니다. 첫 GitHub 조작 경험이 되고,
> 제목 형식을 맞추면서 "규칙대로 쓰면 시스템이 알아본다"는 감각도 생깁니다.
> 대신 첫날 아침에 세 명의 이슈 제목이 정확한지 한 번 확인해 주세요.

---

## 7. 진행 중 점검

하루 2회(점심·저녁) 자동 점검이 돌면서 진척을 평가해 알려줍니다. 수동으로 보고 싶으면:

```bash
python3 tools/checkup.py --owner flyai-kfc
```

평가 결과를 진도판에 띄우려면 `docs/evaluation.json`을 갱신하고 push하면 됩니다.
(자동 점검이 갱신할 내용을 만들어 주므로, 붙여넣고 push만 하면 됩니다.)

```json
{
  "updatedAt": "2026-07-28 18:30",
  "day": 1,
  "verdict": "Day 1 게이트 미달 1명. 내일 오전을 보강 시간으로 쓰는 것을 권합니다.",
  "summary": "전체 상황 두세 문장",
  "members": [
    { "login": "aaa", "status": "지금 어떤 상태인지", "next": "다음에 뭘 시키면 좋은지" }
  ]
}
```

---

## 자주 막히는 곳

| 증상 | 원인과 해결 |
|---|---|
| 진도판이 "불러오기 실패" | `course-config`의 owner/repo 오타, 또는 레포가 private |
| 모든 팀원이 커밋 0 | `aliases`에 각자의 `git config user.name` 값이 빠짐 |
| 워크플로우가 push에서 403 | 조직 설정에서 쓰기 허용, 또는 `SNAPSHOT_TOKEN` 등록 (4번 단계) |
| 레포 설정의 권한 라디오가 회색 | 조직 기본값이 잠근 것. 조직 설정에서 바꿔야 함 (4-A) |
| 진도판이 "직접 조회 모드" | 스냅샷이 아직 없음. 정상 동작이며 그대로 써도 됨 |
| 체크박스를 체크했는데 반영 안 됨 | 이슈 제목이 `[진도] <깃허브아이디>` 형식이 아님 |
| Pages 404 | Pages 소스가 `/docs`가 아니라 `/`로 설정됨 |
