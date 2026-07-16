# Evidence Regeneration

Regenerate synthetic evidence with:

```bash
make assurance-full assurance-report release-evidence verify-release-evidence
```

Regenerate the portfolio manifest with:

```bash
make portfolio-check
```

The manifest validates handover and portfolio assets. It does not modify analytical outputs or governance conclusions.

After regeneration, confirm:

```bash
make dashboard-check portfolio-check handover-check final-audit
```
