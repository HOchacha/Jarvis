"""환경변수 → 설정 객체. 모든 모듈이 여기서 설정을 읽는다."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

load_dotenv(ROOT / ".env")


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(
            f"환경변수 {key} 가 설정되지 않았습니다. .env 파일을 확인하세요 "
            f"(.env.example 참고)."
        )
    return val


@dataclass(frozen=True)
class Config:
    # 두뇌
    anthropic_api_key: str
    model: str = "claude-opus-4-8"

    # 사용자
    user_name: str = "사용자"
    timezone: str = "Asia/Seoul"
    persona: str = "따뜻하지만 솔직하게, 핵심만 말한다."

    # 웨이크워드
    wakeword_model: str = "hey_jarvis"
    wakeword_threshold: float = 0.5

    # STT
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute: str = "int8"

    # TTS
    piper_voice: str = "secrets/voices/ko_KR-glados-medium.onnx"

    # 캘린더
    google_client_secret: str = "secrets/google_client_secret.json"
    google_token: str = "secrets/google_token.json"
    calendar_id: str = "primary"

    @classmethod
    def load(cls) -> "Config":
        return cls(
            anthropic_api_key=_require("ANTHROPIC_API_KEY"),
            model=os.getenv("JARVIS_MODEL", "claude-opus-4-8"),
            user_name=os.getenv("JARVIS_USER_NAME", "사용자"),
            timezone=os.getenv("JARVIS_TIMEZONE", "Asia/Seoul"),
            persona=os.getenv("JARVIS_PERSONA", "따뜻하지만 솔직하게, 핵심만 말한다."),
            wakeword_model=os.getenv("JARVIS_WAKEWORD_MODEL", "hey_jarvis"),
            wakeword_threshold=float(os.getenv("JARVIS_WAKEWORD_THRESHOLD", "0.5")),
            whisper_model=os.getenv("JARVIS_WHISPER_MODEL", "small"),
            whisper_device=os.getenv("JARVIS_WHISPER_DEVICE", "cpu"),
            whisper_compute=os.getenv("JARVIS_WHISPER_COMPUTE", "int8"),
            piper_voice=os.getenv(
                "JARVIS_PIPER_VOICE", "secrets/voices/ko_KR-glados-medium.onnx"
            ),
            google_client_secret=os.getenv(
                "JARVIS_GOOGLE_CLIENT_SECRET", "secrets/google_client_secret.json"
            ),
            google_token=os.getenv(
                "JARVIS_GOOGLE_TOKEN", "secrets/google_token.json"
            ),
            calendar_id=os.getenv("JARVIS_CALENDAR_ID", "primary"),
        )
