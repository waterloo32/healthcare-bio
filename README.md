# 바이오/헬스케어 뉴스 큐레이션 (MVP)

PRD(`PRD_바이오헬스케어_뉴스_큐레이션.md`) 기준 MVP 구현. RSS 자체 수집 → 규칙 기반 분류
→ 추출 요약 → SQLite 저장 → 정적 JSON으로 내보내 GitHub Pages에서 카드형 목록/필터/검색 제공.

**배포 방식**: 상시 구동 서버 없이 완전 무료로 운영하기 위해 정적 사이트 구조를 택했습니다.
GitHub Actions가 하루 4회 수집 파이프라인을 실행하고 결과를 `docs/data/*.json`으로 커밋하면,
GitHub Pages가 `docs/`를 그대로 정적으로 서빙합니다. FastAPI(`backend/app/main.py`)는 로컬
개발/디버깅용으로 남겨뒀지만 배포에는 사용하지 않습니다.

## 구조

```
backend/
  app/
    collector/        # RSS 수집, robots.txt 체크, 기사 본문 추출
    config.py          # DB 경로, User-Agent, rate limit 등 설정
    sources.py          # MVP 5개 소스 (Fierce Biotech/Pharma, Endpoints, STAT, MedCity)
    categories.py       # 카테고리 체계 (PRD 7절)
    classifier.py        # 규칙 기반 분류기
    summarizer.py         # 추출 요약기 (PRD 8.4 옵션 A)
    dedup.py               # 제목 유사도 기반 중복 병합
    pipeline.py             # 전체 파이프라인 오케스트레이션
    models.py                # Article / CollectionRun / SourceRunLog (SQLAlchemy)
    serialize.py              # Article -> dict 직렬화 (API/정적 JSON 공용)
    main.py                    # FastAPI API + 로컬 개발 서버 (배포에는 미사용)
  run_collect.py                # 수집 배치 1회 실행 CLI
  export_static.py               # DB -> docs/data/*.json 내보내기 (GitHub Actions가 실행)
  requirements.txt
docs/
  index.html / style.css / app.js   # 카드형 목록, 필터, 검색 (바닐라 JS, 빌드 불필요, GitHub Pages 소스)
  data/articles.json / meta.json     # 정적 데이터 (Actions가 매 실행마다 갱신·커밋)
.github/workflows/collect.yml          # 스케줄 수집 + 정적 데이터 커밋/푸시
data/news.db                            # SQLite (Actions 실행 간 dedup 상태 유지를 위해 저장소에 커밋됨)
logs/collect.log                         # 수집 로그 (FR-5, 로컬 전용 · git에는 미포함)
```

## 배포 (GitHub Pages + Actions, 완전 무료)

1. GitHub에 **public** 저장소를 만들고 이 프로젝트를 push (아래 "git 초기 설정" 참고).
2. 저장소 Settings → Pages → Source를 "Deploy from a branch" → `main` / `/docs`로 설정.
3. Settings → Actions → General → Workflow permissions에서 "Read and write permissions" 선택
   (`.github/workflows/collect.yml`이 데이터를 커밋/푸시하려면 필요).
4. Actions 탭에서 `Collect News` 워크플로를 "Run workflow"로 한 번 수동 실행해 정상 동작 확인.
5. 이후 `https://<사용자명>.github.io/<저장소명>/` 에서 사이트 확인 (Pages 최초 반영에 1~2분 소요).

### git 초기 설정

```powershell
git init
git add .
git commit -m "Initial commit: 바이오헬스케어 뉴스 큐레이션 MVP"
git branch -M main
git remote add origin https://github.com/<사용자명>/<저장소명>.git
git push -u origin main
```

이후로는 GitHub Actions가 하루 4회(00/06/12/18시 UTC) 자동으로 수집 → 분류 → 요약 →
`docs/data/*.json` 갱신 → 커밋/푸시까지 수행하며, GitHub Pages가 그 변경을 자동 반영합니다.
사람이 서버를 켜두거나 유지보수할 필요가 없습니다.

## 로컬 실행 (개발/디버깅용)

가상환경(`.venv`)과 패키지는 이미 설치되어 있습니다.

### 1. 뉴스 수집 (배치 1회 실행)

```powershell
.venv\Scripts\python.exe backend\run_collect.py
.venv\Scripts\python.exe backend\export_static.py   # docs/data/*.json 갱신
```

- 소스별 성공/실패, 신규 기사 수를 콘솔과 `logs/collect.log`에 남깁니다.
- 소스 성공률이 95% 미만이면 경고 로그를 출력합니다 (PRD FR-5, 목표 지표).

### 2. 웹 서버 실행 (선택, API를 직접 두드려보고 싶을 때)

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

브라우저에서 http://localhost:8000 접속. (배포된 사이트는 이 서버 없이 `docs/`를 정적으로 서빙하는 것뿐이므로, 로컬에서는 `docs` 폴더를 `python -m http.server`로 열어도 동일하게 확인 가능합니다.)

## 알려진 제약 (MVP 범위)

- **Fierce Biotech / Fierce Pharma**: RSS 피드는 정상 수집되지만, 개별 기사 페이지는 봇 차단(403)으로
  본문을 가져오지 못합니다. 이 경우 RSS가 제공하는 짧은 설명을 본문 대체로 사용하므로 요약 품질이
  제한적입니다. 추후 Playwright 등 브라우저 기반 수집으로 보강 검토 필요(PRD 리스크 표 참고).
- **Endpoints News**: `endpoints.news`가 자동화 요청 자체를 403으로 차단하는 경우가 있어 수집 실패율이
  높을 수 있습니다. 온보딩 체크리스트 상 "주의 소스"로 표시됨.
- **STAT News**: robots.txt가 AI 학습 크롤러(ClaudeBot 등)를 명시적으로 차단하지만, 본 봇은 학습 목적이
  아닌 개인 뉴스 큐레이션이며 별도 User-Agent(`BioHealthNewsCurationBot/0.1`)를 사용합니다. STAT+ 유료
  기사는 본문이 페이월로 막혀 있어 제목/요약 위주로만 노출됩니다. 외부 공개 전 ToS 재검토 필요
  (PRD 12절 오픈 이슈 #2).
- **요약 방식**: PRD 8.4 옵션 A(추출 요약, 무비용)로 구현. 문장을 그대로 골라 붙이는 방식이라 FR-11의
  "재구성" 요건을 완전히 충족하지 못하는 한계가 있음(PRD 12절 오픈 이슈 #1과 동일). 품질이 부족하면
  LLM 기반 요약(옵션 C)을 소량 예산으로 병행 검토.
- **2차 분류 보강(임베딩/LLM), NIH·PubMed 소스, 이메일 알림**: 로드맵상 MVP 이후(v1.1~v2) 항목으로 아직
  미구현.

## 다음 단계 제안

1. Fierce/Endpoints 본문 수집 실패율이 높으면 Playwright 기반 수집기로 교체 검토.
2. 분류 정확도 샘플 검수(목표 85%, PRD 2절) 후 키워드 사전 보정.
3. 개인 사용을 넘어 공개할 경우 STAT/Endpoints 등 유료 콘텐츠 비중이 있는 소스의 ToS 재검토.
