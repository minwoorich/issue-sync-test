# GitHub ↔ Notion 이슈 동기화

GitHub Issues와 Notion 데이터베이스를 동기화하는 자동화 도구입니다.

## 📚 빠른 시작 가이드

**[→ 전체 설정 가이드 보기 (docs/)](./docs/)**

처음 시작하시나요? 단계별 가이드를 따라하세요:

1. **[GitHub Projects 설정](./docs/01-projects-setup.md)** - Projects V2 생성 및 필드 설정
2. **[Notion 설정](./docs/02-notion-setup.md)** - Integration 생성 및 데이터베이스 준비
3. **[GitHub Secrets](./docs/03-github-secrets.md)** - API Key 및 권한 설정
4. **[테스트 실행](./docs/04-testing.md)** - 동기화 테스트 및 확인
5. **[여러 레포 동기화](./docs/05-multiple-repos.md)** - 중앙 수집 모드 (선택사항)
6. **[Classic Token 가이드](./docs/06-classic-token-guide.md)** - PAT 생성 (여러 레포 + Projects)
7. **[커스텀 필드 추가](./docs/07-custom-fields-guide.md)** - 필드 확장 (고급)

⏱️ **기본 설정: 약 40-50분**  
⏱️ **여러 레포: +15-20분**  
⏱️ **Classic Token: +10분**  
⏱️ **커스텀 필드: +15-30분**

## 기능

- ✅ **GitHub Issues → Notion 동기화**
- 📝 이슈 제목, 상태, 라벨, 본문 내용 모두 동기화
- 🎨 **Markdown 완전 지원**: 헤딩, 코드 블록, 리스트, 체크박스, 인용구, 굵은 글씨 등
- 🎯 **Projects V2 연동**: 프로젝트 정보 자동 동기화
  - 프로젝트 이름, Status (Backlog/Ready/In progress/In review/Done)
  - Priority, Story Points, Capacity, Sprint 등 모든 커스텀 필드
- 🏢 **여러 레포 중앙 수집** (선택사항)
  - config.yml로 레포 목록 관리
  - 개인 레포 / Organization 레포 지원
  - Repository 필드로 구분
- 🔄 이슈 생성, 수정, 닫기 시 자동 동기화
- ⏰ 주기적 자동 동기화 (매 시간)
- 🎯 수동 실행 가능

## 📊 동기화되는 필드

현재 동기화가 지원되는 모든 필드 목록입니다.

### 📌 GitHub Issue 기본 필드 (10개)

GitHub Issue의 기본 정보가 자동으로 동기화됩니다.

