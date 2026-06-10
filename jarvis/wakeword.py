"""웨이크워드 감지 — "자비스" 부르면 깨어난다.

openWakeWord 사용. 기본 제공 모델(hey_jarvis 등)로 바로 시작 가능하고,
커스텀 한국어 "자비스" 모델을 학습하면 경로를 넣어 교체한다
(scripts/train_wakeword.md 참고).
"""
from __future__ import annotations

import numpy as np

SAMPLE_RATE = 16_000  # openWakeWord 요구 샘플레이트
FRAME_SAMPLES = 1280  # 80ms 프레임 (권장)


class WakeWord:
    def __init__(self, model: str, threshold: float = 0.5):
        from openwakeword.model import Model
        from openwakeword.utils import download_models

        # 내장 모델 사용 시 최초 1회 다운로드
        if not model.endswith(".onnx") and not model.endswith(".tflite"):
            download_models([model])
            self._model = Model(wakeword_models=[model])
            self._key = model
        else:
            self._model = Model(wakeword_models=[model])
            # 커스텀 모델은 파일명이 키가 됨
            self._key = next(iter(self._model.models.keys()))
        self._threshold = threshold

    def detect(self, pcm16: np.ndarray) -> bool:
        """16kHz int16 프레임을 받아 웨이크워드면 True.

        pcm16: shape (FRAME_SAMPLES,) int16
        """
        scores = self._model.predict(pcm16)
        return scores.get(self._key, 0.0) >= self._threshold

    def reset(self) -> None:
        """대화 진입 후 내부 상태 초기화 (연속 트리거 방지)."""
        self._model.reset()
