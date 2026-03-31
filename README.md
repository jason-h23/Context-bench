# ContextBench

AI 에이전트 컨텍스트 파일(CLAUDE.md, SOUL.md, rules/)을 진단하는 CLI 도구.

중복 규칙, 모순되는 지시, 모호한 표현, 토큰 낭비를 찾아내고 수정 방법을 제안합니다.

## Why?

AI 에이전트의 성능이 기대에 못 미칠 때, 대부분 더 비싼 모델로 교체합니다.
하지만 실제 원인은 **컨텍스트 설계**에 있는 경우가 더 많습니다.

- CLAUDE.md와 rules/ 파일 사이에 같은 규칙이 반복되고 있지 않은가?
- 서로 모순되는 지시가 섞여 있지 않은가?
- 실제로 토큰의 몇 %가 낭비되고 있는가?

ContextBench는 이 질문에 데이터로 답합니다.

## Quick Start

```bash
# 설치
git clone https://github.com/jason-h23/Context-bench.git
cd Context-bench
uv venv && uv pip install -e .

# API 키 설정
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 진단
contextbench diagnose CLAUDE.md rules/
```

## Commands

### `contextbench diagnose` — 컨텍스트 진단

```bash
# 전체 진단 (로컬 체크 + Claude API 분석)
contextbench diagnose CLAUDE.md rules/

# 로컬 체크만 (무료, API 불필요)
contextbench diagnose --no-llm CLAUDE.md rules/

# 마크다운으로 저장
contextbench diagnose --format markdown --output report.md CLAUDE.md

# 모델 변경
contextbench diagnose --model claude-sonnet-4-6 CLAUDE.md
```

출력 예시:
```
  Context Diagnosis Report
  ========================

  Files Analyzed: 5
  Total Tokens:   2,438
  Estimated Waste: ~1,110 tokens (46%)
  Issues Found:   11

  [HIGH] 불변성(Immutability) 원칙 중복
    golden-principles.md:L5-L9
    coding-style.md:L3-L21
    불변성에 대한 설명이 3곳에서 반복됨.
    Fix: golden-principles.md에서 '왜'만 유지, coding-style.md의 코드 예제 통합.
    ~180 tokens

  [HIGH] 결론 먼저 원칙 중복
    golden-principles.md:L23-L27
    interaction.md:L19-L33
    ...

  Token Breakdown:
    golden-principles.md              725 tokens  █████░░░░░░░░░░░░░░░ 30%
    CLAUDE.md                         703 tokens  █████░░░░░░░░░░░░░░░ 29%
    interaction.md                    474 tokens  ███░░░░░░░░░░░░░░░░░ 19%
    coding-style.md                   333 tokens  ██░░░░░░░░░░░░░░░░░░ 14%
    security.md                       203 tokens  █░░░░░░░░░░░░░░░░░░░  8%
```

### `contextbench tokencount` — 토큰 카운트

```bash
# 파일별 토큰 수
contextbench tokencount CLAUDE.md rules/

# 섹션별 breakdown
contextbench tokencount CLAUDE.md --breakdown
```

API 호출 없이 로컬에서 즉시 실행됩니다 (tiktoken 기반).

### `contextbench compare` — 버전 비교

```bash
contextbench compare CLAUDE.md.bak CLAUDE.md
```

수정 전/후 토큰 변화, 해결된 이슈, 새로 발생한 이슈를 비교합니다.

## What It Checks

| 검사 항목 | 로컬 (무료) | LLM 분석 |
|----------|:-----------:|:--------:|
| 토큰 카운트 | ✅ | - |
| 파일 간 동일 내용 탐지 | ✅ | - |
| 70%+ 유사도 탐지 | ✅ | - |
| 중복/겹치는 지시 | - | ✅ |
| 모순되는 규칙 | - | ✅ |
| 모호한 표현 | - | ✅ |
| 토큰 낭비 추정 | - | ✅ |
| 미사용 규칙 | - | ✅ |
| 수정 제안 | - | ✅ |

## Supported Context Files

- `CLAUDE.md` — Claude Code 프로젝트 설정
- `SOUL.md` — OpenClaw 에이전트 정체성
- `AGENTS.md` — 에이전트 운영 규칙
- `rules/*.md` — 규칙 파일 디렉토리
- `.claude/rules/*.md` — Claude Code 규칙
- 기타 모든 `.md` 파일

## Requirements

- Python 3.12+
- Anthropic API 키 (`diagnose` 명령에 필요, `tokencount`는 불필요)

## License

MIT
