#!/usr/bin/env python3
"""
연습 레포의 진척을 점검해 한 화면 리포트로 출력합니다.
예약 점검 세션이 이 스크립트를 돌린 뒤, 출력을 근거로 정성 평가를 씁니다.

레포를 git clone해서 분석하므로 GitHub API 접근 권한이 필요 없습니다.
PR·리뷰·체크리스트처럼 git만으로는 알 수 없는 정보는 GitHub Actions가
만들어 둔 docs/activity.json에서 읽습니다. (없으면 git 데이터만으로 동작)

사용법:
    python3 tools/checkup.py --owner <OWNER>
    python3 tools/checkup.py --owner <OWNER> --json
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone

UNIT = "\x1f"
KST = timezone(timedelta(hours=9))

# 역량 점수는 "PR 하나 머지 + 충돌 한 번"이면 금방 포화되므로,
# 페이스 판정에는 체크리스트 진행률을 절반 섞어 해상도를 높인다.
# 아래 값은 각 Day가 끝난 시점의 기대 blended 값.
MILESTONES = [0, 48, 73, 100]
DAY_START, DAY_END = 9.5, 17.5


def blended(overall, checklist):
    done = sum(checklist[str(d)][0] for d in (1, 2, 3))
    total = sum(checklist[str(d)][1] for d in (1, 2, 3))
    if not total:
        return overall
    return round((overall + done / total * 100) / 2)


def course_position(start_date):
    """코스 시작일 기준으로 (현재 Day, 경과 지점 0~3)을 반환."""
    if not start_date:
        return 1, 0.0
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=KST)
    except ValueError:
        return 1, 0.0
    now = datetime.now(KST)
    day_idx = (now.date() - start.date()).days
    h = now.hour + now.minute / 60
    frac = max(0.0, min(1.0, (h - DAY_START) / (DAY_END - DAY_START)))
    c = max(0, min(2, day_idx))
    return c + 1, max(0.0, min(3.0, c + frac))


def expected_score(elapsed):
    i = int(elapsed)
    if i >= 3:
        return MILESTONES[3]
    return MILESTONES[i] + (MILESTONES[i + 1] - MILESTONES[i]) * (elapsed - i)


def pace_of(overall, elapsed):
    if elapsed < 0.2:
        return None, 0
    d = round(overall - expected_score(elapsed))
    if d >= 15:
        return "빠름", d
    if d <= -15:
        return "느림", d
    return "정상", d


def run(cmd, cwd=None):
    """git 출력을 읽는다.

    Windows에서는 subprocess가 로케일 코덱(한국어 환경이면 cp949)으로 디코딩하려다
    한글 커밋 메시지에서 UnicodeDecodeError를 낸다. git은 UTF-8로 출력하므로
    encoding을 명시하고, 깨지는 문자는 버리지 말고 대체한다.
    """
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True,
                           encoding="utf-8", errors="replace")
    except FileNotFoundError:
        sys.exit("git을 찾을 수 없습니다. git이 설치되어 있고 PATH에 있는지 확인하세요.")
    if p.returncode != 0:
        return ""
    return p.stdout or ""


def ensure_clone(owner, repo, workdir, source=None):
    url = source or "https://github.com/%s/%s.git" % (owner, repo)
    path = os.path.join(workdir, repo)
    if os.path.isdir(os.path.join(path, ".git")):
        run(["git", "fetch", "--all", "--prune", "--quiet"], cwd=path)
    else:
        os.makedirs(workdir, exist_ok=True)
        try:
            p = subprocess.run(
                ["git", "clone", "--no-single-branch", "--quiet", url, path],
                capture_output=True, encoding="utf-8", errors="replace")
        except FileNotFoundError:
            sys.exit("git을 찾을 수 없습니다. git이 설치되어 있고 PATH에 있는지 확인하세요.")
        if p.returncode != 0:
            sys.exit("레포를 클론하지 못했습니다. public인지, 이름이 맞는지 확인하세요.\n"
                     + (p.stderr or "").strip())
    return path


def main_branch(path):
    for ref in ("origin/main", "origin/master"):
        if run(["git", "rev-parse", "--verify", "--quiet", ref], cwd=path).strip():
            return ref
    return "HEAD"


def load_members(path):
    idx = os.path.join(path, "docs", "index.html")
    if not os.path.isfile(idx):
        sys.exit("docs/index.html이 없습니다. 대시보드가 레포에 올라가 있는지 확인하세요.")
    html = open(idx, encoding="utf-8").read()
    block = re.search(r'id="course-config"[^>]*>(.*?)</script>', html, re.S)
    if not block:
        sys.exit("docs/index.html에서 course-config 설정을 찾지 못했습니다.")
    cfg = json.loads(block.group(1))
    if not cfg.get("members"):
        sys.exit("course-config에 팀원이 비어 있습니다.")
    return cfg


def build_alias(members):
    alias = {}
    for m in members:
        for k in [m["login"], m.get("name", "")] + list(m.get("aliases") or []):
            if k:
                alias[str(k).lower()] = m["login"]
    return alias


def main():
    # Windows 콘솔(cp949)은 이 스크립트가 쓰는 기호·한글 일부를 인코딩하지 못해
    # 출력 단계에서 죽는다. 표준 출력을 UTF-8로 바꾸고, 안 되는 문자는 대체한다.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True)
    ap.add_argument("--repo", default="fly-ai-playground")
    ap.add_argument("--workdir", default=os.path.join(tempfile.gettempdir(), "flyai-checkup"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="기존 클론을 지우고 새로 받기")
    ap.add_argument("--source", help="클론 URL 직접 지정 (테스트용)")
    args = ap.parse_args()

    if args.fresh:
        shutil.rmtree(os.path.join(args.workdir, args.repo), ignore_errors=True)

    path = ensure_clone(args.owner, args.repo, args.workdir, args.source)
    cfg = load_members(path)
    members = cfg["members"]
    alias = build_alias(members)
    main_ref = main_branch(path)

    def who(*keys):
        for k in keys:
            if not k:
                continue
            k = str(k).lower()
            if "@" in k:
                k = k.split("@")[0]
            if k in alias:
                return alias[k]
        return None

    stats = {}
    for m in members:
        stats[m["login"]] = {
            "commits": 0, "merge_commits": 0, "branches": set(), "specs": [],
            "claude_md": 0, "skills": 0, "last": "", "recent": [], "merged_prs": 0,
        }

    # --- git: 모든 브랜치의 커밋 ---
    unmatched = defaultdict(int)
    fmt = UNIT.join(["%H", "%an", "%ae", "%aI", "%P", "%s"])
    log = run(["git", "log", "--all", "--pretty=format:" + fmt], cwd=path)
    for line in log.splitlines():
        parts = line.split(UNIT)
        if len(parts) < 6:
            continue
        _sha, name, email, date, parents, subject = parts[:6]
        if "[bot]" in name or name == "github-actions":
            continue
        w = who(name, email)
        if not w:
            unmatched[(name, email)] += 1
            continue
        s = stats[w]
        s["commits"] += 1
        # PR 머지 커밋은 GitHub이 대신 만들어 주는 것이라 충돌 해결로 치지 않는다.
        # 로컬에서 직접 만든 머지 커밋만이 "충돌을 직접 풀었다"는 증거다.
        if len(parents.split()) > 1 and not subject.startswith("Merge pull request"):
            s["merge_commits"] += 1
        if date > s["last"]:
            s["last"] = date
        if len(s["recent"]) < 5:
            s["recent"].append(subject[:88])

    # --- git: 특정 경로를 건드린 커밋 (하네스 기여) ---
    for pathspec, key in (("CLAUDE.md", "claude_md"), (".claude", "skills")):
        out = run(["git", "log", "--all", "--pretty=format:%an" + UNIT + "%ae", "--", pathspec], cwd=path)
        for line in out.splitlines():
            bits = line.split(UNIT)
            w = who(*bits)
            if w:
                stats[w][key] += 1

    # --- git: 브랜치 소유 ---
    for b in run(["git", "branch", "-r", "--format=%(refname:short)"], cwd=path).splitlines():
        b = b.strip()
        m = re.match(r"origin/sandbox/([^-/]+)", b)
        if m:
            w = who(m.group(1))
            if w:
                stats[w]["branches"].add(b)

    # --- git: main에 머지된 PR (머지 커밋 메시지의 브랜치 이름에서 주인을 찾는다) ---
    merged = run(["git", "log", main_ref, "--merges", "--pretty=format:%s"], cwd=path)
    for line in merged.splitlines():
        m = re.search(r"Merge (?:pull request #\d+ from |branch '?)(\S+?)'?$", line)
        if not m:
            continue
        ref = m.group(1)
        owner_part = ref.split("/")[0] if "/" in ref else ""
        b = re.search(r"sandbox/([A-Za-z0-9_.]+?)(?:-|/|$)", ref)
        w = (who(b.group(1)) if b else None) or who(owner_part)
        if w:
            stats[w]["merged_prs"] += 1

    # --- git: SPEC.md 존재 (main뿐 아니라 모든 브랜치에서 찾는다) ---
    seen_paths = set()
    for f in run(["git", "log", "--all", "--pretty=format:", "--name-only"], cwd=path).splitlines():
        f = f.strip()
        if not f or f in seen_paths:
            continue
        seen_paths.add(f)
        m = re.match(r"^sandbox/([^/]+)/", f)
        if m and f.lower().endswith("/spec.md"):
            w = who(m.group(1))
            if w and f not in stats[w]["specs"]:
                stats[w]["specs"].append(f)

    # --- Actions 스냅샷 (PR·리뷰·체크리스트) ---
    snap = None
    snap_path = os.path.join(path, "docs", "activity.json")
    if os.path.isfile(snap_path):
        try:
            snap = json.load(open(snap_path, encoding="utf-8"))
        except Exception:
            snap = None

    def snapv(login, key, default=0):
        if not snap or "people" not in snap:
            return default
        return (snap["people"].get(login) or {}).get(key, default)

    def checklist(login):
        c = snapv(login, "checklist", None) or {"1": [0, 0], "2": [0, 0], "3": [0, 0]}
        return c

    def item_checked(login, kw):
        items = snapv(login, "checklistItems", None) or {}
        return any(kw in k and v for k, v in items.items())

    day_now, elapsed = course_position(cfg.get("startDate"))
    result = {
        "repo": "%s/%s" % (args.owner, args.repo),
        "checkedAt": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "snapshot": bool(snap),
        "snapshotAt": (snap or {}).get("generatedAt"),
        "startDate": cfg.get("startDate"),
        "day": day_now, "elapsed": round(elapsed, 2),
        "expectedScore": round(expected_score(elapsed)),
        "members": [],
    }

    for m in members:
        login = m["login"]
        s = stats[login]
        prs_opened = snapv(login, "prsOpened", 0)
        prs_merged = max(snapv(login, "prsMerged", 0), s["merged_prs"])
        reviews = snapv(login, "reviewsGiven", 0)
        issue_activity = snapv(login, "issueComments", 0) + snapv(login, "issuesOpened", 0)
        pr_quality = snapv(login, "prBodyQuality", 0)
        resolved_conflict = bool(s["merge_commits"]) or item_checked(login, "conflict")
        has_spec = bool(s["specs"]) or bool(snapv(login, "hasSpec", False))

        git_s = 25 * (s["commits"] > 0) + 25 * (prs_opened > 0 or bool(s["branches"])) \
            + 25 * (prs_merged > 0) + 25 * resolved_conflict
        harness = 40 * (s["claude_md"] > 0) + 40 * (s["skills"] > 0) + 20 * item_checked(login, "서브에이전트")
        thinking = 40 * has_spec + 30 * (pr_quality >= 1) + 30 * (s["commits"] >= 3)
        comms = 40 * (reviews > 0) + 30 * (issue_activity > 0) + 30 * (pr_quality >= 2)

        overall = round((git_s + harness + thinking + comms) / 4)
        blend = blended(overall, checklist(login))
        pace_label, pace_delta = pace_of(blend, elapsed)
        result["members"].append({
            "login": login, "name": m.get("name", login), "role": m.get("role", "learner"),
            "skip": bool(m.get("skip")),
            "scores": {"git": git_s, "harness": harness, "thinking": thinking, "comms": comms},
            "overall": overall, "blended": blend,
            "pace": pace_label, "paceDelta": pace_delta,
            "commits": s["commits"], "mergeCommits": s["merge_commits"],
            "branches": sorted(s["branches"]),
            "prsOpened": prs_opened, "prsMerged": prs_merged,
            "reviewsGiven": reviews, "issueActivity": issue_activity,
            "claudeMdCommits": s["claude_md"], "skillCommits": s["skills"],
            "hasSpec": has_spec, "specs": s["specs"], "prBodyQuality": pr_quality,
            "resolvedConflict": resolved_conflict,
            "lastActivity": s["last"], "recentCommits": s["recent"],
            "checklist": checklist(login),
        })

    result["unmatchedAuthors"] = [
        {"name": n, "email": e, "commits": c}
        for (n, e), c in sorted(unmatched.items(), key=lambda x: -x[1])
    ]

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    learners = [m for m in result["members"]
                if m["role"] == "learner" and not m["skip"]] or result["members"]
    team_avg = round(sum(m["overall"] for m in learners) / max(1, len(learners)))

    print("=" * 74)
    print("연습 레포 점검 · %s · %s" % (result["repo"], result["checkedAt"]))
    print("Day %d · 학습 대상 %d명 평균 %d%% (이 시점 기대치 %d%%)"
          % (result["day"], len(learners), team_avg, result["expectedScore"]))
    if not snap:
        print("주의: docs/activity.json이 없습니다. PR·리뷰·체크리스트 지표는 0으로 보입니다.")
        print("      .github/workflows/activity.yml이 한 번이라도 돌았는지 확인하세요.")
    elif result["snapshotAt"]:
        print("스냅샷 수집 시각: %s" % result["snapshotAt"])
    print("=" * 74)

    for m in result["members"]:
        sc = m["scores"]
        if m["skip"]:
            print("\n▸ %s (가이드 · 실습 면제)  @%s" % (m["name"], m["login"]))
            print("   지원   리뷰 %d · 이슈 활동 %d · 커밋 %d"
                  % (m["reviewsGiven"], m["issueActivity"], m["commits"]))
            continue
        tag = " (가이드)" if m["role"] == "guide" else ""
        pace_txt = ""
        if m["pace"]:
            pace_txt = "   [%s %+d]" % (m["pace"], m["paceDelta"])
        print("\n▸ %s%s  @%s   종합 %d%%%s" % (m["name"], tag, m["login"], m["overall"], pace_txt))
        print("   역량   Git %3d%% · 하네스 %3d%% · 사고 %3d%% · 소통 %3d%%"
              % (sc["git"], sc["harness"], sc["thinking"], sc["comms"]))
        print("   활동   커밋 %d · 브랜치 %d · PR %d(머지 %d) · 리뷰 %d · 이슈 %d"
              % (m["commits"], len(m["branches"]), m["prsOpened"], m["prsMerged"],
                 m["reviewsGiven"], m["issueActivity"]))
        print("   증거   SPEC %s · CLAUDE.md %d회 · 스킬 %d회 · 충돌해결 %s · PR본문 %d/2"
              % ("O" if m["hasSpec"] else "X", m["claudeMdCommits"], m["skillCommits"],
                 "O" if m["resolvedConflict"] else "X", m["prBodyQuality"]))
        ck = m["checklist"]
        print("   체크   Day1 %s/%s · Day2 %s/%s · Day3 %s/%s"
              % (ck["1"][0], ck["1"][1], ck["2"][0], ck["2"][1], ck["3"][0], ck["3"][1]))
        print("   최근   %s" % (m["lastActivity"][:16].replace("T", " ") if m["lastActivity"] else "활동 없음"))
        for r in m["recentCommits"][:3]:
            print("          · %s" % r)

    print("\n" + "=" * 74)
    print("주의 신호")
    flagged = False
    stuck = [m["name"] for m in learners if m["overall"] < 40]
    if stuck:
        print("  · 도달도 40%% 미만: %s" % ", ".join(stuck)); flagged = True
    no_conflict = [m["name"] for m in learners if not m["resolvedConflict"]]
    if no_conflict and result["day"] >= 2:
        print("  · 아직 충돌 해결 경험 없음: %s  (Day 2를 넘기면 기회가 없습니다)"
              % ", ".join(no_conflict)); flagged = True
    no_review = [m["name"] for m in learners if m["reviewsGiven"] == 0]
    if no_review and result["day"] >= 2:
        print("  · 아직 남의 PR 리뷰 없음: %s" % ", ".join(no_review)); flagged = True
    no_spec = [m["name"] for m in learners if not m["hasSpec"]]
    if no_spec:
        print("  · SPEC.md 없음(구현부터 시작한 정황): %s" % ", ".join(no_spec)); flagged = True
    if not flagged:
        print("  · 없음")

    # --- 일정 조정 권고 ---
    print("\n일정 조정 권고")
    paces = [m["pace"] for m in learners if m["pace"]]
    slow = [m["name"] for m in learners if m["pace"] == "느림"]
    fast = [m["name"] for m in learners if m["pace"] == "빠름"]
    if not paces:
        print("  · 아직 판정하기 이릅니다. 다음 점검에서 다시 봅니다.")
    elif len(slow) >= 2:
        print("  · 늦추기 — %s 이(가) 뒤처져 있습니다." % ", ".join(slow))
        print("    다음 Day로 넘어가기 전에 반나절 보강을 넣으세요. 진도를 밀면 다음 단계가 더 어려워집니다.")
    elif len(fast) == len(paces) and len(paces) >= 2:
        print("  · 당기기 — 전원이 예상보다 앞서 있습니다.")
        print("    남은 시간에 다음 Day 과제를 미리 시작하거나, 마지막 날을 반나절로 줄여도 됩니다.")
    elif len(slow) == 1:
        print("  · 개별 보강 — %s 만 뒤처져 있습니다." % slow[0])
        print("    전체 일정은 유지하고, 가이드 한 명이 붙어 따라잡게 하는 편이 효율적입니다.")
    else:
        print("  · 유지 — 계획대로 진행하세요.")

    if result["unmatchedAuthors"]:
        print("\n매칭되지 않은 커밋 작성자 (course-config의 aliases에 추가하세요)")
        for u in result["unmatchedAuthors"][:8]:
            print("  · %s <%s>  커밋 %d개" % (u["name"], u["email"], u["commits"]))
    print("=" * 74)


if __name__ == "__main__":
    main()
