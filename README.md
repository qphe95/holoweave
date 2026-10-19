# Holoweave

A decentralized store built against shadowbanning and narrative control. Files are prepaid for a fixed term (default 10 years) and erasure-coded together in 64 MB packs whose pieces sit on random holders, so making one chosen file unreadable takes about two-thirds of all stake. Every read is PIR with no gateways, so nodes never learn which record a reader wants; a refused or wrong answer earns the node nothing, and the reader rebuilds that piece from other holders.

Status: design and paper proofs. Nothing is implemented yet.

## Contents

| Path | What it is |
| --- | --- |
| [`docs/design.md`](docs/design.md) | Main design: threat model, encoding and placement, ingest, retrieval, storage proofs, repair, economics, expiry, performance, guarantees |
| [`docs/security-games.md`](docs/security-games.md) | Security games and paper proofs for G1 (availability) and G2 (record privacy and routing around refusals), plus simulation results |
| [`docs/comparison.md`](docs/comparison.md) | Comparison with Arweave, Filecoin, Walrus, Storj, Sia, IPFS, Freenet and entanglement-based systems (Tangler, Dagster, OFF, Recast) |
| [`docs/build-or-integrate.md`](docs/build-or-integrate.md) | Decision to build Holoweave's own network instead of layering on Walrus |
| [`docs/appendix/research-notes.md`](docs/appendix/research-notes.md) | Sealing (dropped for v1), coded PIR (dropped), doubly-efficient PIR (parked) |
| [`docs/appendix/review-log.md`](docs/appendix/review-log.md) | Adversarial review findings F1–F13, second review R1–R14, primitives P1–P6 |
| [`sim/`](sim/SIMULATION.md) | Placement, churn, traffic-model and pack simulations; SimplePIR and YPIR benchmarks |

The living version of these docs is the Holoweave Design Doc on claude.ai; these markdown files are a snapshot from Oct 19, 2026.

## Next steps

1. ~~Run the YPIR benchmark~~ (done Oct 19: no client hint, about 0.46 core-seconds per 32 KB record at 1 GB domains).
2. ~~Churn-aware G1~~ (done Oct 19: found and fixed the repair ratchet; Theorem 1′ in `docs/security-games.md`).
3. ~~Traffic model behind G2~~ (done Oct 19: file and profile reads are recognizable even over an anonymity layer, so G2 now rests on record privacy plus routing around refusals; no anonymity layer is required).
4. ~~Challenge model~~ (done Oct 19: challenges dropped; readers route around refusals and nodes are paid only per verified answer).
5. ~~Replace auditors~~ (done Oct 19: each node posts one daily STARK over 2,500 beacon-sampled leaves per TB, due within 10 minutes).
6. ~~Independent adversarial review~~ (done Oct 19: findings R1–R14 and how each was resolved are in the review log).
7. ~~Packs~~ (done Oct 19: the outer code runs over 64 MB packs, raising the stake needed to kill one chosen file from about 57% to about 66%; see `sim/group_code.py`).
8. Benchmark the storage-proof STARK prover.
9. Prototype encoding, packs, placement and repair.
10. Independent cryptographic review of the games and proofs.

Open design decisions: a hidden placement committee (so holders can't find a file's pieces from its address), the read-payment design, and the base chain, DA layer and proof aggregation.
