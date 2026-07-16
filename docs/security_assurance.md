# Security Assurance

Milestone 13 implements a deterministic local pattern scan for obvious credentials and unsafe workflow controls. It checks private-key headers, common token formats, bearer tokens and generic password assignments.

`.env.example` is allowed to contain documented placeholders. The scan is not equivalent to enterprise secret-scanning products.

Workflow checks require read-only permissions, no deployment commands, no package publishing, no public dashboard launch and no write-token usage.
