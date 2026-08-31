# WFM Metrics Glossary

This document defines the core metrics used across all Workforce Management (WFM) reporting, dashboards, and the Intraday_raw dataset. All time-based values are measured in seconds unless stated otherwise.

## Call Volume Metrics

**Offered** — The total number of calls that entered the queue for a given language, LOB (Line of Business), and interval, regardless of outcome. This is the baseline volume metric used for all forecasting and capacity calculations.

**Handled** — The number of offered calls that were successfully answered by an agent and completed. A call is only counted as handled once the interaction is fully closed (including after-call work).

**Transferred** — The number of calls that were moved from one queue, agent, or LOB to another before resolution. Transferred calls are split into two sub-metrics:
- **Transferredout** — calls that left the current queue to another destination.
- **Transferredin** — calls that arrived into the current queue from another source.

**Rerouted** — Calls automatically redirected by the system logic (e.g., overflow routing) rather than manually transferred by an agent.

**Unanswered** — Calls that reached an agent but were not picked up within the ring window and returned to the queue or were lost.

**Abandoned** — Calls where the customer disconnected before being answered by an agent. This is one of the primary indicators of service quality.

**Abandonedringing** — A subset of abandoned calls where the customer hung up specifically during the ringing phase, after being connected to an agent's line but before the agent answered.

**Voicemails** — Calls that were routed to voicemail instead of being handled live.

**Callswisl** — Calls with In-Service Level; calls that were answered within the target Service Level threshold defined for that LOB.

## Time Metrics

**Tottalktime** — Total cumulative time (in seconds) agents spent actively talking to customers, including any hold time during the call.

**Tottalk_without_hold** — Same as above, but excluding any time the call spent on hold.

**Totholdtime** — Total cumulative time customers spent on hold during handled calls.

**Callholds** — The number of individual hold events that occurred across all handled calls in the interval.

**Totwraptime** — Total after-call work time — the time agents spend on administrative tasks (notes, data entry, follow-up actions) immediately after ending a call, before becoming available again.

**Totspeedtoanswer** — Total cumulative time between a call being offered and being answered by an agent, summed across all handled calls in the interval.

**Totwaittime** — Total cumulative time calls spent waiting in queue before being answered or abandoned.

**Totprodqueuetime** — Total "productive" queue time — time spent in queue that ultimately led to a successful handle (excludes wait time for abandoned calls).

**Waittoabandon** — Cumulative wait time for calls that were ultimately abandoned, measured from entering the queue to disconnection.

**Totdelayabandon** — Total delay time attributable to abandoned calls specifically (used to separate abandonment-driven delay from overall queue delay).

**Totringtime** — Total time calls spent ringing at an agent's station before being answered, transferred, or abandoned.

**Longdelay** — Flag/counter for calls whose wait time exceeded the "long delay" threshold defined for that LOB (typically used as an early-warning indicator, distinct from full SLA breach).

**Totdelaytime** — Total cumulative delay time across all calls in the interval, regardless of final outcome.

**Callsunderten** — The number of calls answered within the first 10 seconds of queue time — used as a fast-service quality indicator.

## Distribution Buckets

The `wait_aband_X` and `wait_answer_X` columns (where X is a number of seconds: 5, 10, 15, 20, 25, 30, 35, 40, 45, 60, 90, 120) represent distribution buckets showing how many calls were abandoned or answered within that specific wait-time window. For example, `wait_answer_15` counts calls answered between the previous threshold and 15 seconds of waiting. These buckets are used to build wait-time distribution curves and to identify where in the wait curve most abandonment occurs.

**Maxwaitaband** — The single longest wait time recorded among abandoned calls in the interval.

**Maxwaitanswer** — The single longest wait time recorded among answered calls in the interval.

## Dimensions

- **Dim_Site** — The physical or virtual site handling the interval of calls (Site 1–4).
- **Dim_Language** — The language of the interaction (Language 1–6).
- **LOB** — Line of Business, representing a distinct service or product queue (LOB 1–4).
- **repdate** — The reporting date for the interval.
- **Intvl_UTC / Intvl_CET** — The specific time interval, expressed in UTC and Central European Time respectively.
