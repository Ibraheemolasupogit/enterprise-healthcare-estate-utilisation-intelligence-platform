# Effective Utilisation

Effective clinical utilisation is a bounded weighted score. The weights are configured in `config/utilisation.yaml` and
must sum to one.

Components:

- actual occupied utilisation;
- attendance utilisation;
- completed contacts per available room hour factor;
- workforce availability factor;
- cancellation penalty factor;
- no-show penalty factor.

Missing components are treated as zero rather than imputed. Scores are bounded from 0 to 1. Protected specialist
capacity is reported separately and is never classified as releasable solely because utilisation is low.

