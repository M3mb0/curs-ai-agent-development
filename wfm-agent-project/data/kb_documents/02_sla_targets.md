# Service Level Agreement (SLA) Targets

This document defines the SLA targets that apply across all Lines of Business (LOB 1–4) and how they are measured against the Intraday_raw dataset.

## Primary SLA Definition

The core Service Level metric is defined as:

**Service Level (%) = Callswisl / Offered × 100**

This measures the percentage of offered calls that were answered within the target response window for each LOB.

## LOB-Specific Targets

- **LOB 1** (highest priority, typically technical/critical support): target Service Level of 90% of calls answered within 20 seconds. Abandon rate target: below 3%.
- **LOB 2** (general customer service): target Service Level of 80% of calls answered within 30 seconds. Abandon rate target: below 5%.
- **LOB 3** (billing and account inquiries): target Service Level of 75% of calls answered within 40 seconds. Abandon rate target: below 6%.
- **LOB 4** (low-priority / informational): target Service Level of 70% of calls answered within 60 seconds. Abandon rate target: below 8%.

## Abandon Rate Definition

**Abandon Rate (%) = Abandoned / Offered × 100**

An abandon rate above target for two consecutive reporting days should trigger a review of staffing levels for that LOB and language combination.

## Average Handle Time (AHT)

**AHT (seconds) = (Tottalktime + Totwraptime) / Handled**

AHT is monitored per language and LOB combination, since handling complexity varies significantly by market. A sustained AHT increase of more than 15% above the trailing 4-week average should be flagged for root cause analysis (see Escalation Procedures).

## Long Delay Threshold

A call is flagged under `longdelay` when its wait time exceeds:
- 45 seconds for LOB 1
- 60 seconds for LOB 2
- 90 seconds for LOB 3
- 120 seconds for LOB 4

Long delay counts are an early-warning signal and are reviewed separately from full SLA breaches, since they often precede abandonment spikes.

## Reporting Cadence

- Intraday SLA is reviewed every 30 minutes during operating hours.
- Daily SLA rollups are reviewed each morning for the previous day, per site, language, and LOB.
- Weekly SLA trends are reviewed every Monday, covering the prior 7-day period, and are used as the primary input for the following week's staffing plan.
