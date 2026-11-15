"""닷홈(ky1apt.dothome.co.kr) 업로드용 화면 파일을 만든다.

닷홈 무료 호스팅은 PHP용이라 Python 서버를 돌릴 수 없으므로,
화면(index.html)만 닷홈에 올리고 음성 만들기는 Render 서버(/api/tts)를 부른다.

실행: python build_dothome.py  →  dist_dothome/index.html 을 닷홈 html 폴더에 올린다
"""
import os
import sys

API_BASE = "https://geonyoung1-broadcast.onrender.com"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE_DIR, "static", "index.html")
OUT_DIR = os.path.join(BASE_DIR, "dist_dothome")
MARK = "<script>\n    tailwind.config"


def build(api_base: str = API_BASE) -> str:
    with open(SRC, encoding="utf-8") as f:
        html = f.read()
    if MARK not in html:
        sys.exit("index.html 구조가 바뀌어 음성 서버 주소를 넣을 위치를 찾지 못했습니다.")
    inject = f'<script>window.TTS_API_BASE = "{api_base}";</script>\n  '
    html = html.replace(MARK, inject + MARK, 1)
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return out


if __name__ == "__main__":
    print("만든 파일:", build())
