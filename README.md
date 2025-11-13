# GitHub ↔ Notion 이슈 동기화

GitHub Issues와 Notion 데이터베이스를 동기화하는 자동화 도구입니다.

## 기능

- ✅ GitHub Issues → Notion 동기화
- 📝 이슈 제목, 상태, 라벨, 본문 내용 모두 동기화
- 🎨 Markdown 완전 지원: 헤딩, 코드 블록, 리스트, 체크박스, 인용구, 굵은 글씨 등
- 🔄 이슈 생성, 수정, 닫기 시 자동 동기화
- ⏰ 주기적 자동 동기화 (매 시간)
- 🎯 수동 실행 가능

## 설정 방법

### 1. Notion 데이터베이스 준비

Notion에서 다음 속성을 가진 데이터베이스를 생성하세요:

| 속성 이름 | 타입 | 설명 |
|----------|------|------|
| Title | Title | 이슈 제목 |
| Issue Number | Number | 이슈 번호 |
| Status | Select | Open / Closed |
| Labels | Text | 라벨 목록 |
| URL | URL | GitHub 이슈 링크 |
| Created At | Date | 생성일 |
| Assignee | Text | 담당자 (선택) |

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

1. GitHub API를 통해 모든 이슈 조회 (제목, 상태, 라벨, 본문 등)
2. 각 이슈에 대해:
   - Notion에 이미 존재하는지 확인 (Issue Number로 검색)
   - 존재하면: 속성 및 본문 내용 업데이트
   - 존재하지 않으면: 새 페이지 생성 및 본문 추가
3. 이슈 본문 Markdown을 Notion 블록으로 변환:
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

- [ ] Notion → GitHub 양방향 동기화
- [ ] 코멘트 동기화
- [ ] 마일스톤 지원
- [ ] 프로젝트 보드 연동

## 라이선스

MIT
