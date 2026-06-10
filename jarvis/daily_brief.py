"""자비스가 먼저 말 거는 정기 브리핑 (cron 용).

  아침 일정 보고:   python -m jarvis.daily_brief morning
  저녁 하루 회고:   python -m jarvis.daily_brief evening

crontab 예시:
  0 7 * * *  cd /home/ubuntu/life-working && python -m jarvis.daily_brief morning
  0 23 * * * cd /home/ubuntu/life-working && python -m jarvis.daily_brief evening
"""
from __future__ import annotations

import sys

from config import Config
from jarvis import audio, coach
from jarvis.main import build


def run(mode: str) -> None:
    cfg = Config.load()
    brain, _stt, tts, _wake = build(cfg)

    instruction = coach.MORNING_BRIEF if mode == "morning" else coach.EVENING_REVIEW
    text = brain.system_turn(instruction)
    print(f"자비스: {text}")
    audio.play(tts.synthesize(text), tts.sample_rate)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    if mode not in ("morning", "evening"):
        print("사용법: python -m jarvis.daily_brief [morning|evening]")
        sys.exit(1)
    run(mode)
