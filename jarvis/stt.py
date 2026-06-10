"""로컬 음성→텍스트 (faster-whisper). 오프라인."""
from __future__ import annotations

import numpy as np


class STT:
    def __init__(self, model_size: str, device: str, compute_type: str):
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )

    def transcribe(self, pcm16: np.ndarray, language: str = "ko") -> str:
        """16kHz int16 오디오 → 텍스트."""
        if pcm16.size == 0:
            return ""
        audio = pcm16.astype(np.float32) / 32768.0
        segments, _info = self._model.transcribe(
            audio,
            language=language,
            vad_filter=True,
            beam_size=5,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
