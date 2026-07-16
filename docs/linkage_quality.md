# Linkage Quality

Milestone 3 records linkage quality as deterministic evidence, not as real-world performance.

Tracked metrics include:

- match rate;
- exact-match rate;
- warning-match rate;
- manual-review rate;
- unmatched rate;
- duplicate-candidate rate;
- expected-defect detection rate.

The current synthetic sample is identifier-rich, so buildings, services and sites link by exact identifier. One room
link carries a warning because it is tied to a documented source defect. Duplicate-room-label evidence is now consumed
by the Milestone 4 quality framework as `DQ-ROM-UNI-001` and routed to manual review.

These metrics are engineering checks over fictional data. They are not evidence that any real source system can be
linked at the same rate.
