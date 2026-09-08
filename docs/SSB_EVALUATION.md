# SSB Official Evaluation Notes (honest)

This document is written as if reviewed by an SSB / MHA technical evaluation board comparing ~500 SIH / college teams (IIT/NIT/others).

## What works in your favour
1. **Problem fit** — Uses existing CCTV, Edge AI at BOP, Central for command — matches real SSB constraints (bandwidth, remote posts).
2. **Security awareness** — HMAC+Fernet alerts, JWT RBAC, replay/rate-limit, audit hash-chain, VPN guidance — above average for student prototypes.
3. **Operational honesty** — Offline queue, low-bandwidth mode, human-in-the-loop (alerts only) — realistic, not “fully autonomous fantasy”.
4. **Scope completeness** — Detection, tracking, face, ANPR (IND/NPL/BTN), virtual fence, dashboard, field app, C2 export.
5. **Hardening trail** — Documented limits, eval protocol, privacy TTL — shows maturity.

## What will cost ranks against top IIT/NIT teams
1. **No proven field accuracy** — Without labeled day/night/fog mAP, face TPR, ANPR accuracy on *border* video, claims stay demo-grade.
2. **No independent security audit / pen-test report** — Critical for MHA systems; student code alone is not enough.
3. **Scale evidence** — Load test script exists; published results at 50–100 BOP / 16 cams each are missing.
4. **Hardware BOM & cost model** — Edge mini-PC, power, maintenance at remote BOP not costed.
5. **Integration with existing SSB C2 / radio / SOPs** — Webhook/export is a start; full SOP alignment not demonstrated.
6. **Privacy / legal packing** — TTL and redaction help; formal data protection note for face data still thin for production.
7. **Presentation of failure modes** — Fog, spoofing, adversarial patches, camera tamper — boards expect explicit mitigations.

## Ranking outlook (illustrative, not a promise)
Among 500 teams, a **well-demoed, honest, security-conscious** system like this typically lands in **top 5–15%** if:
- Live demo is stable (Edge → Central → Dashboard → Field app)
- Judges see VPN + auth + offline queue working
- Team clearly states “prototype, needs field eval”

**1st rank** usually goes to teams that also show:
- Measured accuracy on realistic data **or** strong novel technical edge (e.g. custom low-power model, radio integration, proven pilot with a force unit)
- Crisp cost/deployment plan signed off by a domain mentor
- Zero critical security holes in live review

Without field metrics + audit, **1st rank is unlikely** against the strongest IIT/NIT entries; **finalist / top-10 contention is realistic** if demo and documentation are excellent.

## Minimum package for board confidence
- [ ] Labeled eval report (even small) for day + night
- [ ] One-page security design + threat model
- [ ] Load-test numbers attached
- [ ] Cost per BOP estimate
- [ ] Clear “human decision remains with jawan/officer” statement
