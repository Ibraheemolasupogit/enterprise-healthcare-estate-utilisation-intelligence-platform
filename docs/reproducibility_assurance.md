# Reproducibility Assurance

Assurance run identity is deterministic and excludes timestamps, local paths, process IDs and runtime durations. It is based on framework version, profile, upstream run IDs, assurance config checksum, check catalogue checksum, repository contract checksum, documentation contract checksum and security rule checksum.

Release evidence uses SHA-256 checksums. The release manifest does not checksum itself.

Two independent assurance executions can compare exported files, run IDs, gate outcomes and manifest content byte-for-byte.
