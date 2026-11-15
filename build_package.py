"""다른 PC로 옮길 설치용 압축 파일을 만든다.

실행: python build_package.py  →  dist/건영1차_안내방송_설치본.zip
압축을 풀고 start_server.bat 을 더블클릭하면 Python·패키지가 자동 설치된다.
"""
import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOP = "건영1차_안내방송"
OUT = os.path.join(BASE_DIR, "dist", f"{TOP}_설치본.zip")

FILES = [
    "app.py",
    "static/index.html",
    "requirements.txt",
    "start_server.bat",
    "make_shortcut.ps1",
    "설치_안내.txt",
]
CRLF_FILES = {"start_server.bat", "설치_안내.txt"}       # cmd·메모장용 줄바꿈
BOM_FILES = {"make_shortcut.ps1"}                        # Windows PowerShell 5.1이 한글을 읽도록


def file_bytes(rel: str) -> bytes:
    with open(os.path.join(BASE_DIR, rel), "rb") as f:
        data = f.read()
    if rel in CRLF_FILES or rel in BOM_FILES:
        data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if rel in BOM_FILES and not data.startswith(b"\xef\xbb\xbf"):
        data = b"\xef\xbb\xbf" + data
    return data


def build() -> str:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            z.writestr(f"{TOP}/{rel}", file_bytes(rel))
    return OUT


if __name__ == "__main__":
    path = build()
    print(path, f"{os.path.getsize(path) / 1024:.0f} KB")
