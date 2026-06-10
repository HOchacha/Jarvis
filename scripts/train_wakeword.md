# 웨이크워드 "자비스" 설정

## 가장 빠른 시작 — 내장 모델

openWakeWord에는 `hey_jarvis` 내장 모델이 있어 바로 쓸 수 있습니다. 최초 실행 시
자동 다운로드됩니다. `.env` 기본값:

```
JARVIS_WAKEWORD_MODEL=hey_jarvis
JARVIS_WAKEWORD_THRESHOLD=0.5
```

"Hey Jarvis"에 반응합니다. 한국어 발음 "헤이 자비스"로도 어느 정도 동작합니다.
오인식이 많으면 `JARVIS_WAKEWORD_THRESHOLD` 를 0.6~0.7로 올리세요.

## 한국어 "자비스" 커스텀 모델 (선택, 더 자연스러움)

openWakeWord는 커스텀 웨이크워드를 학습할 수 있습니다(합성 음성으로 자동 학습).

1. 공식 학습 노트북 사용 (Colab 권장):
   https://github.com/dscripka/openWakeWord  → `automatic_model_training` 안내
2. 학습 시 단어를 "자비스"로 지정 → `jarvis.onnx` 산출
3. 파일을 `secrets/jarvis.onnx` 에 두고 `.env` 수정:

```
JARVIS_WAKEWORD_MODEL=secrets/jarvis.onnx
```

> 라즈베리파이(ARM)에서는 onnxruntime 설치가 가벼워 권장됩니다.
> 학습은 PC/Colab에서 하고, 산출된 `.onnx` 만 파이로 복사하세요.
