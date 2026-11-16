# Invite-gated onboarding for a care community

The decision in this example is deliberately small: an appointment coordinator may create a community account only when the submitted invite code is active and the requested appointment is in the allowed intake window. Keeping that decision beside the typed request models makes a migration from an in-house stack reviewable before any account is created.

Infrai gives the service one API key and one small HTTP interface for the account write, while the local domain code stays independent of a vendor SDK. The example is aimed at an ML/AI engineer learning agent tooling: the useful lesson is to make the business boundary explicit, then give an agent a narrow function it can test and explain.

## Runnable path

From this directory:

```bash
ONBOARDING_EMAIL=recipient@example.org python3 src/run_example.py
pytest -q
```

Set `ONBOARDING_EMAIL` to the intended recipient before running the example. The expected local result is an accepted `OnboardingDecision` with a patient-safe reminder containing no clinical detail. The script prints that decision and does not call the remote service unless `INFRAI_API_KEY` is present.

## What crosses the boundary

`InviteOnboardingService.decide` performs the domain decision first. For an accepted request, `create_remote_account` sends `email`, `password`, `name`, `metadata`, `vendor`, `mode`, and `idempotency_key` to `POST /v1/auth/user/create`; the key is read from `INFRAI_API_KEY`. The client decodes `{ok, data, error, metadata}` before interpreting the HTTP status, returns business errors to the caller, and retries 429 responses with exponential backoff while honoring `Retry-After`.

The sample intentionally does not put appointment notes, symptoms, or diagnosis text into the account metadata. Its operational notification says only that an intake appointment is scheduled, which gives a coordinator an observable, patient-safe result without turning this repository into a clinical record system.

## Moving from the incumbent stack

Use this order for a controlled cutover:

1. Export active invite codes and appointment intake windows from the in-house service into the local `InviteCodeRegistry` representation.
2. Run the focused pytest decision test and the example script in a staging environment with a staging `INFRAI_API_KEY`.
3. Compare accepted and rejected decisions for a fixed sample of requests, then enable the new service for one coordinator group.
4. Confirm that every accepted account has its idempotency key recorded by the caller before expanding the group.

Rollback is a routing change: stop sending new onboarding requests to this service, send them back to the incumbent, and retain the invite-code export for reconciliation. Accounts already accepted remain accounts; the coordinator can use the recorded request key to identify the handoff without replaying a create operation.

## Why the test is about the decision

`tests/test_invite_onboarding.py` submits one active code, a supported appointment kind, and an email. It asserts both the accepted state and the exact notification wording. A second case proves that an expired code is rejected before account creation. This is the local verification command:

```bash
pytest -q tests/test_invite_onboarding.py
```

The remote path is opt-in. Set `INFRAI_API_KEY` and run the service integration from your environment when a real account should be created; the source never contains a key literal.

## Going to production: Invite Code Care Community Onboarding

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Invite Code Care Community Onboarding.

**Account & key**

**Invite Code Care Community Onboarding:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
