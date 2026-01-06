# Claude Clone

CLI 기반 AI 코딩 어시스턴트 - Claude Code에서 영감을 받아 만든 프로젝트

## 설치

```bash
# uv 사용 (권장)
uv pip install -e ".[dev]"

# pip 사용
pip install -e ".[dev]"
```

## 실행

```bash
claude-clone
```

## 개발 현황

- [x] 아키텍처 설계
- [x] 프로젝트 초기화
- [ ] MVP Alpha 개발 중

## 문서

- [아키텍처 설계서](docs/architecture.md)
- [개발 로드맵](docs/roadmap.md)
- [유저 스토리](docs/user-stories-v0.0.3.md)

## 기술 스택

- Python 3.11+
- LangGraph + LangChain
- Gemini 3.0 Flash Preview (MVP)
- Typer + Rich + prompt_toolkit

## 라이선스

MIT
