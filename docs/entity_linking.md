# Entity Linking

Milestone 3 links buildings, rooms, services and sites using deterministic, explainable rules. Canonical Milestone 2
identifiers remain the trusted primary key.

Matching hierarchy:

1. exact canonical identifier;
2. exact composite key where needed;
3. normalised name with parent or context agreement;
4. conservative similarity for future manual review;
5. unmatched/manual review.

Current sample records all contain canonical identifiers, so accepted links are exact identifier matches. Rooms remain
parent-aware through building context; room names are not treated as globally unique.

Normalisation applies Unicode compatibility normalisation, lowercase comparison, leading/trailing trim, repeated-space
collapse and punctuation/hyphen/apostrophe standardisation. It does not remove meaningful numbers from room or building
identifiers.

Duplicate candidates are retained in `evidence_duplicate_candidates`; no source row is deleted or merged. Low-confidence
matches would be marked `manual_review` rather than promoted.

