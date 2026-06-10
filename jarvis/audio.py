"""마이크 입력 / 스피커 출력 + 발화구간(VAD) 기반 턴 종료 감지.

마이크는 16kHz mono int16, 80ms(1280 샘플) 블록으로 공급한다.
 - 웨이크워드(openWakeWord)는 1280 샘플 블록을 그대로 쓴다.
 - webrtcvad 는 10/20/30ms 프레임만 받으므로, 블록을 320 샘플(20ms)로 쪼개 먹인다.

흐름:
  - frames():            1280 샘플 블록 스트림 (웨이크워드용)
  - record_utterance():  말이 끝날 때까지 녹음 → int16 배열 (STT용)
  - play() / play_interruptible(): TTS 오디오 재생 (후자는 바지인 지원)
"""
from __future__ import annotations

import queue
from collections.abc import Iterator

import numpy as np
import sounddevice as sd
import webrtcvad

SAMPLE_RATE = 16_000
BLOCK_SAMPLES = 1280          # 80ms — openWakeWord 권장
VAD_FRAME_SAMPLES = 320       # 20ms — webrtcvad 유효 프레임
VAD_FRAME_MS = 20


def _vad_subframes(block: np.ndarray) -> Iterator[np.ndarray]:
    """1280 샘플 블록 → 320 샘플 4개."""
    for i in range(0, len(block) - VAD_FRAME_SAMPLES + 1, VAD_FRAME_SAMPLES):
        yield block[i : i + VAD_FRAME_SAMPLES]


class Microphone:
    def __init__(self, block_samples: int = BLOCK_SAMPLES):
        self._q: queue.Queue[np.ndarray] = queue.Queue()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=block_samples,
            callback=self._cb,
        )

    def _cb(self, indata, frames, time_info, status):  # noqa: ANN001
        self._q.put(indata[:, 0].copy())

    def __enter__(self) -> "Microphone":
        self._stream.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stream.stop()
        self._stream.close()

    def drain(self) -> None:
        """큐에 쌓인 프레임 버리기 (TTS 재생 동안 들어온 자기 목소리 제거 등)."""
        while not self._q.empty():
            try:
                self._q.get_nowait()
            except queue.Empty:
                break

    def frames(self) -> Iterator[np.ndarray]:
        while True:
            yield self._q.get()

    def record_utterance(
        self,
        max_seconds: float = 15.0,
        silence_ms: int = 800,
        start_timeout_s: float = 6.0,
        vad_aggressiveness: int = 2,
    ) -> np.ndarray:
        """말이 끝날 때까지(침묵 silence_ms 지속) 녹음. 시작이 없으면 빈 배열."""
        vad = webrtcvad.Vad(vad_aggressiveness)
        collected: list[np.ndarray] = []
        started = False
        silent_subframes = 0
        silence_limit = silence_ms // VAD_FRAME_MS
        max_subframes = int(max_seconds * 1000 / VAD_FRAME_MS)
        start_limit = int(start_timeout_s * 1000 / VAD_FRAME_MS)
        count = 0

        for block in self.frames():
            for sub in _vad_subframes(block):
                count += 1
                is_speech = vad.is_speech(sub.tobytes(), SAMPLE_RATE)
                if is_speech:
                    started = True
                    silent_subframes = 0
                    collected.append(sub)
                elif started:
                    silent_subframes += 1
                    collected.append(sub)
                    if silent_subframes >= silence_limit:
                        return _concat(collected)
                else:
                    if count >= start_limit:  # 아무 말도 시작 안 함 → 포기
                        return np.zeros(0, dtype=np.int16)
                if count >= max_subframes:
                    return _concat(collected)
        return _concat(collected)


def _concat(frames: list[np.ndarray]) -> np.ndarray:
    return np.concatenate(frames) if frames else np.zeros(0, dtype=np.int16)


def play(pcm16: np.ndarray, sample_rate: int) -> None:
    if pcm16.size == 0:
        return
    sd.play(pcm16, samplerate=sample_rate)
    sd.wait()


def play_interruptible(pcm16: np.ndarray, sample_rate: int, mic: Microphone) -> bool:
    """재생 중 사용자가 ~100ms 이상 말하면 멈춘다(바지인). 끊겼으면 True."""
    if pcm16.size == 0:
        return False
    vad = webrtcvad.Vad(2)
    mic.drain()
    sd.play(pcm16, samplerate=sample_rate)
    speech_run = 0
    stream = sd.get_stream()
    while stream is not None and stream.active:
        try:
            block = mic._q.get(timeout=0.05)
        except queue.Empty:
            continue
        for sub in _vad_subframes(block):
            if vad.is_speech(sub.tobytes(), SAMPLE_RATE):
                speech_run += 1
                if speech_run >= 5:
                    sd.stop()
                    return True
            else:
                speech_run = 0
    return False
