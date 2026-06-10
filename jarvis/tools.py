"""Claude 가 사용할 도구 정의 + 실행 디스패치.

도구 = 자비스가 실제 세상에 손을 뻗는 통로:
  - 일정 읽기/추가 (구글 캘린더)
  - 생활 기록 남기기 / 최근 기록 조회 (생활 교정 근거)
  - 사용자 선호/목표 기억
  - 현재 시각
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from jarvis import store
from jarvis.calendar_client import CalendarClient

# Anthropic Messages API tool 스키마
TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "get_schedule",
        "description": (
            "구글 캘린더에서 일정을 가져온다. 사용자가 '오늘/내일/이번주 일정'을 "
            "물어보거나, 생활 교정을 위해 일정 맥락이 필요할 때 호출한다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "오늘=0, 내일=1. 기준 시작일.",
                },
                "span_days": {
                    "type": "integer",
                    "description": "조회 기간(일). 하루=1, 이번주=7.",
                },
            },
            "required": ["days_ahead", "span_days"],
        },
    },
    {
        "name": "create_event",
        "description": "구글 캘린더에 새 일정을 추가한다. 시각은 ISO8601(현지시각).",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "일정 제목"},
                "start_iso": {
                    "type": "string",
                    "description": "시작 시각 ISO8601, 예: 2026-06-11T14:00:00",
                },
                "end_iso": {
                    "type": "string",
                    "description": "종료 시각 ISO8601",
                },
                "location": {"type": "string", "description": "장소(선택)"},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
    },
    {
        "name": "log_activity",
        "description": (
            "사용자의 생활 기록을 남긴다. 사용자가 기상/수면/운동/식사/집중/기분 등을 "
            "보고하면 호출. category 예: 기상, 수면, 운동, 식사, 집중, 기분."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "note": {"type": "string", "description": "내용. 예: '7시 기상, 개운함'"},
            },
            "required": ["category", "note"],
        },
    },
    {
        "name": "get_recent_logs",
        "description": (
            "최근 생활 기록을 조회한다. 생활 패턴을 짚어 교정 조언을 할 때 근거로 쓴다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "최근 며칠. 기본 7."},
                "category": {
                    "type": "string",
                    "description": "특정 카테고리만(선택). 예: 수면",
                },
            },
            "required": ["days"],
        },
    },
    {
        "name": "remember_preference",
        "description": (
            "사용자의 목표/선호를 장기 기억한다. 예: 목표='매일 7시 기상', "
            "선호='저녁엔 커피 금지'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "get_current_time",
        "description": "현재 날짜와 시각, 요일을 가져온다.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


class Tools:
    def __init__(self, calendar: CalendarClient | None, timezone: str):
        self._cal = calendar
        self._tz = ZoneInfo(timezone)

    def _need_cal(self) -> CalendarClient:
        if self._cal is None:
            raise RuntimeError("캘린더가 설정되지 않았습니다 (구글 OAuth 미완료).")
        return self._cal

    def dispatch(self, name: str, args: dict[str, Any]) -> str:
        """도구 실행. 결과는 Claude 에게 돌려줄 문자열(JSON)."""
        try:
            result = self._run(name, args)
        except Exception as e:  # noqa: BLE001 — 에러도 Claude 에게 전달해 대처하게 함
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        return json.dumps(result, ensure_ascii=False)

    def _run(self, name: str, args: dict[str, Any]) -> Any:
        if name == "get_schedule":
            return self._need_cal().between(
                days_ahead=args.get("days_ahead", 0),
                span_days=args.get("span_days", 1),
            )
        if name == "create_event":
            return self._need_cal().create_event(
                summary=args["summary"],
                start_iso=args["start_iso"],
                end_iso=args["end_iso"],
                location=args.get("location", ""),
            )
        if name == "log_activity":
            return store.log_activity(args["category"], args["note"])
        if name == "get_recent_logs":
            return store.recent_logs(
                days=args.get("days", 7), category=args.get("category")
            )
        if name == "remember_preference":
            return store.set_preference(args["key"], args["value"])
        if name == "get_current_time":
            now = datetime.now(self._tz)
            weekday = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
            return {
                "datetime": now.isoformat(timespec="minutes"),
                "weekday": f"{weekday}요일",
            }
        raise ValueError(f"알 수 없는 도구: {name}")
