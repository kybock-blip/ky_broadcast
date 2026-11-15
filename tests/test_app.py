"""건영1차아파트 안내방송시스템 서버 테스트 (음성 합성은 가짜 응답 — 네트워크 없음)
실행: python -m pytest tests -v
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as server
from fastapi.testclient import TestClient

client = TestClient(server.app)


@pytest.fixture
def fake_edge(monkeypatch):
    calls = []

    class FakeCommunicate:
        def __init__(self, text, **kw):
            calls.append((text, kw))

        async def stream(self):
            yield {"type": "audio", "data": b"ID3fake-mp3"}

    monkeypatch.setattr(server, "tts_audio_cache", {})
    monkeypatch.setattr(server.edge_tts, "Communicate", FakeCommunicate)
    return calls


def test_page_title():
    r = client.get("/")
    assert r.status_code == 200
    assert "<title>건영1차아파트 안내방송시스템</title>" in r.text
    assert "산림" not in r.text, "산림 큐레이터 흔적이 남지 않아야 함"


def test_tts_default_and_cache(fake_edge):
    assert client.post("/api/tts", json={"text": "  "}).status_code == 400
    r = client.post("/api/tts", json={"text": "관리사무소에서 안내 말씀 드립니다."})
    assert r.status_code == 200 and r.headers["content-type"].startswith("audio/mpeg")
    assert fake_edge[0][1] == {"voice": "ko-KR-SunHiNeural", "rate": "-4%"}
    client.post("/api/tts", json={"text": "관리사무소에서 안내 말씀 드립니다."})
    assert len(fake_edge) == 1, "같은 문안은 다시 만들지 않음"


def test_tts_options_and_bad_values(fake_edge):
    client.post("/api/tts", json={"text": "가", "voice": "ko-KR-InJoonNeural", "rate": "+10%", "pitch": "+5Hz"})
    assert fake_edge[-1][1] == {"voice": "ko-KR-InJoonNeural", "rate": "+10%", "pitch": "+5Hz"}
    client.post("/api/tts", json={"text": "나", "voice": "en-US-Fake", "rate": "fast", "pitch": "high"})
    assert fake_edge[-1][1] == {"voice": "ko-KR-SunHiNeural", "rate": "-4%"}


def test_tts_supertonic(monkeypatch):
    calls = []
    monkeypatch.setattr(server, "SUPERTONIC_AVAILABLE", True)
    monkeypatch.setattr(server, "tts_audio_cache", {})
    monkeypatch.setattr(server, "_synthesize_supertonic", lambda t, v, s: calls.append((t, v, s)) or b"RIFFwav")
    r = client.post("/api/tts", json={"text": "단수 안내", "voice": "supertonic-M2", "rate": "+10%"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("audio/wav")
    assert calls == [("단수 안내", "M2", 1.1)]


def test_tts_failure_returns_502(monkeypatch):
    class Broken:
        def __init__(self, *a, **k): pass
        async def stream(self):
            raise ConnectionError("offline")
            yield
    monkeypatch.setattr(server, "tts_audio_cache", {})
    monkeypatch.setattr(server.edge_tts, "Communicate", Broken)
    r = client.post("/api/tts", json={"text": "인터넷 끊김"})
    assert r.status_code == 502 and "인터넷" in r.json()["detail"]


def test_supertonic_hidden_when_not_installed(monkeypatch):
    monkeypatch.setattr(server, "SUPERTONIC_AVAILABLE", False)
    assert client.get("/api/voices").json() == {"supertonic": False}
    r = client.post("/api/tts", json={"text": "가", "voice": "supertonic-F1"})
    assert r.status_code == 400 and "Edge" in r.json()["detail"]


def test_healthz():
    assert client.get("/healthz").json() == {"ok": True}


def test_cors_allows_only_dothome():
    ok = client.options("/api/tts", headers={
        "Origin": "https://ky1apt.dothome.co.kr",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == "https://ky1apt.dothome.co.kr"
    bad = client.get("/api/voices", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in bad.headers


def test_build_dothome_injects_api_base(tmp_path, monkeypatch):
    import build_dothome
    monkeypatch.setattr(build_dothome, "OUT_DIR", str(tmp_path))
    html = open(build_dothome.build(), encoding="utf-8").read()
    assert 'window.TTS_API_BASE = "https://geonyoung1-broadcast.onrender.com"' in html
    assert html.index("TTS_API_BASE =") < html.index("const API_BASE"), "주소가 화면 스크립트보다 먼저 정해져야 함"
