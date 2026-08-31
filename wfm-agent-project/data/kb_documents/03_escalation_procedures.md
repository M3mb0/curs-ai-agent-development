# Escalation Procedures

This document describes when and how to escalate operational issues identified through intraday or daily WFM monitoring.

## Trigger Conditions

An escalation should be raised when any of the following conditions are observed:

1. **Service Level breach** — Service Level falls more than 15 percentage points below target for any LOB, sustained across two or more consecutive 30-minute intervals.
2. **Abandon rate spike** — Abandon rate exceeds double the LOB target within a single day.
3. **AHT anomaly** — Average Handle Time increases by more than 15% above the trailing 4-week average for a given language and LOB.
4. **Long delay surge** — The count of calls flagged under `longdelay` increases by more than 50% compared to the same day in the prior week.
5. **Language-specific imbalance** — A single language shows Offered volume more than 30% above forecast while overall site volume remains within 10% of forecast (indicating a routing or staffing imbalance rather than a general surge).

## Escalation Levels

**Level 1 — Team Lead Review**
Triggered by any single condition above, sustained for at least one reporting interval. The team lead reviews real-time queue status and reallocates available agents across languages or LOBs where cross-skilling permits.

**Level 2 — WFM Analyst Investigation**
Triggered if the Level 1 response does not resolve the issue within 60 minutes, or if two or more trigger conditions occur simultaneously. The WFM analyst investigates root cause using the intraday dataset, comparing the affected interval against the same interval on the prior 4 weeks (see Root Cause Analysis Guidelines).

**Level 3 — Site Management Escalation**
Triggered if the issue persists beyond a full shift, or if the root cause is identified as a structural staffing shortfall rather than a temporary spike. Site management reviews the forecast and staffing plan for the affected language/LOB and approves any schedule or shift changes.

## Response Actions by Trigger Type

- **Volume surge (Offered spike)**: Activate overflow routing to cross-skilled agents; if unavailable, extend queue announcements and consider callback offers to reduce abandonment.
- **AHT increase**: Review recent process or system changes; check whether a specific issue type (e.g., a known outage) is driving longer handling times.
- **Abandon rate spike with normal volume**: Investigate system-side issues (IVR malfunction, incorrect routing rules) before assuming a staffing cause.
- **Long delay surge concentrated in one language**: Check agent language-skill availability; this is frequently a scheduling gap rather than a true capacity shortfall.

## Documentation Requirement

Every Level 2 or Level 3 escalation must be logged with: date, affected language/LOB/site, trigger condition, root cause identified, corrective action taken, and follow-up review date. This log is used as input for the next forecasting cycle to avoid repeat incidents.
