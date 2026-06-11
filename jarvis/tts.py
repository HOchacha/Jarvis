"""로컬 텍스트→음성 — macOS 내장 `say` (오프라인, 한국어 Yuna).

원래 설계는 Piper였지만 (1) 공식 Piper 저장소에 한국어 음성이 없고,
(2) 커뮤니티 한국어 음성은 piper-tts 최신 API가 지원하지 않는 phoneme_type 을
쓰는 문제가 있어, macOS 내장 TTS(`say`)로 교체했다.
인터페이스(synthesize -> int16 ndarray, sample_rate)는 그대로라 나머지 코드는 무변경.

JARVIS_PIPER_VOICE 값:
  - `.onnx` 경로(기본값)면 무시하고 한국어 기본 음성 'Yuna' 사용
  - 그 외 문자열은 say 음성 이름으로 본다 (예: Yuna). `say -v '?'` 로 목록 확인.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

_DEFAULT_VOICE = "Yuna"  # macOS 내장 한국어 음성


class TTS:
    def __init__(self, voice_path: str, sample_rate: int = 22050):
        if shutil.which("say") is None:
            raise RuntimeError("macOS 'say' 명령을 찾을 수 없습니다 (이 TTS는 macOS 전용).")
        name = Path(voice_path).name
        # 기본 .onnx 경로면 한국어 기본 음성으로, 그 외엔 say 음성 이름으로 해석
        self._voice = _DEFAULT_VOICE if (not name or name.endswith(".onnx")) else name
        self.sample_rate = sample_rate

    def synthesize(self, text: str) -> np.ndarray:
        """텍스트 → mono int16 오디오 배열 (sample_rate 는 self.sample_rate)."""
        if not text.strip():
            return np.zeros(0, dtype=np.int16)

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            subprocess.run(
                [
                    "say",
                    "-v", self._voice,
                    "-o", path,
                    f"--data-format=LEI16@{self.sample_rate}",
                    text,
                ],
                check=True,
                capture_output=True,
            )
            with wave.open(path, "rb") as w:
                channels = w.getnchannels()
                raw = w.readframes(w.getnframes())
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

        pcm = np.frombuffer(raw, dtype=np.int16)
        if channels > 1:  # 안전: 다채널이면 모노로 다운믹스
            pcm = pcm.reshape(-1, channels).mean(axis=1).astype(np.int16)
        return pcm
