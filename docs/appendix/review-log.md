# Review log

Oct 18, 2026

An independent adversarial review of the design found two critical and four high-severity problems. The biggest: refusing to serve costs a node nothing, so the anti-censorship guarantee does not yet hold. All have concrete fixes, several of which simplify the design.

**Status (Oct 18, 2026):** F1 to F6 and F8 to F11 are folded into the consolidated design (costly challenges, DA-carrying forced inclusion, per-stripe random placement with immediate repair and reshuffles, fixed-shape reads, well-formed-query fraud proofs, commit-reveal audits, shielded fees, capacity pricing, hash-only commitments). F7 (sealing margin) is moot: sealing was dropped for v1. The claims corrected below no longer appear in the design.

## Findings

| # | Severity | Problem | Attack | Fix |
| --- | --- | --- | --- | --- |
| F1 | Critical | Non-answers are never punished | A node silently drops off-chain queries to X's buckets and answers only the rare on-chain challenges. Answering on-chain costs it nothing, and the challenger loses its bond. Payouts are gated on a KZG proof the node can make from w peers' symbols without storing anything. | Every on-chain-answered challenge costs the node a fixed penalty plus that epoch's escrow, and the challenger's bond is burned rather than paid to the node. Post challenges to a DA blob layer, one escalation per file read. Gate payouts on public audits (F6) and drop the KZG payout proof. |
| F2 | Critical | Forced inclusion keyed on a hash | An uploader posts `H(c)`, never delivers `c`, and collects builders' slashing. Or one builder lists withheld data, so the whole union batch fails sampling. | The forced path carries the data: excluded uploaders post `c` to a DA blob. Sample each builder's list separately and finalize the lists that pass. |
| F3 | High | One file can be destroyed selectively, and the threshold shrinks | X's 96 holders are public and fixed for 10 years. 65 bribed holders delete only X's m records (rarely audited); one dead stripe kills X. After churn, with 31 symbols missing under lazy repair, 34 colluders suffice. | Client-side outer erasure code (m to 2m pieces). Place a file's stripes on independent holder sets. Re-randomize holders yearly. Repair eagerly (see P2 below). |
| F4 | High | Timing fingerprints | A read hits X's specific tuple of (node, bucket) pairs within seconds. Colluders sharing logs drop only matching bursts; audits (2 per bucket per week) almost never fall in them. | F1's costly escalation is the real defense. Readers spread queries over hours on separate circuits; auditors send synthetic file-shaped bursts. |
| F5 | High | Framing an honest node | A reader sends a malformed query (not a unit vector), gets a correct answer that matches no commitment, reveals its secret and wins a fraud proof. A node can also self-report through a Sybil to collect the bounty. | Node signs (H(query), answer). Fraud proofs reveal secret and error term, and the chain checks the query is well-formed. Worst-case-correct PIR parameters. Bounty well below the slash. |
| F6 | High | Audits have no funded equilibrium | Paid-per-audit: a node's own Sybil auditors collect. Bounty-only: an honest network pays nothing, so audits starve. An auditor colluding with a node tells it which queries are audits. | Commit-reveal audits assigned by the beacon to auditors outside the holder set; reveal after the epoch so anyone can verify the audit and its result; pay per verified reveal. This also gates payouts. |
| F7 | Medium | Sealing has no margin | k = 13 is exactly break-even against 30x hardware, a modular-square-root ASIC plausibly beats 30x, and F1 lets an attacker re-seal only when challenged. | Choose k against a measured ASIC estimate with 3x to 5x margin, or move to hardness-based sealing (P5). |
| F8 | Medium | On-chain links deanonymize uploaders | The fee account and refund payee for `H(c)` link a published address back to an account and time. | Pay via a shielded pool or relayer; refund to a blinded token. |
| F9 | Medium | Overload hides censorship | One cheap query per cold bucket forces about 230 MB/s of disk per node; dropping under load looks like censorship. PIR compute is per query, not shared. | Price queries at marginal scan cost; publish per-node capacity and only slash refusals within it. |
| F10 | Medium | 10-year commitment risks | A quantum adversary breaks KZG within the term (framing, forged answers). 32-byte chunks overflow the BLS scalar field about 55% of the time. Sloth needs p ≡ 3 (mod 4); the BLS field is ≡ 1 (mod 4). | Hash-based commitments (P1). Pack 31 bytes per element. Name both fields and the mapping. |
| F11 | Low | Smaller issues | Paying for beacon-derived filler; builders withholding a holder's symbol to get it slashed; a single-party VRF beacon can be biased; exit vs. lazy repair conflict. | Don't pay for filler; holders fetch from DA with a grace period; threshold beacon or VDF; direct handoff on exit. |

