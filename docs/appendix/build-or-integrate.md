# Build or integrate

> **Historical record.** This file records past work and is not the current design; where it disagrees with [../design.md](../design.md), the design wins. A summary of what changed and why is in [history.md](history.md).

Oct 18, 2026

**Decision (Oct 18, 2026): build Holoweave's own network.** Integrating would leave too many guarantees weakened: non-selectivity only on separate mirror servers, refusals logged but never penalized, and dependence on Sui, WAL pricing and Walrus's stake concentration. Building keeps node-level PIR, enforced challenges and Holoweave's own terms. The analysis below is kept as the record of that choice. Ideas worth borrowing from Walrus: its epoch-change protocol for moving shards, and its aggregator and cache model for the fast path. Encoding each blob across all shards was considered and rejected: it gives an exact two-thirds threshold, but the shard count caps the number of operators, while per-stripe random placement scales to any network size.

**Original recommendation (not adopted): build Holoweave as a layer on Walrus.** Walrus already spreads every blob across all of its shards, so blocking any blob needs nodes holding more than two-thirds of them, which is the availability property Holoweave was going to build. What Walrus lacks (private reads, 10-year terms, blind uploads, deniability) can be added on top without changing Walrus. Build a separate network only if node-level PIR or enforced serving challenges turn out to be essential and Walrus won't adopt them.

## What Walrus already provides

| Holoweave needs | Walrus today | Fit |
| --- | --- | --- |
| A file spread so blocking it needs most of the network | Every blob is encoded into one sliver per shard across all shards (1,000 on mainnet, judging by the 334-sliver read threshold); a reader needs slivers from just over a third, so blocking needs nodes holding more than two-thirds | **Strong.** Deterministic, no outer code or per-stripe placement needed |
| Redundancy and repair | RedStuff 2D erasure coding at about 4.5x, self-healing with bandwidth proportional to lost data | **Strong**, and cheaper than Holoweave's 6x |
| Proofs that nodes store data | Storage challenges that work in asynchronous networks; availability certificates signed by two-thirds of shards | **Good** |
| Holders that change over time | Shards are reassigned per two-week epoch by a Sui contract, with an epoch-change protocol | **Good** (replaces the yearly reshuffle) |
| Fast reads and caches | Permissionless aggregators and caches rebuild blobs and serve them over HTTP; clients verify | **Strong**: this is Holoweave's fast path |
| Encoding fraud proofs | Inconsistency proofs for incorrectly encoded blobs | **Good** |
| Data that can't be deleted early | Permanent blobs, and shared blobs that anyone can fund and extend | **Good** |
| Encrypted content | Blobs are public, but they can hold ciphertext | **Fine**: Holoweave encrypts on the client anyway |

## Gaps and how a Holoweave layer fills them

| Gap | Holoweave layer on top | Needs Walrus changes? |
| --- | --- | --- |
| Nodes see which blob is requested, so they can refuse one selectively | **PIR private-read servers** mirror Walrus blobs (they are public) and answer YPIR queries over large domains. Non-selectivity (G2) holds on these servers. Later, propose a PIR sidecar for Walrus nodes through governance. | No (sidecar: yes) |
| Storage lasts at most 2 years (53 epochs) | An **endowment contract** on Sui escrows 10 years of funding and extends each shared, permanent blob before it expires. | No, if a Move contract can call the shared-blob extension (to confirm) |
| Uploads and payments link to Sui accounts | **Blind ingest:** clients encrypt and pad, upload over an anonymity layer, and pay through a relayer or sponsored transactions funded by blinded credits. | No |
| Nodes hold identifiable blobs | **Light mixing** in the client: each stored blob is XORed with randomizer blobs (other permanent blobs in the same funding cohort), so no blob belongs to one file. | No |
| Small items waste space | **Bundling** in the client, or Walrus storage pools and its small-blob batching. | No |
| Nodes aren't forced to answer serving challenges | A **refusal log** contract records signed client reports and failed retrievals per blob ID, as public evidence. It can't force Walrus nodes to answer on-chain or slash them; that would need a Walrus protocol change. | For enforcement: yes |

## Effect on the guarantees

| Guarantee | On Walrus with a Holoweave layer | Compared with building |
| --- | --- | --- |
| G1 availability | Holds: blocking a blob needs nodes holding more than two-thirds of shards. Rests on Walrus's assumption that over two-thirds of shards are honest each epoch | Similar threshold; deterministic instead of probabilistic |
| G2 non-selectivity | Holds on Holoweave's PIR servers only; Walrus nodes themselves can still refuse a known blob, but alone that can't block it below the threshold | Weaker: in the built design every node is blind on the private path |
| G3 accountability | Wrong slivers are caught by Walrus's verification; non-answers are recorded publicly but not penalized | Weaker: no forced on-chain answers or slashing for refusal |
| G4 blind ingest | Holds with a relayer and client encryption | Same |

**Risks of depending on Walrus**

- **Sui.** Blob registration, payment and certificates are Sui transactions; validators censoring those transactions would block new uploads.
- **Concentration.** Mainnet launched with over 100 storage nodes, but shard assignment follows stake. If a few operators hold over two-thirds of shards, G1 is weaker than the design assumes. This needs checking against live stake data.
- **Economics and governance.** WAL token prices, storage pricing and protocol changes are outside Holoweave's control, so a 10-year endowment carries price risk at each renewal.
- **Two-year horizon.** Every blob must be extended at least every two years; a lapse in the endowment contract means data loss.

**The build option.** Building gives node-level PIR, enforced challenges with slashing, and Holoweave's own term and economics. It costs years of protocol engineering, recruiting and incentivizing node operators, and bootstrapping enough stake to make the availability threshold meaningful. Walrus already has the operators and stake.

## Next steps

1. **Check stake concentration** on Walrus mainnet: how many operators together hold two-thirds of shards.
2. **Confirm the endowment path:** whether a Move contract can extend shared blobs, and how storage is priced at renewal.
3. **Prototype the client library** on Walrus testnet: encrypt, pad, bundle, mix with randomizer blobs, and store as permanent shared blobs.
4. **Prototype a PIR mirror server:** mirror a set of blobs and serve YPIR queries over them; measure latency next to the YPIR benchmark.
5. **Measure Walrus read latency** through aggregators and directly from nodes, to compare with the fast-path target.
6. **Talk to the Walrus Foundation** about a node-side PIR sidecar and enforceable serving challenges.

**Sources**

- [Walrus architecture and security assumptions](https://docs.wal.app/design/architecture.html)
- [Walrus assurance and security properties](https://docs.wal.app/design/properties.html)
- [Walrus RedStuff parameters](https://docs.wal.app/docs/system-overview/red-stuff-parameters)
- [Walrus glossary](https://docs.wal.app/docs/glossary)
- [Walrus: storing blobs](https://docs.wal.app/docs/walrus-client/storing-blobs)
- [Walrus: managing blobs (shared blobs)](https://docs.wal.app/docs/walrus-client/managing-blobs)
- [Walrus mainnet announcement](https://docs.wal.app/blog/06_mainnet)
- [Walrus paper](https://arxiv.org/html/2505.05370v2)
