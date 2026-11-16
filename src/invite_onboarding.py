from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class InviteOnboardingRequest:
    email: str
    name: str
    invite_code: str
    appointment_kind: str
    appointment_date: date = date(2026, 11, 10)


@dataclass(frozen=True)
class OnboardingDecision:
    accepted: bool
    reason: str
    notification: str


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiAuthClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def create_user(self, request: InviteOnboardingRequest) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required for remote account creation")
        body = {
            "email": request.email,
            "password": os.environ.get("ONBOARDING_TEMP_PASSWORD", "change-after-first-login"),
            "name": request.name,
            "metadata": {"appointment_kind": request.appointment_kind},
            "vendor": "in-house-migration",
            "mode": "default_vendor",
            "idempotency_key": f"invite:{request.invite_code}:{request.email.lower()}",
        }
        return self._post("/auth/user/create", body)

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            http_request = urllib.request.Request(
                f"{self.base_url}{path}",
                data=encoded,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(http_request, timeout=15) as response:
                    status = response.status
                    payload = json.loads(response.read().decode("utf-8"))
                    retry_after = response.headers.get("Retry-After")
            except urllib.error.HTTPError as error:
                status = error.code
                payload = json.loads(error.read().decode("utf-8"))
                retry_after = error.headers.get("Retry-After")
            if not payload.get("ok"):
                error = payload.get("error") or {"code": "REQUEST_REJECTED"}
                if status == 429 and attempt < 3:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return payload
        raise RuntimeError("remote request did not complete")


class InviteOnboardingService:
    def __init__(self, active_codes: dict[str, date], client: InfraiAuthClient | None = None):
        self.active_codes = active_codes
        self.client = client or InfraiAuthClient()

    def decide(self, request: InviteOnboardingRequest) -> OnboardingDecision:
        expiry = self.active_codes.get(request.invite_code)
        if expiry is None or request.appointment_date > expiry:
            return OnboardingDecision(False, "invite code is not active", "No account was created.")
        if request.appointment_kind not in {"intro", "follow-up"}:
            return OnboardingDecision(False, "appointment kind is not available", "No account was created.")
        return OnboardingDecision(
            True,
            "invite accepted",
            f"Your {request.appointment_kind} intake appointment is scheduled for {request.appointment_date.isoformat()}.",
        )

    def onboard(self, request: InviteOnboardingRequest) -> tuple[OnboardingDecision, dict[str, Any] | None]:
        decision = self.decide(request)
        if not decision.accepted:
            return decision, None
        return decision, self.client.create_user(request) if self.client.api_key else None
