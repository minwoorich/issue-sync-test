# 🔑 Classic Token 사용 가이드

여러 레포와 Projects를 동기화하기 위한 Classic Token 생성 가이드입니다.

## 📋 언제 필요한가요?

다음 경우에 Classic Token이 필요합니다:

- ✅ 여러 **private 레포**의 이슈를 동기화
- ✅ **User/Organization Projects** 정보를 가져오기
- ✅ Fine-grained Token의 Projects 권한 문제 회피

---

## 🚀 Classic Token 생성

### 1. GitHub Settings 접속

1. GitHub 우측 상단 **프로필 클릭**
2. **Settings** 선택
3. 좌측 하단 **Developer settings** 클릭

### 2. Classic Token 메뉴

1. **Personal access tokens** 클릭
2. **Tokens (classic)** 선택 ← **중요!**
3. **Generate new token (classic)** 클릭

### 3. Token 정보 입력

```
Note: notion-sync-classic
   (또는 원하는 이름)

Expiration: 90 days
   (또는 원하는 기간, No expiration은 비권장)
```

### 4. Scopes 선택 (중요!)

**체크할 것 (2개만!):**

#### ✅ repo
```
✓ repo
  ✓ repo:status (자동 체크됨)
  ✓ repo_deployment (자동)
  ✓ public_repo (자동)
  ✓ repo:invite (자동)
  ✓ security_events (자동)
```

**이것만 체크하면:**
- private/public 레포 접근
- 이슈 읽기
- 콘텐츠 읽기

#### ✅ read:project
```
read:project
  (하위 항목 없음)
```

**이것만 체크하면:**
- Projects 정보 읽기
- Repository/User/Organization 모든 레벨 Projects

---

### ⚠️ 체크하지 말아야 할 것들

다음은 **불필요**합니다 (보안상 체크 X):

```
❌ admin:repo_hook (Webhook 관리)
❌ write:packages (패키지 쓰기)
❌ delete:packages (패키지 삭제)
❌ admin:org (조직 관리)
❌ admin:public_key (SSH 키 관리)
❌ admin:repo (레포 삭제/이전)
❌ admin:gpg_key (GPG 키)
```

**필요한 권한만 최소한으로!** 🔒

---

### 5. Token 생성

- **Generate token** 버튼 클릭
- Token이 표시됩니다

### 6. Token 복사

```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

⚠️ **중요:** 
- 이 페이지를 벗어나면 다시 볼 수 없습니다!
- 안전한 곳에 임시 저장하거나 바로 Secret에 추가
- 잃어버렸다면 재생성 필요

---

## 🔐 GitHub Secret 추가

### 1. Repository Settings

```
junhojang01/issue-sync-test (또는 본인 레포)
→ Settings
→ Secrets and variables
→ Actions
```

### 2. New repository secret

**"New repository secret"** 버튼 클릭

### 3. Secret 정보 입력

```
Name: PAT_GITHUB
      ↑ GITHUB_PAT 아님! GitHub는 GITHUB_로 시작하는 이름 허용 안 함

Secret: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        ↑ 복사한 Classic Token 붙여넣기
```

### 4. Add secret

**"Add secret"** 버튼 클릭

### 5. 확인

Secrets 목록에 추가되었는지 확인:

```
Repository secrets

NOTION_API_KEY         ✓
NOTION_DATABASE_ID     ✓
PAT_GITHUB             ✓ ← 새로 추가됨!
```

---

## 🔄 workflow와의 연결

### workflow.yml 설정

이미 설정되어 있습니다:

```yaml
env:
  GITHUB_PAT: ${{ secrets.PAT_GITHUB }}
  #    ↑ 환경변수         ↑ Secret 이름
```

- **Secret 이름**: `PAT_GITHUB` (GitHub에 저장되는 이름)
- **환경변수**: `GITHUB_PAT` (Python 코드에서 사용하는 이름)

### Python에서 사용

```python
token = os.environ.get('GITHUB_PAT')  # ← 환경변수 이름 사용
```

---

## ✅ 테스트

### 1. config.yml 확인

```yaml
use_personal_access_token: true  # ← true인지 확인
```

### 2. Push & Run

```bash
git push
```

Actions → Run workflow

### 3. 로그 확인

성공 시:
```
🔑 PAT 사용 (여러 레포 + Projects 접근 가능)  ✅
```

Projects 에러 없음:
```
  ✓ Issue #1 업데이트 완료: ...
  # ⚠ GraphQL 에러 없음!
```

### 4. Notion 확인

Projects 정보가 채워졌는지:
```
Project: 2024 Development  ✅
Project Status: In progress ✅
Priority: High             ✅
Story Points: 5            ✅
```

---

## 🐛 문제 해결

### "Resource not accessible by personal access token"

**원인:** Projects 권한 없음

**해결:**
1. Token 편집 또는 재생성
2. `read:project` scope 체크 확인
3. Secret 업데이트

### "Bad credentials"

**원인:** Token이 유효하지 않음

**해결:**
1. Token 재생성
2. 복사 시 공백/줄바꿈 제거
3. Secret에 정확히 붙여넣기

### "GITHUB_PAT가 설정되지 않았습니다"

**원인:** Secret 이름 불일치

**확인:**
- Secret 이름: `PAT_GITHUB` (O)
- workflow: `GITHUB_PAT: ${{ secrets.PAT_GITHUB }}` (O)

### Token이 만료됨

**해결:**
1. 새 Token 생성 (같은 설정)
2. Secret 업데이트
3. 주기적으로 갱신 (90일마다)

---

## 🔐 보안 모범 사례

### ✅ 해야 할 것
- 최소 권한만 부여 (`repo`, `read:project`)
- 정기적으로 Token 갱신 (90일)
- 사용하지 않는 Token 삭제
- Token을 GitHub Secrets에만 저장

### ❌ 하지 말아야 할 것
- Token을 코드에 포함
- Token을 config.yml에 작성
- Token을 커밋
- 불필요한 권한 부여
- Token을 공유

---

## 📊 권한 비교

| Scope | 권한 | 필요 여부 |
|-------|------|-----------|
| `repo` | 레포 읽기/쓰기 | ✅ 필수 |
| `read:project` | Projects 읽기 | ✅ 필수 |
| `admin:org` | 조직 관리 | ❌ 불필요 |
| `delete_repo` | 레포 삭제 | ❌ 불필요 |
| `write:packages` | 패키지 쓰기 | ❌ 불필요 |

**오직 2개만:** `repo` + `read:project`

---

## 🎯 요약

### 단계별 체크리스트

- [ ] Classic Token 생성
  - [ ] Scopes: `repo` ✓
  - [ ] Scopes: `read:project` ✓
- [ ] Token 복사
- [ ] GitHub Secret 추가
  - [ ] Name: `PAT_GITHUB`
  - [ ] Value: 복사한 Token
- [ ] config.yml 확인
  - [ ] `use_personal_access_token: true`
- [ ] Push
- [ ] Actions 실행
- [ ] Notion에서 Projects 정보 확인

---

## 🎉 성공!

Classic Token을 사용하면:
- ✅ 모든 private 레포 접근
- ✅ User/Organization Projects 조회
- ✅ 안정적인 동작
- ✅ 간단한 설정

Notion에 모든 Projects 정보가 동기화됩니다! 🚀

