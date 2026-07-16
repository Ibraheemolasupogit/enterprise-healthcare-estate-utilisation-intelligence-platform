# CI/CD Strategy

The CI design uses least-privilege read-only permissions and local deterministic commands. Pull-request checks run repository, Python, configuration, SQL, documentation, dashboard and security checks.

Main and manual assurance paths can run the full Milestones 1-12 evidence chain followed by Milestone 13 assurance evidence generation.

Pip caching is allowed using dependency-file keys. Generated SQLite databases and evidence outputs are never trusted cache inputs.

Workflow concurrency cancels stale branch runs. No workflow deploys, publishes releases or requests write permissions.
