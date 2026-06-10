# 자비스 (JARVIS) — 음성 대화형 개인 비서

매일 **일정을 보고**하고 **생활을 교정**해 주는, "자비스"처럼 부르면 깨어나는
음성 비서입니다.

- **두뇌**: Claude Opus 4.8 (일정 추론 + 생활 코칭)
- **귀(STT)**: faster-whisper — 로컬/오프라인 (한국어)
- **입(TTS)**: Piper — 로컬/오프라인 (한국어)
- **호출**: openWakeWord — "자비스"
- **일정**: 구글 캘린더 (읽기/추가)
- **생활 교정**: 생활 기록 + 목표 + 일정을 근거로 한 코칭

> 음성 처리는 전부 로컬에서 돌아갑니다. 인터넷이 필요한 건 **두뇌(Claude API)** 뿐입니다.

```
🎤 마이크 ─ "자비스" 감지 ─ STT ─→ Claude(캘린더·생활기록 도구) ─→ Piper TTS ─→ 🔊
                  ↑                                                          │
                  └──────────────── 침묵하면 다시 대기 ──────────────────────┘
```

## 구조

```
config.py              설정(.env 로딩)
chat_text.py           음성 없이 두뇌만 테스트하는 텍스트 REPL  ← 먼저 여기서 검증
jarvis/
  main.py              메인 대화 루프 (웨이크워드 → 대화)
  wakeword.py          openWakeWord ("자비스")
  audio.py             마이크/스피커 + VAD 턴 종료 + 바지인
  stt.py               faster-whisper (음성→글)
  tts.py               Piper (글→음성)
  brain.py             Claude Opus 4.8 + 도구 루프
  tools.py             도구 정의/실행 (일정·생활기록·기억·시각)
  calendar_client.py   구글 캘린더 OAuth + 읽기/추가
  store.py             생활 기록/선호 로컬 저장(JSON)
  coach.py             아침 브리핑 / 저녁 회고 시나리오
  daily_brief.py       정기 브리핑 (cron 용)
scripts/
  setup_google.md      구글 캘린더 설정
  setup_voices.md      Piper 한국어 음성 설치
  train_wakeword.md    웨이크워드 설정/커스텀 학습
```

## 설치

```bash
# 1) 가상환경 + 의존성
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
sudo apt-get install -y portaudio19-dev ffmpeg   # sounddevice/whisper 용 (리눅스)

# 2) 환경변수
cp .env.example .env
#   .env 를 열어 ANTHROPIC_API_KEY 등 채우기

# 3) 구글 캘린더 (선택) — scripts/setup_google.md
# 4) Piper 한국어 음성 — scripts/setup_voices.md
```

## 실행

```bash
# A) 두뇌만 먼저 검증 (음성/모델 다운로드 불필요, API 키만 있으면 됨)
python chat_text.py
#   예) "오늘 일정 알려줘", "어제 6시간밖에 못 잤어", "매일 7시 기상이 목표야"

# B) 전체 음성 비서
python -m jarvis.main
#   → "자비스"(또는 "Hey Jarvis") 라고 부르고 말하기

# C) 정기 브리핑 (cron)
python -m jarvis.daily_brief morning   # 아침 일정 보고
python -m jarvis.daily_brief evening   # 저녁 하루 회고
```

crontab 예시:

```cron
0 7  * * *  cd /home/you/life-working && .venv/bin/python -m jarvis.daily_brief morning
0 23 * * *  cd /home/you/life-working && .venv/bin/python -m jarvis.daily_brief evening
```

## 권장 진행 순서

1. `pip install anthropic python-dotenv` + `.env` 채우고 **`chat_text.py`** 로 두뇌 검증
2. 구글 캘린더 연동 → "오늘 일정" 확인
3. Piper 음성 + 마이크/스피커 연결 → `jarvis.main` 으로 음성 대화
4. 라즈베리파이로 이주 (아래)

## 라즈베리파이(스피커형) 이주

- `JARVIS_WHISPER_MODEL=base`, `JARVIS_WHISPER_COMPUTE=int8` 로 가볍게
- 웨이크워드는 PC/Colab에서 학습 후 `.onnx` 만 복사 (`scripts/train_wakeword.md`)
- 구글 토큰(`secrets/google_token.json`)도 PC에서 인증 후 복사 (헤드리스 대응)
- USB 마이크 + 스피커 연결, `systemd` 서비스로 부팅 시 자동 실행

## 튜닝 포인트

- **지연이 길다** → Whisper 모델 작게(`base`), `brain.py` 의 `effort` 는 이미 `low`
- **한국어 TTS 품질** → Piper 한계 시 TTS만 클라우드로 (tts.py 인터페이스 유지)
- **오인식(웨이크워드)** → `JARVIS_WAKEWORD_THRESHOLD` 상향
- **말투/성격** → `.env` 의 `JARVIS_PERSONA`
- **코칭 강도/시나리오** → `jarvis/coach.py`, `jarvis/brain.py` 시스템 프롬프트
