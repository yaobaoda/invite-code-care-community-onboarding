from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.invite_onboarding import InviteOnboardingRequest, InviteOnboardingService


def test_active_invite_accepts_and_uses_patient_safe_notification() -> None:
    service = InviteOnboardingService({"CARE-2026": date(2026, 12, 31)})
    request = InviteOnboardingRequest("maya@example.org", "Maya", "CARE-2026", "intro")

    decision = service.decide(request)

    assert decision.accepted is True
    assert decision.notification == "Your intro intake appointment is scheduled for 2026-11-10."


def test_expired_invite_rejects_before_account_creation() -> None:
    service = InviteOnboardingService({"CARE-2026": date(2026, 10, 1)})
    request = InviteOnboardingRequest("maya@example.org", "Maya", "CARE-2026", "intro")

    decision = service.decide(request)

    assert decision.accepted is False
    assert decision.reason == "invite code is not active"
