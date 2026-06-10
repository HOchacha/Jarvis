"""아주 단순한 로컬 저장소 (JSON). 생활 교정의 '근거 데이터'가 여기 쌓인다.

- activity log: 사용자가 보고한 생활 기록 (기상/운동/식사/수면 등)
- preferences: 자비스가 기억해야 할 사용자 선호/목표
대화 메모리(대화 맥락)는 여기 두지 않는다 — 세션 휘발이 자연스러움.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from config import DATA_DIR

_LOG_FILE = DATA_DIR / "activity_log.jsonl"
_PREFS_FILE = DATA_DIR / "preferences.json"


def log_activity(category: str, note: str, when: str | None = None) -> dict[str, Any]:
    """생활 기록 한 줄 추가. category 예: 기상, 수면, 운동, 식사, 집중, 기분."""
    entry = {
        "ts": when or datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "note": note,
    }
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def recent_logs(days: int = 7, category: str | None = None) -> list[dict[str, Any]]:
    """최근 N일 생활 기록. 생활 교정/패턴 분석에 사용."""
    if not _LOG_FILE.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    out: list[dict[str, Any]] = []
    for line in _LOG_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        try:
            ts = datetime.fromisoformat(entry["ts"])
        except (ValueError, KeyError):
            continue
        if ts < cutoff:
            continue
        if category and entry.get("category") != category:
            continue
        out.append(entry)
    return out


def get_preferences() -> dict[str, Any]:
    if not _PREFS_FILE.exists():
        return {}
    return json.loads(_PREFS_FILE.read_text(encoding="utf-8"))


def set_preference(key: str, value: Any) -> dict[str, Any]:
    """자비스가 기억할 사용자 선호/목표 저장. 예: 목표='매일 7시 기상'."""
    prefs = get_preferences()
    prefs[key] = value
    _PREFS_FILE.write_text(
        json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return prefs
