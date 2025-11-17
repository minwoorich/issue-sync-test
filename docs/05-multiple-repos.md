# 🔄 Step 5: 여러 레포 동기화 설정 (선택사항)

이 문서는 여러 레포의 이슈를 한 곳에서 중앙 관리하는 방법을 설명합니다.

## 목차
- [개요](#개요)
- [config.yml 생성](#configyml-생성)
- [Organization PAT 설정](#organization-pat-설정)
- [테스트](#테스트)

---

## 개요

### 기본 모드 (현재)
```
issue-sync-test 레포
  └── 이 레포의 이슈만 동기화
```

### 중앙 수집 모드
```
issue-sync-test 레포 (중앙 허브)
  ├── config.yml (레포 목록)
  └── 
    ┌─→ username/project-a 이슈들
    ├─→ username/project-b 이슈들  } 모두 Notion으로
    └─→ username/project-c 이슈들
```

---

## config.yml 생성

### 1. 예시 파일 복사

레포지토리 루트에 `config.yml.example` 파일이 있습니다.

```bash
# 복사
cp config.yml.example config.yml
```

### 2. 레포 목록 수정

`config.yml` 파일을 열어서 동기화할 레포를 추가하세요:

```yaml
# 동기화할 레포 목록
repositories:
  - jangjunho/issue-sync-test
  - jangjunho/my-project
  - jangjunho/another-project
  # 더 추가 가능...
```

### 3. 파일 구조

```yaml
# ============================================================
# 레포 설정
# ============================================================

repositories:
  - username/repo1
  - username/repo2
  - username/repo3

# ============================================================
# 고급 설정 (선택사항)
# ============================================================

# Personal Access Token 사용 여부
use_personal_access_token: false  # Organization용은 true

# Projects 동기화 활성화
sync_projects: true

# 동기화할 이슈 상태
issue_state: all  # all, open, closed

# 한 번에 가져올 최대 이슈 수 (레포당)
max_issues_per_repo: 100
```

---

## 개인 레포 vs Organization 레포

### 개인 레포만 동기화

**설정:**
```yaml
repositories:
  - jangjunho/project-a
  - jangjunho/project-b

use_personal_access_token: false  # 기본 GITHUB_TOKEN 사용
```

**추가 작업:** 없음! 그대로 사용 가능

---

### Organization 레포 동기화

**설정:**
```yaml
repositories:
  - myorg/backend-api
  - myorg/frontend-web
  - myorg/mobile-app

use_personal_access_token: true  # PAT 필요!
```

**추가 작업:** Personal Access Token (PAT) 생성 필요

---

## Organization PAT 설정

여러 private 레포와 Projects에 접근하려면 Personal Access Token이 필요합니다.

### ⚠️ 중요: Classic Token 사용 권장!

Fine-grained Token의 Projects 권한이 불안정할 수 있습니다.
**Classic Token을 사용하면 확실하게 작동합니다!** ✅

---

### 방법 1: Classic Token (권장! ⭐)

#### 1. Classic Token 생성

**GitHub → Settings → Developer settings → Personal access tokens**

1. **Personal access tokens** 클릭
2. **Tokens (classic)** 선택 ← **이쪽!**
3. **Generate new token (classic)** 클릭

#### 2. Token 설정

```
Note: notion-sync-classic
Description: For Notion sync with Projects

Expiration: 90 days (또는 원하는 기간)

Select scopes:
  ✓ repo  ← 체크! (전체 레포 읽기/쓰기)
    ✓ repo:status (자동)
    ✓ repo_deployment (자동)
    ✓ public_repo (자동)
    ✓ repo:invite (자동)
    ✓ security_events (자동)
  
  ✓ read:project  ← 체크! (Projects 읽기)
```

**⚠️ 주의:** `repo`와 `read:project` 2개만 체크하면 됩니다!

#### 3. Generate & Copy

- **Generate token** 클릭
- Token 복사 (다시 볼 수 없음!)
- 형식: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 방법 2: Fine-grained Token (고급 사용자)

#### 1. Fine-grained Token 생성

**GitHub → Settings → Developer settings → Personal access tokens**

1. **Personal access tokens** 클릭
2. **Fine-grained tokens** 선택
3. **Generate new token** 클릭

#### 2. Token 설정

```
Token name: notion-sync-fine-grained
Description: For Notion sync across repos

Expiration: 90 days

Resource owner: [본인 계정 선택]

Repository access:
  ☑ Only select repositories
    - junhojang01/issue-sync-test
    - junhojang01/deeplink-test
    - (동기화할 레포들 모두 선택)
```

#### 3. Permissions 설정

**Repository permissions:** (스크롤 필요!)
```
Actions: No access
Administration: No access
...
Issues: Read-only ✓
Contents: Read-only ✓
Metadata: Read-only ✓ (자동)
...
Projects: Read-only ✓  ← 찾아서 체크! (알파벳 P...)
```

**Account permissions:** (User Projects 사용 시)
```
Projects: Read-only ✓  ← 이것도 체크!
```

⚠️ **주의:** Fine-grained Token에서 Projects 권한이 제대로 작동하지 않을 수 있습니다.
**문제 발생 시 Classic Token 사용을 권장합니다!**

#### 4. Generate & Copy

- **Generate token** 클릭
- Token 복사

---

### 공통: GitHub Secret 추가

**⚠️ 중요:** GitHub는 `GITHUB_`로 시작하는 Secret 이름을 허용하지 않습니다!

따라서 **`PAT_GITHUB`** 이름을 사용합니다.

#### Secret 추가:

Repository → Settings → Secrets and variables → Actions

```
Name: PAT_GITHUB  ← GITHUB_PAT 아님! (등록 불가)
Secret: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        ↑ 복사한 Classic Token
```

#### workflow에서 사용:

```yaml
env:
  GITHUB_PAT: ${{ secrets.PAT_GITHUB }}
             환경변수↑      ↑Secret 이름
```

- **Secret 이름**: `PAT_GITHUB` (GitHub에 저장)
- **환경변수 이름**: `GITHUB_PAT` (Python에서 사용)

### 5. config.yml 업데이트

```yaml
repositories:
  - myorg/backend-api
  - myorg/frontend-web

use_personal_access_token: true  # ← 이것을 true로!
```

---

## 테스트

### 1. config.yml 확인

```bash
# 파일이 있는지 확인
ls config.yml

# 내용 확인
cat config.yml
```

### 2. 로컬 테스트 (선택사항)

```bash
# 환경 변수 설정
export GITHUB_TOKEN="your_token"
export NOTION_API_KEY="your_notion_key"
export NOTION_DATABASE_ID="your_database_id"

# 실행
python sync_issues.py
```

**예상 출력:**
```
======================================================================
GitHub Issues → Notion 동기화 시작
======================================================================

⚙️  설정 로드 중...
✓ config.yml 발견!

🔑 GITHUB_TOKEN 사용 (기본)

📋 config.yml에서 3개 레포를 찾았습니다.

======================================================================
[1/3] 레포: username/project-a
======================================================================
✓ GitHub에서 5개의 이슈를 가져왔습니다.
...
```

### 3. GitHub Actions 실행

1. **config.yml을 커밋하고 Push**
   ```bash
   git add config.yml
   git commit -m "여러 레포 동기화 설정 추가"
   git push
   ```

2. **Actions 탭에서 수동 실행**
   - Run workflow 클릭

3. **로그 확인**
   - 각 레포별로 동기화 진행 확인
   - "동기화한 레포: X개" 메시지 확인

### 4. Notion 확인

모든 레포의 이슈가 하나의 Notion 데이터베이스에:

```
Title              | Repository          | Issue # | Status
-------------------|---------------------|---------|--------
로그인 버그        | username/project-a  | #1      | Open
다크모드 추가      | username/project-b  | #5      | Open
API 개선           | username/project-c  | #3      | Closed
```

**Repository 필드**로 구분 가능!

---

## 주의사항

### ⚠️ config.yml은 Git에 포함됩니다

`config.yml`은 **레포지토리에 커밋**됩니다.

**이유:**
- GitHub Actions가 설정 파일을 읽어야 함
- 레포 목록은 일반적으로 공개 정보 (민감하지 않음)

**민감한 정보는 절대 포함하지 마세요:**
- ❌ API Keys, Tokens → GitHub Secrets 사용
- ❌ 비밀번호, 개인정보
- ✅ 레포 목록 (public/private 레포 이름은 OK)

**팀과 공유:**
- config.yml을 push하면 모두 동일한 설정 사용
- `config.yml.example`은 참고용

### ⚠️ PAT 보안

Personal Access Token은:
- ❌ 코드에 포함하지 마세요
- ❌ 커밋하지 마세요
- ✅ GitHub Secrets에만 저장
- ✅ 주기적으로 갱신

### ⚠️ Rate Limiting

여러 레포를 동기화하면 API 호출이 많아집니다:
- GitHub API: 시간당 5,000 requests (인증 시)
- Notion API: 초당 3 requests

**많은 레포 + 많은 이슈**가 있다면 시간이 걸릴 수 있습니다.

---

## 문제 해결

### config.yml이 로드되지 않음

**확인:**
```bash
# 파일 위치
ls -la config.yml

# 파일이 레포 루트에 있어야 함
repo/
  ├── config.yml  ← 여기!
  ├── sync_issues.py
  └── ...
```

### "GITHUB_PAT가 없습니다" 에러

`use_personal_access_token: true`인데 PAT가 없을 때:

**해결:**
1. PAT 생성 (위 가이드 참고)
2. GitHub Secrets에 `GITHUB_PAT` 추가
3. 또는 `use_personal_access_token: false`로 변경

### 특정 레포만 동기화 실패

**로그 확인:**
```
✗ 레포 myorg/backend-api 동기화 실패: 404 Not Found
```

**원인:**
- 레포 이름 오타
- 레포 접근 권한 없음
- Private 레포인데 PAT 권한 부족

**해결:**
- 레포 이름 확인
- PAT 권한 확인
- PAT의 Repository access에 해당 레포 추가

### Organization에서 "Resource not accessible" 에러

**원인:**
- Organization 설정에서 PAT 사용이 제한됨

**해결:**
1. Organization Settings
2. Personal access tokens (Beta)
3. 정책 확인 및 승인

---

## 다음 단계

### 확장 아이디어

1. **필터링**
   ```yaml
   repositories:
     - username/project-a:
         labels: ["bug", "enhancement"]  # 특정 라벨만
         state: "open"  # 열린 이슈만
   ```

2. **다른 Notion DB**
   ```yaml
   repositories:
     - username/project-a:
         notion_database: "db_id_1"
     - username/project-b:
         notion_database: "db_id_2"
   ```

3. **스케줄 조정**
   - 레포가 많으면 스케줄 빈도 조정
   - 또는 이벤트 트리거만 사용

---

## 성공 사례

### 시나리오: 스타트업의 모든 프로젝트 관리

```yaml
repositories:
  - startup/backend-api
  - startup/web-frontend
  - startup/mobile-app
  - startup/admin-panel
  - startup/data-pipeline
  - startup/docs
```

**결과:**
- 6개 레포의 모든 이슈를 Notion 하나로 관리
- PM이 전체 프로젝트 현황을 한눈에 파악
- Repository 필터로 팀별 이슈 분류

**소요 시간:** 
- 설정: 10분
- 첫 동기화: 3분 (약 200개 이슈)
- 이후 자동 동기화

---

축하합니다! 🎉

이제 여러 레포의 이슈를 한 곳에서 관리할 수 있습니다!

다음: Organization 확장 시 이 가이드를 다시 참고하세요.

