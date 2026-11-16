import os
from datetime import date

from invite_onboarding import InviteOnboardingRequest, InviteOnboardingService


def main() -> None:
    service = InviteOnboardingService({"CARE-2026": date(2026, 12, 31)})
    email = os.environ.get("ONBOARDING_EMAIL")
    if not email:
        raise SystemExit("ONBOARDING_EMAIL is required")
    request = InviteOnboardingRequest(email, "Maya", "CARE-2026", "intro")
    decision, account = service.onboard(request)
    print(decision)
    if account is not None:
        print({"remote_account_created": True, "response_keys": sorted(account)})
    else:
        print({"remote_account_created": False, "next_step": "set INFRAI_API_KEY for the remote write"})


if __name__ == "__main__":
    main()
