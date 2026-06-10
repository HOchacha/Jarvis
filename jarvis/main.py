"""자비스 메인 루프.

  대기 → "자비스" 호출 감지 → (삑) → 사용자 발화 녹음 → STT
       → Claude 두뇌(+캘린더/생활기록 도구) → Piper TTS → 스피커
       → 대화 이어가기(웨이크워드 없이) → 침묵하면 다시 대기

실행:  python -m jarvis.main
"""
from __future__ import annotations

import sys

import numpy as np

from config import Config
from jarvis import audio, coach
from jarvis.audio import SAMPLE_RATE, Microphone, play, play_interruptible
from jarvis.brain import Brain
from jarvis.stt import STT
from jarvis.tts import TTS
from jarvis.wakeword import WakeWord

_GOODBYE = ("그만", "잘 자", "잘자", "끝", "고마워 자비스", "수고했어", "바이")


def _beep() -> np.ndarray:
    """짧은 응답음(삑). 호출 즉시 반응을 주어 지연감을 줄인다."""
    t = np.linspace(0, 0.12, int(SAMPLE_RATE * 0.12), endpoint=False)
    tone = (0.25 * np.sin(2 * np.pi * 880 * t) * 32767).astype(np.int16)
    return tone


def _is_goodbye(text: str) -> bool:
    return any(g in text for g in _GOODBYE)


def build(cfg: Config) -> tuple[Brain, STT, TTS, WakeWord]:
    from jarvis.calendar_client import CalendarClient
    from jarvis.tools import Tools

    try:
        calendar = CalendarClient(
            client_secret=cfg.google_client_secret,
            token_path=cfg.google_token,
            calendar_id=cfg.calendar_id,
            timezone=cfg.timezone,
        )
    except Exception as e:  # noqa: BLE001 — 캘린더 없이도 음성 대화는 동작
        print(f"[경고] 캘린더 연동 실패(일정 기능 비활성): {e}", file=sys.stderr)
        calendar = None

    tools = Tools(calendar, cfg.timezone)
    brain = Brain(cfg.anthropic_api_key, cfg.model, tools, cfg.persona, cfg.user_name)
    stt = STT(cfg.whisper_model, cfg.whisper_device, cfg.whisper_compute)
    tts = TTS(cfg.piper_voice)
    wake = WakeWord(cfg.wakeword_model, cfg.wakeword_threshold)
    return brain, stt, tts, wake


def converse(brain: Brain, stt: STT, tts: TTS, mic: Microphone, first_reply: str | None = None) -> None:
    """웨이크워드 이후의 대화. 침묵하거나 작별하면 종료."""
    if first_reply:
        play_interruptible(tts.synthesize(first_reply), tts.sample_rate, mic)

    while True:
        mic.drain()
        pcm = mic.record_utterance()
        text = stt.transcribe(pcm)
        if not text:
            return  # 더 말이 없으면 대기 상태로
        print(f"  나: {text}")
        if _is_goodbye(text):
            play(tts.synthesize("응, 필요하면 다시 불러."), tts.sample_rate)
            return
        reply = brain.respond(text)
        print(f"  자비스: {reply}")
        interrupted = play_interruptible(tts.synthesize(reply), tts.sample_rate, mic)
        if interrupted:
            continue  # 사용자가 끼어듦 → 바로 다음 발화 받기


def main() -> None:
    cfg = Config.load()
    print("자비스 로딩 중... (모델 첫 실행은 시간이 걸릴 수 있어요)")
    brain, stt, tts, wake = build(cfg)
    beep = _beep()

    print(f"\n준비 완료. '{cfg.wakeword_model}'(\"자비스\")라고 불러보세요. (Ctrl+C 종료)\n")
    with Microphone() as mic:
        for block in mic.frames():
            if not wake.detect(block):
                continue
            wake.reset()
            print("• 호출 감지")
            play(beep, SAMPLE_RATE)
            converse(brain, stt, tts, mic)
            print(f"\n다시 대기 중... \"자비스\"\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료합니다.")
