# 🏃 내 대회 보관소 (race-hub)

국내 러닝·트레일러닝·철인3종·수영·자전거 대회를 한 페이지에서 보는 개인 대시보드.
GitHub가 매일 아침 6시(한국시간)에 자동으로 대회 정보를 수집해서 갱신합니다.
내 컴퓨터는 켜둘 필요가 없습니다.

## 폴더 구성

- `index.html` — 대시보드 화면
- `data.json` — 대회 데이터 (자동 갱신됨)
- `manual_events.json` — 수동 관리 목록 (자전거·수영 등 자동수집이 안 되는 대회)
- `scripts/scrape.py` — 수집 스크립트
- `.github/workflows/update.yml` — 매일 자동 실행 설정

## 설치 방법 (한 번만 하면 끝)

### 1. GitHub 계정 만들기 (이미 있으면 건너뛰기)
1. https://github.com 접속 → 우측 상단 **Sign up**
2. 이메일·비밀번호·아이디 입력하고 가입 (무료)

### 2. 저장소(repository) 만들기
1. 로그인 후 우측 상단 **+** 버튼 → **New repository**
2. Repository name: `race-hub` 입력
3. **Public** 선택 (Pages 무료 사용에 필요)
4. **Create repository** 클릭

### 3. 파일 올리기
1. 방금 만든 저장소 페이지에서 **uploading an existing file** 링크 클릭
2. 이 폴더(race-hub) 안의 **모든 파일과 폴더를 통째로** 드래그해서 업로드
   - 주의: `.github` 폴더는 숨김 폴더라 드래그가 안 될 수 있음.
     그 경우 업로드 후 저장소에서 **Add file → Create new file** 클릭,
     파일명에 `.github/workflows/update.yml` 입력하고
     update.yml 내용을 복사해 붙여넣기
3. 하단 **Commit changes** 클릭

### 4. Pages 켜기 (웹페이지 주소 만들기)
1. 저장소 상단 **Settings** 탭 → 왼쪽 메뉴 **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / 폴더: **/ (root)** 선택 → **Save**
4. 1~2분 후 `https://내아이디.github.io/race-hub/` 주소가 생김
   → 이 주소를 폰·PC 북마크에 저장하면 끝

### 5. 자동 갱신 켜기
1. 저장소 상단 **Actions** 탭 클릭
2. "워크플로를 활성화하시겠습니까" 안내가 나오면 **enable** 클릭
3. 왼쪽 "매일 대회 데이터 갱신" 클릭 → **Run workflow** 버튼 → 실행
   (이게 "디스패치" = 수동 즉시 실행. 이후엔 매일 아침 6시 자동 실행됨)

## 평소 사용법

- 대회 확인: `https://내아이디.github.io/race-hub/` 접속
- 즉시 갱신: Actions 탭 → Run workflow
- 대회 직접 추가: `manual_events.json` 파일을 GitHub에서 직접 편집
  (연필 아이콘 → 기존 형식대로 추가 → Commit)

## 참고사항

- 자동 수집 소스: roadrun.co.kr (마라톤·트레일), triathlon.or.kr (철인3종)
- 자전거(그란폰도)·수영 대회는 종합 사이트가 없어 `manual_events.json`으로 관리.
  가끔 Claude에게 "manual_events.json 최신화해줘"라고 요청하면 됩니다.
- GitHub 무료 정책상 60일간 저장소에 아무 활동이 없으면 자동 실행이 잠들 수 있음.
  Actions 탭에서 버튼 한 번 누르면 다시 깨어납니다.
- 대회 날짜·접수 정보는 변동될 수 있으니 신청 전 공식 홈페이지 확인 필수.