## Primitives that simplify, speed up or harden the system

None needs new cryptography except P5. Most adapt known constructions to Holoweave's static, erasure-coded data, and each fixes at least one finding.

| # | Primitive | What it changes | Fixes | Recommendation |
| --- | --- | --- | --- | --- |
| P1 | Hash-only commitments: a Merkle root over symbols plus a FRI-based proof that each batch is a valid Reed-Solomon codeword (FRIDA-style) | Removes KZG, its trusted setup and the homomorphic symbol-commitment derivation. Readers check a hash path instead of a 1,024-point MSM. Safe against quantum computers. | F10, part of F5 | **Adopt** |
| P2 | Minimum-storage regenerating code (Clay code) with a random invertible precoding so every symbol still mixes all pieces | Repairs one lost symbol at about 1.5x its size (95 helpers send 1/64 each), so repair can be eager. No degraded window where 34 colluders suffice. Sub-packetization is 4,096, i.e. 8-byte sub-chunks of a 32 KB symbol. | F3, F11 (exit) | **Adopt**, after benchmarking disk reads at helpers |
| P3 | Commit-reveal PIR audits assigned by the beacon | One mechanism for detection, liveness and payout gating; results become public evidence. The KZG payout proof and separate audit types go away. | F1, F6 | **Adopt** |
| P4 | PIR with server preprocessing for static data, and its verifiable variant ([ReinsPIRe, ePrint 2026/1934](https://eprint.iacr.org/2026/1934)) | Buckets never change, so preprocessing is paid once. Claims about 2x scan throughput (5.9 GB/s per core) and an in-storage mode suited to disk-backed buckets. Verifiable answers could replace reveal-the-secret fraud proofs. | F5, F9 | **Benchmark** against YPIR |
| P5 | Hardness-based sealing: incompressible encodings (Moran–Wichs 2020) or trapdoor-permutation replica encodings (Damgård–Ganesh–Orlandi 2019) | Security of sealing would rest on a hardness assumption instead of a hardware cost ratio. Obstacle: the storing node must never hold the trapdoor, so encoding needs a threshold encoder committee. | F7 | **Research track** |
| P6 | A data-availability blob layer for forced inclusion and challenges (not a primitive) | Forced inclusion carries the data; challenges and answers stop going through calldata. Replaces hash-keyed inclusion and much of the multi-builder machinery. | F1, F2 | **Adopt** if DA throughput fits the upload volume |

## Decisions needed and claims to correct

**Decisions**

- [ ] **Keep entanglement, or switch to a systematic code?** The reviewer points out that bystander damage is a cost to strangers, not to the censor, so it doesn't deter. A systematic code plus a client-side outer code and independent holder sets would cut reads from about 36x to about 1x. Entanglement was an original goal, so this is a design choice, not a bug fix.
- [ ] **Fraud proofs:** reveal-the-secret with on-chain well-formedness checks, or verifiable PIR (P4)?
- [ ] **Sealing scope:** keep it with an ASIC-based margin, or treat capture of more than about 1/3 of a batch as out of scope and drop it?
- [ ] **Holder re-randomization period** (yearly suggested), and the repair trigger if P2 is not adopted (8 to 12 missing suggested).

**Claims in the design to correct**

- Guarantee 4: one node corrupting X damages nothing (the code absorbs it). About *m*(*w* − 1) pieces are damaged only when 65 or more holders collude.
- "Caught the first time the file is read privately": a read queries a given holder with probability 36/96 per stripe, so not guaranteed.
- "Refusing a bucket is slashed" and "always visible": unsupported until F1 is fixed.
- "Fewer than 65 colluders cannot make a stripe unavailable": only while all 96 holders are present.
- Read cost: at least 36x the file size (*w* + 4 holders) times PIR response expansion, plus the upload of about 1,152 PIR queries per MB read.
- "0.1 core-seconds per scan, shared across the batch": PIR compute is per query; only the memory pass is shared.
- Lazy repair is about 2x bandwidth per rebuilt symbol, not 1x.
- k = 13 is break-even against 30x hardware, not a safety margin.
- The idea 2 barrier should not lean on the Freij-Hollanti et al. capacity conjecture, which Sun and Jafar showed is not tight in general. The conclusion still holds in this regime: a coalition of at least *w* holders knows the whole batch.

**Checked and correct:** 6.1 × 10^8 symbols per 20 TB node, 20,000 buckets, 5,714 audits a day (94% chance of catching 0.05%), 33 MB/s weekly scans, the sealing figures, and the binomial tails for 20% and 33% stake.
