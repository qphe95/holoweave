# Holoweave

A decentralized store built against shadowbanning and narrative control: the quiet, selective suppression of one person's project, post or archive.

## Why

**Stopping quiet censorship.** Most real censorship isn't a ban. One file stops loading, one post drops out of reach, one link times out for some readers, and nobody but the author notices. It works because a host can target one item precisely while everything else keeps working. Holoweave makes that kind of targeted removal cost about as much as taking down the whole network.

**Audit trails nobody can quietly edit.** The same property makes Holoweave a base for tamper-evident audit trails. Supply chains and large organizations keep records (shipments, inspections, approvals, payments, access logs) whose value depends on nobody being able to change them later. Today those trails usually live on systems run by a small trusted group, such as IT admins, database owners or a vendor. That group can alter or delete an entry for personal gain, cover a mistake, or bow to pressure, and the people relying on the trail may never find out. In Holoweave no such group exists:

- Every record is committed by a Merkle root on a public chain when it's stored, so changing it afterwards is detectable by anyone holding its address.
- No operator, admin or small coalition can remove one chosen record. That takes about two-thirds of all stake, and even then the nodes involved can be slashed.
- Nodes can't tell which records they hold or which ones a reader is fetching, so they can't single out the one entry someone wants gone.

Records are kept for a fixed, prepaid term (default 10 years) and can be renewed by re-uploading. An organization would still publish the list of its record addresses somewhere append-only, such as Holoweave's optional discovery index, so readers know which entries to check.

## How it works

- **Files are coded together in 64 MB packs** whose pieces sit on independent random holders, so making one chosen file unreadable takes about two-thirds of all stake, the same stake that could black out most of the network.
- **Every read is PIR**, with no gateways, so a node never learns which record a reader wants. A refused reader rebuilds the piece from other holders.
- **Every answer is signed.** A node that deletes or corrupts a chosen file's record hands that file's readers wrong answers they can prove, and loses its bond; it can't avoid this by spotting their queries.
- **Files are prepaid for a fixed term** (default 10 years), and escrow is released only to nodes that pass daily storage proofs.

## How it prevents selective deletion

Say someone wants one file, X, gone (a post, a project, one entry in an audit trail) while everything else keeps working. Holoweave closes off each way of doing that:

1. **Deleting it outright takes about two-thirds of the network.** X's pieces are coded together with many other files into a 64 MB pack, and any half of the pack's 4,096 pieces rebuilds it. Each piece sits on its own randomly chosen set of 96 nodes, weighted by stake. Destroying X means destroying more than 2,048 of those stripes at once, which needs about two-thirds of all stake: the point where an attacker could black out most of the network anyway. Below about 66% of stake the chance of making X unreadable is under 10^-18.
2. **A node can't tell which queries are for X.** Every read is a PIR query, so the node computes its answer over a whole 1 GB domain without learning which record was asked for. If it wants to refuse X's readers based on their queries, it has to refuse the whole domain, about 1 GB of other people's data. Readers then just rebuild the piece from 32 other holders, and the refusing node isn't paid.
3. **Deleting X's data gets the node caught.** A node can work out which of its stored pieces belong to X once X's address is public, so it could delete just those. But every answer it gives is signed, and from then on every answer to a query for X is wrong. Because it can't tell which queries are for X, it can't avoid giving those wrong answers to X's readers. Any of them can post a short proof that the node's signed answer doesn't match what was committed on chain, and the node loses its bond. Honest nodes can't be framed, because the proof rebuilds the reader's query from a seed.

So a node's options against X are to keep serving it, refuse its whole domain (which achieves nothing, since readers go elsewhere), or be slashed the first time a reader of X files a proof. What remains: a node can refuse particular readers by address, which slows them down but doesn't stop them; an attacker willing to pay more than a node's bond can still buy a deletion, which readers route around; and a coalition with about two-thirds of stake can destroy a file outright, though slashing follows. The proofs are in [`docs/security-games.md`](docs/security-games.md) (Theorems 1 to 4).

## Status

Design and paper proofs, with simulations and PIR benchmarks. Nothing is implemented yet.

## Contents

| Path | What it is |
| --- | --- |
| [`docs/design.md`](docs/design.md) | The design: threat model, packs and placement, ingest, retrieval, signed answers, storage proofs, repair, economics, expiry, parameters, guarantees, open decisions, risks |
| [`docs/security-games.md`](docs/security-games.md) | Security games and paper proofs: G1 availability (Theorems 1, 1′), G2 record privacy and routing around refusals (Theorems 2, 3), G3 no unpunished selective deletion (Theorem 4) |
| [`docs/comparison.md`](docs/comparison.md) | Comparison with Arweave, Filecoin, Walrus, Storj, Sia, IPFS, Freenet, entanglement-based systems and PIR-DSN |
| [`sim/SIMULATION.md`](sim/SIMULATION.md) | Simulations (packs, churn, placement, traffic) and YPIR/SimplePIR benchmarks |
| [`docs/appendix/history.md`](docs/appendix/history.md) | How the design got here: what was tried, dropped and why |
| [`docs/appendix/review-log.md`](docs/appendix/review-log.md) | Record of the two adversarial reviews (F1–F13, R1–R14) |
| [`docs/appendix/build-or-integrate.md`](docs/appendix/build-or-integrate.md) | Record of the decision to build a separate network rather than a layer on Walrus |
| [`docs/appendix/research-notes.md`](docs/appendix/research-notes.md) | Background on approaches not in the design: sealing, coded PIR, doubly-efficient PIR |

The appendix files are historical records; where they disagree with `docs/design.md`, the design wins.

## Next steps

1. Benchmark YPIR with decoding error below 2^-60 and the answer-fraud-proof STARK.
2. Benchmark the storage-proof STARK prover.
3. Prototype encoding, packs, placement and repair.
4. Independent cryptographic review of the games and proofs.

Open design decisions: hidden placement (so holders can't find a file's pieces from its address), the read-payment design, and the base chain, DA layer and proof aggregation.
