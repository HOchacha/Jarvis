# 구글 캘린더 연동 설정

자비스가 캘린더를 읽고 일정을 추가하려면 OAuth 클라이언트가 필요합니다. 1회만 하면 됩니다.

## 1. 구글 클라우드 콘솔에서 OAuth 클라이언트 만들기

1. https://console.cloud.google.com 접속 → 프로젝트 생성(또는 선택)
2. **API 및 서비스 → 라이브러리** → "Google Calendar API" 검색 → **사용 설정**
3. **API 및 서비스 → OAuth 동의 화면**
   - User Type: **외부(External)**
   - 앱 이름/이메일 입력 후 저장
   - **테스트 사용자**에 본인 구글 계정 추가 (중요)
4. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → OAuth 클라이언트 ID**
   - 애플리케이션 유형: **데스크톱 앱**
   - 생성 후 **JSON 다운로드**

## 2. 시크릿 파일 배치

다운로드한 JSON을 이 경로로 저장하세요:

```
secrets/google_client_secret.json
```

(`.env` 의 `JARVIS_GOOGLE_CLIENT_SECRET` 와 일치해야 합니다.)

## 3. 최초 인증

처음 실행할 때 브라우저가 열리고 구글 로그인 → 권한 허용을 하면,
`secrets/google_token.json` 이 자동 생성되어 이후로는 재인증이 필요 없습니다.

```bash
python chat_text.py   # 또는 python -m jarvis.main
# → "오늘 일정 알려줘" 라고 입력해 동작 확인
```

> 헤드리스(모니터 없는 라즈베리파이)라면, 먼저 PC에서 인증해
> `secrets/google_token.json` 을 생성한 뒤 파이로 복사하면 됩니다.