| # | Notion 속성 | 타입 | GitHub 필드 | 필수 | 설명 |
|---|------------|------|-------------|------|------|
| 1 | **Title** | Title | `title` | ✅ | 이슈 제목 |
| 2 | **Issue Number** | Number | `number` | ✅ | 이슈 번호 (#1, #2, ...) |
| 3 | **Status** | Select | `state` | ✅ | Open / Closed |
| 4 | **Labels** | Text | `labels` | ✅ | 라벨 (쉼표 구분) |
| 5 | **URL** | URL | `html_url` | ✅ | GitHub 이슈 링크 |
| 6 | **Created At** | Date | `created_at` | ✅ | 생성 날짜 |
| 7 | **Assignee** | Text | `assignee.login` | ⭕ | 담당자 (없을 수 있음) |
| 8 | **Milestone** | Text | `milestone.title` | ⭕ | 마일스톤 (없을 수 있음) |
| 9 | **Repository** | Text | `repository.full_name` | ✅ | 레포지토리 (여러 레포 시) |
| 10 | **(본문)** | Blocks | `body` | ⭕ | Markdown → Notion 블록 변환 |

**범례:** ✅ 필수 / ⭕ 선택 (값이 있을 때만)

### 🎯 GitHub Projects V2 필드 (10개)

Projects V2에 이슈가 추가되어 있고, 필드 값이 설정되어 있으면 자동 동기화됩니다.

| # | Notion 속성 | 타입 | Projects 필드 타입 | 예시 값 |
|---|------------|------|-------------------|---------|
| 1 | **Project** | Text | - | 2024 Development |
| 2 | **Project Status** | Select | Single Select | Backlog, Ready, In progress, In review, Done |
| 3 | **Priority** | Select | Single Select | Critical, High, Medium, Low |
| 4 | **Size** | Select | Single Select | XS, S, M, L, XL |
| 5 | **Story Points** | Number | Number | 1, 2, 3, 5, 8, 13 |
| 6 | **Capacity** | Number | Number | 시간 단위 (1, 2, 5, 8) |
| 7 | **Sprint** | Text | Iteration | Sprint 1, 2024-W01 |
| 8 | **Start date** | Date | Date | 2024-01-15 |
| 9 | **Target date** | Date | Date | 2024-02-01 |
| 10 | **Due date** | Date | Date | 2024-02-15 |

**✨ 모든 커스텀 필드 추가 가능!** - [가이드 보기](./docs/07-custom-fields-guide.md)

### 🎨 지원되는 Projects 필드 타입

| GitHub Projects 타입 | Notion 타입 | 지원 | 예시 |
|---------------------|-------------|------|------|
| **Single Select** | Select | ✅ | Status, Priority, Size, Team |
| **Number** | Number | ✅ | Story Points, Capacity, Estimated Hours |
| **Text** | Text | ✅ | Notes, Description |
| **Date** | Date | ✅ | Start date, Target date, Due date |
| **Iteration** | Text | ✅ | Sprint, Iteration |
| Multi-Select | Multi-select | ⚠️ | Tags (수동 추가 가능) |

**⚠️ 참고:** Multi-Select는 코드 수정이 필요합니다. [커스텀 필드 가이드](./docs/07-custom-fields-guide.md) 참고

---

## 설정 방법

### 1. Notion 데이터베이스 준비

**필수 속성 (Issue 기본):**

| 속성 이름 | 타입 | 필수 |
|----------|------|------|
| Title | Title | ✅ |
| Issue Number | Number | ✅ |
| Status | Select (Open, Closed) | ✅ |
| Labels | Text | ✅ |
| URL | URL | ✅ |
| Created At | Date | ✅ |

**선택 속성 (Issue 추가):**

| 속성 이름 | 타입 | 설명 |
|----------|------|------|
| Assignee | Text | 담당자 |
| Milestone | Text | 마일스톤 |
| Repository | Text | 레포 이름 (여러 레포 동기화 시) |

**Projects 속성 (Projects V2 사용 시):**

| 속성 이름 | 타입 | 옵션 |
|----------|------|------|
| Project | Text | - |
| Project Status | Select | Backlog, Ready, In progress, In review, Done |
| Priority | Select | Critical, High, Medium, Low |
| Size | Select | XS, S, M, L, XL |
| Story Points | Number | - |
| Capacity | Number | - |
| Sprint | Text | - |
| Start date | Date | - |
| Target date | Date | - |
| Due date | Date | - |

**⚠️ Select 옵션은 GitHub Projects와 정확히 일치해야 합니다!**

### 2. Notion Integration 생성

1. [Notion Integrations](https://www.notion.so/my-integrations)에서 새 Integration 생성
2. API Key 복사
3. 생성한 데이터베이스를 Integration과 연결 (우측 상단 `...` → `Connect to` → Integration 선택)

### 3. GitHub Secrets 설정

Repository → Settings → Secrets and variables → Actions에서 다음 Secrets를 추가:

- `NOTION_API_KEY`: Notion Integration API Key
- `NOTION_DATABASE_ID`: Notion 데이터베이스 ID
  - 데이터베이스 URL에서 추출: `https://notion.so/{workspace}/{DATABASE_ID}?v=...`
  - 32자리 영숫자 문자열 (하이픈 제외)

### 4. GitHub Actions 권한 확인

Repository → Settings → Actions → General → Workflow permissions:
- "Read repository contents and packages permissions" 권한이 활성화되어 있어야 합니다.

## 사용 방법

### 자동 실행

다음 상황에서 자동으로 실행됩니다:
- 이슈가 생성, 수정, 닫힘, 재오픈될 때
- 라벨이 추가/제거될 때
- 매 시간마다 (스케줄)

### 수동 실행

1. Actions 탭으로 이동
2. "GitHub Notion Issues Sync" 워크플로우 선택
3. "Run workflow" 버튼 클릭

### 로컬에서 테스트

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_TOKEN="your_github_token"
export NOTION_API_KEY="your_notion_api_key"
export NOTION_DATABASE_ID="your_database_id"

# 스크립트 실행
python sync_issues.py
```

## 동작 원리

1. **GitHub REST API**로 모든 이슈 조회 (제목, 상태, 라벨, 본문 등)
2. **GitHub GraphQL API**로 각 이슈의 Projects V2 정보 조회
   - 프로젝트 이름
   - Status, Priority, Story Points, Capacity, Sprint 등 모든 필드
3. 각 이슈에 대해:
   - Notion에 이미 존재하는지 확인 (Issue Number로 검색)
   - 존재하면: 속성 및 본문 내용 업데이트
   - 존재하지 않으면: 새 페이지 생성 및 본문 추가
4. 이슈 본문 Markdown을 Notion 블록으로 변환:
   - `# 헤딩` → Heading 블록
   - ` ```코드``` ` → Code 블록 (언어 구문 강조 포함)
   - `- 리스트` → Bulleted List
   - `1. 리스트` → Numbered List
   - `- [ ] 체크박스` → To-do 블록
   - `> 인용구` → Quote 블록
   - `` `인라인 코드` ``, `**굵은 글씨**` → Rich Text 스타일

## 파일 구조

```
.
├── .github/
│   └── workflows/
│       └── action.yml          # GitHub Actions 워크플로우
├── sync_issues.py              # 동기화 스크립트
├── requirements.txt            # Python 의존성
└── README.md                   # 이 파일
```

## 문제 해결

### "Notion API Key가 유효하지 않습니다" 에러
- Notion Integration이 올바르게 생성되었는지 확인
- Integration이 데이터베이스에 연결되었는지 확인

### "Database ID를 찾을 수 없습니다" 에러
- 데이터베이스 ID가 올바른지 확인 (32자리 영숫자)
- 하이픈(-)이 포함되어 있으면 제거

### "GitHub API 호출 실패" 에러
- Repository 이름이 올바른지 확인 (`owner/repo` 형식)
- Private repository의 경우 GITHUB_TOKEN 권한 확인

## 향후 계획

- [x] **Projects V2 연동** ✅ (완료!)
  - [x] GraphQL API로 프로젝트 정보 조회
  - [x] Status, Priority, Story Points, Capacity 등 동기화
  - [x] 모든 커스텀 필드 자동 감지
- [x] **여러 레포 동기화** ✅ (완료!)
  - [x] config.yml로 레포 목록 관리
  - [x] 중앙 집중식 동기화
  - [x] Organization 레포 지원 (PAT)
- [ ] **양방향 동기화** (다음 목표)
  - [ ] Notion → GitHub 이슈 생성
  - [ ] Notion Status 변경 → GitHub 이슈 닫기
- [ ] 코멘트 동기화
- [ ] 마일스톤 지원
- [ ] 이슈 템플릿 지원

## 라이선스

MIT
