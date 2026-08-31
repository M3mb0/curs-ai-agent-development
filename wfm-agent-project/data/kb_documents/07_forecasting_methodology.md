# Forecasting Methodology

This document describes the standard approach for building intraday and daily call volume forecasts.

## Forecast Types

**Daily forecast** — total expected Offered volume per language and LOB for a full day, derived from historical trends and seasonal adjustments.

**Intraday forecast** — the daily forecast distributed across the day's intervals (15 or 30 minutes), following a historical arrival pattern specific to that language, LOB, and day of week.

## Building an Intraday Pattern

An intraday arrival pattern is built by:
1. Selecting a historical baseline period — typically the same day of week over the trailing 4–8 weeks, excluding known outlier days (holidays, outages, marketing campaigns).
2. Calculating, for each interval, the percentage of that day's total volume that historically arrives in that interval.
3. Averaging these percentages across the baseline period to produce a smoothed intraday distribution curve that sums to 100% across all intervals in a day.

## Applying the Pattern to a New Volume Target

Once the intraday distribution pattern is established, it can be applied to any total daily volume target:

**Forecasted interval volume = Total daily forecast × Interval's historical percentage share**

This method allows forecasting a specific day's shape even when the total volume target differs significantly from historical daily totals — for example, applying a known Monday arrival pattern to a new, larger target volume for capacity planning purposes.

## Day-of-Week Sensitivity

Arrival patterns differ meaningfully by day of week, particularly between Mondays (typically the highest-volume day due to weekend backlog) and mid-week days. Forecasts should never apply a generic "average day" pattern; the pattern must always be built from the same day-of-week as the day being forecasted.

## Language-Specific Patterns

Each language's arrival pattern is calculated independently, since customer behavior (e.g., typical call times) can vary meaningfully across languages and the regions they represent. Pooling all languages into a single arrival pattern before distributing volume is a common forecasting error and should be avoided.

## Forecast Accuracy Review

Forecast accuracy is reviewed weekly by comparing forecasted vs. actual Offered volume at the interval level, using Mean Absolute Percentage Error (MAPE) as the primary accuracy metric. A MAPE above 15% at the daily level, or above 25% at the interval level, should trigger a review of the baseline period and pattern assumptions used for that language/LOB.
