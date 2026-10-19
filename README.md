# Holoweave

A decentralized store built against shadowbanning and narrative control. Files are prepaid for a fixed term (default 10 years) and spread so thinly and randomly that quietly removing one file needs most of the network; on the private read path, refusing one file means refusing whole PIR domains, and every refusal leaves public evidence.

Status: design and paper proofs. Nothing is implemented yet.

## Contents

| Path | What it is |
| --- | --- |
| [`docs/design.md`](docs/design.md) | Main design: threat model, encoding and placement, ingest, retrieval, audits, repair, economics, expiry, performance, guarantees |
| [`docs/security-games.md`](docs/security-games.md) | Security games and paper proofs for G1 (availability) and G2 (non-selectivity), plus simulation results |
| [`docs/comparison.md`](docs/comparison.md) | Comparison with Arweave, Filecoin, Walrus, Storj, Sia, IPFS, Freenet and entanglement-based systems (Tangler, Dagster, OFF, Recast) |
| [`docs/build-or-integrate.md`](docs/build-or-integrate.md) | Decision to build Holoweave's own network instead of layering on Walrus |
| [`docs/appendix/research-notes.md`](docs/appendix/research-notes.md) | Sealing (dropped for v1), coded PIR (dropped), doubly-efficient PIR (parked) |
| [`docs/appendix/review-log.md`](docs/appendix/review-log.md) | Adversarial review findings F1–F11 and primitives P1–P6 |
| [`sim/`](sim/SIMULATION.md) | Placement simulation, SimplePIR benchmark and YPIR run instructions |

The living version of these docs is the Holoweave Design Doc on claude.ai; these markdown files are a snapshot from Oct 18, 2026.

## Next steps

1. Run the YPIR benchmark natively (instructions in `sim/SIMULATION.md`).
2. Churn-aware G1: model repair delay and correlated outages.
3. Concrete traffic model for the unlinkability assumption A_unlink behind G2.
4. Prototype encoding, placement and repair.
5. Independent cryptographic review of the games and proofs.
