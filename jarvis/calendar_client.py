"""구글 캘린더 연동. 최초 1회 브라우저 OAuth, 이후 토큰 재사용.

설정: scripts/setup_google.md 참고.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarClient:
    def __init__(
        self,
        client_secret: str,
        token_path: str,
        calendar_id: str = "primary",
        timezone: str = "Asia/Seoul",
    ):
        self.calendar_id = calendar_id
        self.tz = ZoneInfo(timezone)
        self._service = self._build_service(client_secret, token_path)

    def _build_service(self, client_secret: str, token_path: str):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        tok = Path(token_path)
        if tok.exists():
            creds = Credentials.from_authorized_user_file(str(tok), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(client_secret).exists():
                    raise RuntimeError(
                        f"구글 OAuth 클라이언트 시크릿이 없습니다: {client_secret}\n"
                        f"scripts/setup_google.md 참고."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret, SCOPES
                )
                creds = flow.run_local_server(port=0)
            tok.parent.mkdir(parents=True, exist_ok=True)
            tok.write_text(creds.to_json(), encoding="utf-8")
        return build("calendar", "v3", credentials=creds)

    def _list(self, start: datetime, end: datetime) -> list[dict[str, Any]]:
        resp = (
            self._service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        out = []
        for ev in resp.get("items", []):
            start_raw = ev["start"].get("dateTime", ev["start"].get("date"))
            end_raw = ev["end"].get("dateTime", ev["end"].get("date"))
            out.append(
                {
                    "summary": ev.get("summary", "(제목 없음)"),
                    "start": start_raw,
                    "end": end_raw,
                    "location": ev.get("location", ""),
                    "all_day": "date" in ev["start"],
                }
            )
        return out

    def today(self) -> list[dict[str, Any]]:
        now = datetime.now(self.tz)
        start = datetime.combine(now.date(), time.min, tzinfo=self.tz)
        end = start + timedelta(days=1)
        return self._list(start, end)

    def between(self, days_ahead: int = 0, span_days: int = 1) -> list[dict[str, Any]]:
        """오늘 기준 days_ahead 일부터 span_days 동안의 일정."""
        now = datetime.now(self.tz)
        start = datetime.combine(
            now.date() + timedelta(days=days_ahead), time.min, tzinfo=self.tz
        )
        end = start + timedelta(days=span_days)
        return self._list(start, end)

    def create_event(
        self, summary: str, start_iso: str, end_iso: str, location: str = ""
    ) -> dict[str, Any]:
        body = {
            "summary": summary,
            "start": {"dateTime": start_iso, "timeZone": str(self.tz)},
            "end": {"dateTime": end_iso, "timeZone": str(self.tz)},
        }
        if location:
            body["location"] = location
        ev = (
            self._service.events()
            .insert(calendarId=self.calendar_id, body=body)
            .execute()
        )
        return {"summary": ev.get("summary"), "id": ev.get("id"), "link": ev.get("htmlLink")}
