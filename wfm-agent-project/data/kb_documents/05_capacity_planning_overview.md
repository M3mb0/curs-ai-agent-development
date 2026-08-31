# Capacity Planning Overview

This document explains the methodology used to calculate required staffing (capacity) for each language, LOB, and interval, based on forecasted call volume.

## Core Inputs

Capacity calculation for a given interval requires four inputs:
1. **Forecasted Offered volume** for that interval (calls expected to arrive).
2. **Forecasted Average Handle Time (AHT)** — expected Tottalktime + Totwraptime per call, based on trailing historical averages for that language/LOB.
3. **Target Service Level** for the relevant LOB (see SLA Targets).
4. **Shrinkage factor** — the percentage of scheduled agent time that is not available for handling calls, due to breaks, training, meetings, and other planned or unplanned absences (see Shift and Break Rules).

## Required Agents Formula (Simplified)

The base staffing requirement before shrinkage is calculated using queuing theory (typically an Erlang C model), which estimates the minimum number of agents needed to achieve the target Service Level given the forecasted volume and AHT.

Once the base requirement is calculated, it is adjusted for shrinkage:

**Scheduled Agents Required = Base Required Agents / (1 − Shrinkage Factor)**

For example, if the base calculation indicates 10 agents are needed to hit target Service Level, and the shrinkage factor is 30%, the schedule must provision approximately 14.3 agents to guarantee 10 are actually available and handling calls at any given moment.

## Interval Granularity

Capacity is calculated at the same interval granularity as the intraday data (15 or 30 minutes), not as a daily average. Daily averages hide peak-hour understaffing, since a language/LOB combination may be adequately staffed on average across a day while being significantly understaffed during peak intervals.

## Multi-Language Pooling Considerations

For sites where agents are cross-skilled across multiple languages (see Queue Management Guidelines), capacity planning should account for pooling efficiency — cross-skilled pools generally require fewer total agents than the sum of single-skill requirements, because idle time in one language can absorb overflow from another. However, pooling benefits should only be assumed for language pairs with an established cross-skilling agreement; unverified pooling assumptions are a common cause of under-forecasting.

## Timezone Considerations

When calculating capacity across sites operating in different timezones, all interval-level calculations must first be normalized to a single reference timezone (typically UTC) before aggregation, to avoid misaligning peak hours across sites. Only after capacity totals are calculated should results be converted back to local site time for schedule publishing.

## Review Cadence

Capacity plans are recalculated weekly using the latest 4-week trailing volume and AHT trends, with a full forecast refresh monthly incorporating seasonal adjustments (e.g., known volume shifts around holidays or product launches).
