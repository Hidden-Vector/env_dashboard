# 지구환경 관제 전광판

매일 07:00(KST)에 GitHub Actions가 자동으로 데이터를 수집해 `data/daily.json`을 갱신하고,
`index.html`이 그 파일을 읽어 화면에 표시하는 완전 무료 대시보드입니다.

## 0. 준비물
- GitHub 계정 (무료)
- (선택) 공공데이터포털(data.go.kr) 계정 — 대기질·전력수급 API를 쓰려면 필요, 이것도 무료

## 1. 배포 방법 (5분)
1. GitHub에서 새 저장소(Repository)를 만듭니다. **반드시 Public(공개)** 으로 만드세요.
   (Public이어야 GitHub Pages·Actions가 완전 무료·무제한으로 동작합니다)
2. 이 폴더 안의 모든 파일(`index.html`, `data/`, `scripts/`, `.github/`)을
   그 저장소에 업로드합니다. (GitHub 웹사이트의 "Add file → Upload files"로도 가능)
3. 저장소 메뉴 `Settings → Pages`로 이동해서
   - Source: `Deploy from a branch`
   - Branch: `main` / `/(root)`
   로 설정하고 저장합니다.
4. 1~2분 뒤 `https://<내아이디>.github.io/<저장소이름>/` 주소로 접속하면 대시보드가 보입니다.

이 시점부터 화면은 뜨지만, 대기질/전력 데이터는 아직 "데이터 없음"으로 보일 수 있습니다.
(키를 안 넣었기 때문에 정상입니다 — 아래 2번에서 채웁니다.)

## 2. 무료 API 키 발급하고 등록하기 (선택, 5~10분)

### 대기질(에어코리아)
1. https://www.data.go.kr 회원가입
2. "에어코리아 대기오염정보" 검색 → 활용신청 (즉시 승인)
3. 발급된 "인증키(Encoding)"를 복사
4. 저장소 `Settings → Secrets and variables → Actions → New repository secret`
   - Name: `AIRKOREA_KEY`
   - Value: 방금 복사한 키

### 전력수급(전력거래소, 국내 CO2 추정용)
1. 같은 data.go.kr에서 "한국전력거래소" 관련 API 활용신청
2. 발급받은 키를 `KPX_KEY` 라는 이름의 Secret으로 동일하게 등록

키를 등록한 뒤, 저장소 상단 `Actions` 탭 → `환경 데이터 매일 자동 갱신` → `Run workflow` 버튼을 눌러
수동으로 한 번 실행해보면 바로 반영된 결과를 확인할 수 있습니다.

## 3. 매일 자동 갱신은 어떻게 되나요?
`.github/workflows/update-data.yml` 파일이 매일 UTC 22:00(=한국시간 07:00)에
GitHub 서버에서 자동으로 `scripts/collect_data.py`를 실행하고,
결과를 `data/daily.json`으로 저장소에 자동 커밋합니다.
당신의 컴퓨터가 꺼져 있어도, 파일을 아무도 열어보지 않아도 GitHub 서버가 대신 실행해줍니다.

## 4. 세계 CO2 배출량은 왜 비어있나요?
Carbon Monitor / Climate TRACE는 별도 API 키 발급 절차나 데이터 형식이 자주 바뀌어
이 템플릿에는 기본으로 넣지 않았습니다. `scripts/collect_data.py`의
`world_co2` 부분에 원하는 소스의 호출 코드를 추가하면 됩니다.
(원하시면 이어서 만들어 드릴 수 있습니다.)

## 5. 전광판(키오스크)으로 띄우기
모니터에 상시 띄워두고 싶다면:
- 크롬 브라우저에서 해당 URL을 열고 `F11`(전체화면) 또는
- 크롬 실행 옵션에 `--kiosk https://<내아이디>.github.io/<저장소이름>/` 를 추가
- 라즈베리파이 등 저전력 기기에 자동 로그인 + 크롬 자동실행을 설정해두면
  전원만 연결된 전광판처럼 사용할 수 있습니다.

## 6. 비용
- Public 저장소 기준 GitHub Pages, GitHub Actions 모두 **완전 무료**입니다.
- 공공데이터포털 API 키 발급도 무료입니다.
- 신용카드 등록이 전혀 필요 없습니다.
