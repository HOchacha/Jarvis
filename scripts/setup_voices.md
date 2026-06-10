# Piper 한국어 음성(TTS) 설치

Piper는 오프라인 TTS입니다. 음성 모델은 `.onnx` + `.onnx.json` 한 쌍입니다.

## 한국어 음성 받기

Piper 공식 음성 저장소(Hugging Face `rhasspy/piper-voices`)에서 한국어(`ko_KR`)를 받습니다.

```bash
mkdir -p secrets/voices
cd secrets/voices

# 예시: 한국어 음성 (실제 사용 가능한 파일명은 저장소에서 확인)
#   https://huggingface.co/rhasspy/piper-voices/tree/main/ko/ko_KR
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/ko/ko_KR"

# (아래 <voice>/<quality> 부분은 저장소 트리에서 실제 경로로 바꾸세요)
wget "$BASE/<voice>/<quality>/ko_KR-<voice>-<quality>.onnx"
wget "$BASE/<voice>/<quality>/ko_KR-<voice>-<quality>.onnx.json"
```

받은 `.onnx` 경로를 `.env` 의 `JARVIS_PIPER_VOICE` 에 적으세요. 예:

```
JARVIS_PIPER_VOICE=secrets/voices/ko_KR-<voice>-<quality>.onnx
```

> 한국어 Piper 음성 종류가 제한적일 수 있습니다. 품질이 아쉬우면:
> - **medium/high** 품질 모델을 우선 선택
> - 또는 STT는 로컬 유지하되 TTS만 클라우드(ElevenLabs/Cartesia)로 바꾸는
>   '하이브리드'로 전환 (tts.py 만 교체하면 됨 — 인터페이스 동일).

## 동작 확인

```bash
python - <<'PY'
from config import Config
from jarvis.tts import TTS
from jarvis import audio
cfg = Config.load()
tts = TTS(cfg.piper_voice)
audio.play(tts.synthesize("안녕하세요, 자비스입니다."), tts.sample_rate)
PY
```
