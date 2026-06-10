"""로컬 텍스트→음성 (Piper). 오프라인.

Piper 음성 모델(.onnx + .onnx.json)을 scripts/setup_voices.md 대로 받아
JARVIS_PIPER_VOICE 에 경로를 지정한다.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


class TTS:
    def __init__(self, voice_path: str):
        from piper.voice import PiperVoice

        path = Path(voice_path)
        if not path.exists():
            raise RuntimeError(
                f"Piper 음성 모델이 없습니다: {voice_path}\n"
                f"scripts/setup_voices.md 를 보고 한국어 음성을 받으세요."
            )
        self._voice = PiperVoice.load(str(path))
        self.sample_rate = self._voice.config.sample_rate

    def synthesize(self, text: str) -> np.ndarray:
        """텍스트 → 16/22kHz int16 오디오 배열 (sample_rate 는 self.sample_rate)."""
        chunks = [
            np.frombuffer(raw, dtype=np.int16)
            for raw in self._voice.synthesize_stream_raw(text)
        ]
        if not chunks:
            return np.zeros(0, dtype=np.int16)
        return np.concatenate(chunks)
