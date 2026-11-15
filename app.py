"""건영1차아파트 안내방송시스템 — 관리사무소용 AI 음성 안내방송 서버
실행: start_server.bat 더블클릭 → http://localhost:8100
"""
import io
import os
import re
import asyncio
import importlib.util
from typing import Optional

import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="건영1차아파트 안내방송시스템")

# 화면을 다른 주소(닷홈)에 올린 경우 그 주소에서만 음성 API를 부를 수 있게 허용
DEFAULT_ORIGINS = "https://ky1apt.dothome.co.kr,http://ky1apt.dothome.co.kr"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MAX_TEXT = 3000
DEFAULT_VOICE = "ko-KR-SunHiNeural"
DEFAULT_RATE = "-4%"
ALLOWED_TTS_VOICES = {
    "ko-KR-SunHiNeural",
    "ko-KR-InJoonNeural",
    "ko-KR-HyunsuMultilingualNeural",
}
SUPERTONIC_VOICES = {f"supertonic-{g}{i}": f"{g}{i}" for g in ("F", "M") for i in range(1, 6)}
RATE_PATTERN = re.compile(r"^[+-]\d{1,3}%$")
PITCH_PATTERN = re.compile(r"^[+-]\d{1,3}Hz$")
CACHE_LIMIT = 60
# Supertonic은 무거워서(onnxruntime·모델 내려받기) 내 PC에서만 설치한다. 배포 서버에는 없으면 목록에서 숨김
SUPERTONIC_AVAILABLE = (importlib.util.find_spec("supertonic") is not None
                        and importlib.util.find_spec("soundfile") is not None)


class TtsRequest(BaseModel):
    text: str
    voice: Optional[str] = DEFAULT_VOICE
    rate: Optional[str] = DEFAULT_RATE
    pitch: Optional[str] = "+0Hz"


tts_audio_cache = {}
_supertonic_engine = None
_supertonic_styles = {}


def _remember(key, audio: bytes) -> None:
    if len(tts_audio_cache) > CACHE_LIMIT:
        tts_audio_cache.clear()
    tts_audio_cache[key] = audio


def _synthesize_supertonic(text: str, voice_name: str, speed: float) -> bytes:
    """Supertonic 로컬 음성 (처음 한 번 모델을 내려받음, 인터넷 없이 동작)"""
    global _supertonic_engine
    if _supertonic_engine is None:
        from supertonic import TTS
        _supertonic_engine = TTS(auto_download=True)
    if voice_name not in _supertonic_styles:
        _supertonic_styles[voice_name] = _supertonic_engine.get_voice_style(voice_name=voice_name)
    import soundfile as sf
    wav, _ = _supertonic_engine.synthesize(
        text=text,
        voice_style=_supertonic_styles[voice_name],
        speed=speed,
        lang="ko",
    )
    buf = io.BytesIO()
    sf.write(buf, wav.squeeze(), _supertonic_engine.sample_rate, format="WAV")
    return buf.getvalue()


@app.post("/api/tts")
async def synthesize_tts(req: TtsRequest):
    text = (req.text or "").strip()[:MAX_TEXT]
    if not text:
        raise HTTPException(status_code=400, detail="방송할 문장이 비어 있습니다.")

    if req.voice in SUPERTONIC_VOICES:
        if not SUPERTONIC_AVAILABLE:
            raise HTTPException(status_code=400, detail="이 서버에서는 Supertonic 음성을 쓸 수 없습니다. Edge 목소리를 골라 주세요.")
        rate = req.rate if req.rate and RATE_PATTERN.match(req.rate) else "+0%"
        key = (text, req.voice, rate, "wav")
        if key in tts_audio_cache:
            return Response(content=tts_audio_cache[key], media_type="audio/wav")
        speed = max(0.7, min(2.0, 1.0 + int(rate[:-1]) / 100.0))
        try:
            audio = await asyncio.to_thread(_synthesize_supertonic, text, SUPERTONIC_VOICES[req.voice], speed)
        except Exception as e:
            print("Supertonic TTS error:", e)
            raise HTTPException(status_code=502, detail="Supertonic 음성 생성 실패")
        if not audio:
            raise HTTPException(status_code=502, detail="Supertonic 음성 생성 실패")
        _remember(key, audio)
        return Response(content=audio, media_type="audio/wav")

    voice = req.voice if req.voice in ALLOWED_TTS_VOICES else DEFAULT_VOICE
    rate = req.rate if req.rate and RATE_PATTERN.match(req.rate) else DEFAULT_RATE
    pitch = req.pitch if req.pitch and PITCH_PATTERN.match(req.pitch) else "+0Hz"
    key = (text, voice, rate, pitch)
    if key in tts_audio_cache:
        return Response(content=tts_audio_cache[key], media_type="audio/mpeg")
    kwargs = {"voice": voice, "rate": rate}
    if pitch != "+0Hz":
        kwargs["pitch"] = pitch
    buf = bytearray()
    try:
        async for chunk in edge_tts.Communicate(text, **kwargs).stream():
            if chunk.get("type") == "audio":
                buf.extend(chunk["data"])
    except Exception as e:
        print("TTS error:", e)
        raise HTTPException(status_code=502, detail="음성 생성 실패 (인터넷 연결을 확인해 주세요)")
    if not buf:
        raise HTTPException(status_code=502, detail="음성 생성 실패")
    audio = bytes(buf)
    _remember(key, audio)
    return Response(content=audio, media_type="audio/mpeg")


@app.get("/api/voices")
def list_voices():
    return {"supertonic": SUPERTONIC_AVAILABLE}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/")
def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
