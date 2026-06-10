"""자비스의 두뇌 — Claude Opus 4.8.

역할:
  1) 일정 보고: 캘린더를 읽어 자연스럽게 브리핑
  2) 생활 교정: 생활 기록 + 일정 + 목표를 근거로 솔직하고 구체적인 코칭
대화 맥락을 유지하며, 필요할 때 도구를 호출한다(매뉴얼 tool-use 루프).
음성 대화이므로 답변은 짧고, 소리 내 읽기 좋게 만든다.
"""
from __future__ import annotations

import anthropic

from jarvis.tools import TOOL_DEFS, Tools

_SYSTEM_TEMPLATE = """\
너는 '{name}'의 개인 비서 자비스(JARVIS)다. 영화 속 자비스처럼, 신뢰할 수 있고 \
유능하며 곁에 있는 동반자다.

역할은 두 가지다:
1) 일정 보고 — 캘린더를 읽어 오늘/이번 주 할 일을 자연스럽게 브리핑한다.
2) 생활 교정 — 생활 기록과 목표, 일정을 근거로 솔직하고 구체적으로 코칭한다. \
막연한 응원이 아니라, 데이터에 기반해 짚어준다. 늦게 잤으면 짚고, 목표와 어긋나면 \
부드럽지만 분명하게 말한다.

성격/말투: {persona}

음성 대화 규칙(매우 중요):
- 답은 짧게. 보통 1~3문장. 소리 내 읽었을 때 자연스러워야 한다.
- 글머리표, 번호 목록, 마크다운, 이모지, 특수기호를 쓰지 마라. 말로 풀어라.
- 시각이나 날짜가 중요하면 추측하지 말고 get_current_time 도구를 먼저 호출한다.
- 일정을 물으면 get_schedule 로 실제 데이터를 확인하고 답한다. 지어내지 않는다.
- 사용자가 생활을 보고하면(기상/수면/운동 등) log_activity 로 기록한다.
- 교정 조언을 할 땐 get_recent_logs 로 패턴을 확인한 뒤 근거를 들어 말한다.
- 사용자가 목표/선호를 말하면 remember_preference 로 기억한다.
"""

# 음성 답변은 짧으므로 큰 max_tokens 불필요 → 비스트리밍으로 충분(타임아웃 위험 없음)
_MAX_TOKENS = 1024
_MAX_TOOL_HOPS = 6


class Brain:
    def __init__(self, api_key: str, model: str, tools: Tools, persona: str, user_name: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._tools = tools
        self._system = _SYSTEM_TEMPLATE.format(name=user_name, persona=persona)
        self._messages: list[dict] = []

    def respond(self, user_text: str) -> str:
        """사용자 발화 → 자비스 답변(텍스트). 도구는 내부에서 자동 처리."""
        self._messages.append({"role": "user", "content": user_text})
        return self._run_tool_loop()

    def system_turn(self, instruction: str) -> str:
        """사용자 발화 없이 자비스가 먼저 말하게 한다(예: 아침 브리핑).

        instruction 은 '지금 아침 일정 브리핑을 해줘' 같은 내부 지시.
        """
        self._messages.append({"role": "user", "content": instruction})
        return self._run_tool_loop()

    def _run_tool_loop(self) -> str:
        for _ in range(_MAX_TOOL_HOPS):
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                system=self._system,
                thinking={"type": "adaptive"},
                output_config={"effort": "low"},  # 음성 지연 최소화
                tools=TOOL_DEFS,
                messages=self._messages,
            )
            # 어시스턴트 응답(도구 호출 포함)을 히스토리에 보존
            self._messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason != "tool_use":
                return self._extract_text(resp)

            # 도구 실행 → 결과를 user turn 으로 되돌림
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    output = self._tools.dispatch(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output,
                        }
                    )
            self._messages.append({"role": "user", "content": tool_results})

        return "음... 처리하다 막혔어. 다시 말해줄래?"

    @staticmethod
    def _extract_text(resp) -> str:
        parts = [b.text for b in resp.content if b.type == "text"]
        return " ".join(p.strip() for p in parts).strip()
