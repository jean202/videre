---
name: study-notes
description: YouTube 강의 영상에서 자막 + 프레임 캡처로 학습 노트(Markdown)를 생성한다.
argument-hint: "[YouTube URL 또는 로컬 영상 파일]"
disable-model-invocation: true
---

## 학습 노트 생성

대상: **$ARGUMENTS**

### 사용법
```bash
python lecture_doc_builder.py --url "https://youtube.com/watch?v=..." --output output/
python lecture_doc_builder.py --file lecture.mp4 --output output/
```

### 출력물
- `output/study_notes.md` — 타임스탬프 기반 학습 노트
- `output/frames/` — 주기적 프레임 캡처 이미지

### 옵션
- `--lang`: 자막 언어 (기본: ko)
- `--interval`: 프레임 캡처 간격 (초)

### 기술 스택
- VTT 자막 다운로드/파싱
- FFmpeg 프레임 캡처
- Markdown 생성
