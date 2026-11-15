# 건영1차아파트 안내방송시스템

관리사무소에서 방송 문안을 입력하면 AI 아나운서 음성으로 안내방송을 만들어 주는 웹페이지입니다.

**배포 주소**
- https://ky1apt.dothome.co.kr — 닷홈 (화면만 올림, 음성은 Render 서버가 만듦)
- https://geonyoung1-broadcast.onrender.com — Render (화면 + 음성 서버)

- 자주 쓰는 방송 문안 6종 (단수, 승강기 점검, 세대 소독, 차량 이동, 분리수거, 소방 훈련)
- 시작·끝 차임벨(도-미-솔-도), 방송 횟수 1~3회, 방송 중지
- 오늘 방송 기록에서 바로 재방송·음성 파일 저장 (저장 파일에는 차임벨 제외)
- 목소리: Microsoft Edge 신경망 3종 (선희·인준·현수, 인터넷 필요)

## 내 PC에서 실행 (Windows)
`start_server.bat` 더블클릭 → http://localhost:8100

## 테스트
```
python -m pip install -r requirements-local.txt
python -m pytest tests -v
```

## 배포 (Render)
`render.yaml`에 설정이 들어 있습니다. Render에서 이 GitHub 저장소를 Blueprint로 연결하면
`main` 브랜치에 올릴 때마다 자동으로 다시 배포됩니다.
무료 요금제는 15분 동안 접속이 없으면 잠들고, 다음 첫 접속 때 깨어나는 데 30~60초가 걸립니다.

## 닷홈 업로드
닷홈 무료 호스팅은 PHP용이라 Python 서버를 돌릴 수 없습니다. 그래서 화면만 닷홈에 올리고,
음성은 Render 서버의 `/api/tts`를 부릅니다 (`app.py`의 `ALLOWED_ORIGINS`가 닷홈 주소만 허용).

1. `python build_dothome.py` → `dist_dothome/index.html` 생성
2. 닷홈 FTP(또는 웹 파일관리자)로 `html` 폴더의 기존 `index.html`을 이 파일로 교체

화면을 고치면 `static/index.html`을 수정한 뒤 1~2를 다시 하면 됩니다.

| 파일 | 역할 |
|---|---|
| `app.py` | 서버 (음성 합성 API `/api/tts`, 화면 제공) |
| `static/index.html` | 화면 전부 |
| `requirements.txt` | 배포 서버용 패키지 |
| `requirements-local.txt` | 개발용 (테스트 패키지 포함) |
| `render.yaml` | Render 배포 설정 |
| `build_dothome.py` | 닷홈 업로드용 화면 만들기 |
