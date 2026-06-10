"""음성 없이 두뇌를 텍스트로 테스트하는 REPL.

마이크/스피커/모델 다운로드 없이, Claude 두뇌 + 캘린더 + 생활기록만 검증한다.
  python chat_text.py

종료: '그만' 또는 Ctrl+C
"""
from __future__ import annotations

import sys

from config import Config
from jarvis.brain import Brain
from jarvis.tools import Tools


def main() -> None:
    cfg = Config.load()

    calendar = None
    try:
        from jarvis.calendar_client import CalendarClient

        calendar = CalendarClient(
            client_secret=cfg.google_client_secret,
            token_path=cfg.google_token,
            calendar_id=cfg.calendar_id,
            timezone=cfg.timezone,
        )
    except Exception as e:  # noqa: BLE001
        print(f"[경고] 캘린더 비활성: {e}", file=sys.stderr)

    tools = Tools(calendar, cfg.timezone)
    brain = Brain(cfg.anthropic_api_key, cfg.model, tools, cfg.persona, cfg.user_name)

    print("자비스 텍스트 모드. 무엇이든 말해보세요. (종료: 그만)\n")
    while True:
        try:
            text = input("나: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text in ("그만", "끝", "exit", "quit"):
            break
        print(f"자비스: {brain.respond(text)}\n")


if __name__ == "__main__":
    main()
