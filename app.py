"""건영1차아파트 안내방송시스템 — 관리사무소용 AI 음성 안내방송 서버
실행: start_server.bat 더블클릭 → http://localhost:8100
음성은 Microsoft Edge 신경망 음성(edge-tts)으로 만든다 (인터넷 필요).
"""
import os
import re
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
RATE_PATTERN = re.compile(r"^[+-]\d{1,3}%$")
PITCH_PATTERN = re.compile(r"^[+-]\d{1,3}Hz$")
CACHE_LIMIT = 60


class TtsRequest(BaseModel):
    text: str
    voice: Optional[str] = DEFAULT_VOICE
    rate: Optional[str] = DEFAULT_RATE
    pitch: Optional[str] = "+0Hz"


tts_audio_cache = {}


def _remember(key, audio: bytes) -> None:
    if len(tts_audio_cache) > CACHE_LIMIT:
        tts_audio_cache.clear()
    tts_audio_cache[key] = audio


@app.post("/api/tts")
async def synthesize_tts(req: TtsRequest):
    text = (req.text or "").strip()[:MAX_TEXT]
    if not text:
        raise HTTPException(status_code=400, detail="방송할 문장이 비어 있습니다.")

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
    """이전 버전 화면(닷홈에 이미 올린 파일 등) 호환용: Supertonic은 더 이상 쓰지 않는다"""
    return {"supertonic": False}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/")
def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
