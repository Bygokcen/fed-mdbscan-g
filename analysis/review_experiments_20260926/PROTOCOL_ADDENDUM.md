# Plan addendum: acceptance-count-matched FLAME random control (27 September 2026)

This addendum fixes a design gap in the E3 FLAME control in the main plan (PROTOCOL.md, SHA-256 `cf7dca80…`). It was written before the runs. Its SHA-256 digest and timestamp are recorded in `protocol_addendum_registration.json`.

## Why

In the E3 FLAME random control, the subset size is whatever number FLAME selected that round along the control's own training trajectory. Because trajectories diverge, the acceptance counts differ from the canonical FLAME run. The mean gap is 0.07 updates on MNIST, 0.96 on Fashion-MNIST, and 1.37 on HAR. So the E3 acceptance counts are not a matched two-arm comparison. The Multi-Krum control does not have this problem, since the count is fixed at 61 in both arms.

## Design (E3m)

- **Conditions:** clean, α=0.01 (scenario 6.2); MNIST, Fashion-MNIST, HAR; seeds 42, 137, 2024. 9 runs total.
- **Intervention:** in each round r, the frozen FLAME selector runs as usual; the clipping norm and noise scale come from it. The selected indices are replaced with a uniformly random subset sized to **the canonical FLAME run's recorded acceptance count for that same round**. Clipping and noise are unchanged.
- **Randomness:** comes from the stream `derive_seed(seed, 'review_matched_random_selection', r)`. The training, attacker, and participation streams are not consumed.
- **Environment:** same as E3. The canonical frozen source, the canonical launch environment, and a script that wraps the frozen function at run time are used. The simulation code is unchanged.

## Validation

- The acceptance count in every round must equal the count in the canonical record.
- Since all participants are honest, the rejection counts are the same from round to round. So the run's BER must come out identical to canonical FLAME.
- The data partition, participation schedule, and initial model must match the canonical run.

A run that fails validation is counted as failed; it is not re-seeded.

## Measurements and reporting

Final accuracy is measured for each seed. The reported gaps are FLAME minus matched random and FedAvg minus matched random, with their mean, minimum, and maximum. The result is written to the supplement regardless of which direction it goes. The manuscript treats the matched control as the basis for FLAME; the unmatched control from E3 remains in the supplement, explicitly labeled as such.
