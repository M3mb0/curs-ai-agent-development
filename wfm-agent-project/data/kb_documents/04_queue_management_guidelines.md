# Queue Management Guidelines

This document describes how call queues are prioritized and managed across languages and Lines of Business (LOB).

## Queue Priority Order

When agents are cross-skilled across multiple LOBs, queues are served in the following default priority order:

1. LOB 1 (highest priority — technical/critical support)
2. LOB 2 (general customer service)
3. LOB 3 (billing and account inquiries)
4. LOB 4 (low priority / informational)

This priority order can be temporarily overridden during an active escalation (see Escalation Procedures) if a lower-priority LOB is experiencing a critical abandon rate spike.

## Cross-Skilling Rules

Agents may be assigned to more than one language or LOB, subject to the following rules:

- An agent's primary language and LOB combination must be at least 70% of their scheduled time.
- Cross-skilled overflow assignments are only activated automatically when the primary queue's Service Level is within target and the secondary queue is breaching target.
- Language cross-skilling is only permitted between languages explicitly marked as a supported pair in the agent's skill profile; agents are never auto-routed to a language they are not certified in.

## Overflow Routing Logic

Overflow routing activates when:
- Offered volume in a queue exceeds forecasted volume by more than 20% for two consecutive 15-minute intervals, AND
- At least one cross-skilled agent is available in an adjacent queue with Service Level currently at or above target.

Overflow routing deactivates automatically once the originating queue's wait time returns below the `longdelay` threshold for that LOB, to avoid starving the secondary queue.

## Callback Offers

For LOB 2, 3, and 4, a callback option is offered to customers automatically once queue wait time exceeds 3 minutes, provided callback capacity is available in the next scheduled interval. LOB 1 does not offer callbacks due to its critical/technical nature; live queue holding is prioritized instead.

## Interval-Level Monitoring

Queue health is assessed at the interval level (15 or 30 minutes, depending on site configuration) using three primary signals together, not in isolation:
- Current wait time trend (rising vs. falling)
- Abandon count in the current interval vs. the same interval on the prior day
- Available staffed agents vs. forecasted required agents (see Capacity Planning Overview)

A queue is only considered "at risk" when at least two of these three signals are simultaneously unfavorable, to avoid reacting to normal short-term fluctuation.
