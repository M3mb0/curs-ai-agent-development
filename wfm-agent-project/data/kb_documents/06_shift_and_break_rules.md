# Shift and Break Rules

This document describes the standard break structure and shrinkage assumptions used in scheduling and capacity planning.

## Standard Shift Structure

A standard full-time shift is 8 hours (480 minutes) of scheduled time, structured as follows:
- 2 short breaks of 15 minutes each (typically placed roughly 2 hours after shift start and 2 hours before shift end).
- 1 meal break of 30 minutes, placed near the midpoint of the shift.
- 30 minutes of non-call activity reserved for training, coaching, or team meetings, scheduled outside of peak intervals whenever possible.

This results in approximately 400 minutes of the 480-minute shift being available for call handling, before accounting for unplanned shrinkage.

## Break Placement Rules

- No more than 20% of any team's headcount for a given language/LOB may be on a scheduled break simultaneously.
- Breaks may not be scheduled during a forecasted peak interval (defined as any interval where forecasted Offered volume is within 90% of the daily maximum) unless staffing levels for that interval exceed the required capacity by at least 10%.
- Meal breaks must be scheduled between hour 3 and hour 6 of the shift, to keep coverage balanced across the full shift.

## Shrinkage Categories

Shrinkage is tracked in two categories:

**Planned shrinkage** — known in advance and built directly into the schedule: breaks, meal periods, scheduled training, team meetings, and scheduled coaching sessions. Planned shrinkage typically totals 15–20% of scheduled time.

**Unplanned shrinkage** — not known in advance and tracked separately for trend analysis: sick leave, late arrivals, system outages, and unscheduled absences. Unplanned shrinkage is monitored weekly per site and language; a sustained increase above the trailing 8-week average should be flagged to site management, as it directly reduces effective capacity against the forecast.

## Adherence Monitoring

Schedule adherence — the degree to which agents follow their assigned schedule (including break timing) — is monitored at the interval level. Adherence below 85% for a given language/LOB team over a rolling 5-day period should trigger a review, since poor adherence directly undermines the accuracy of capacity planning even when the underlying forecast and staffing plan are correct.

## Cross-Reference

Break scheduling data is maintained in the "Planning breaks" tab and must be cross-checked against forecasted peak intervals in the Capacity Calculation tab before being finalized, to avoid inadvertently scheduling breaks during a forecasted peak.
