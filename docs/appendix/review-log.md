# Review log

> **Historical record.** This file records past work and is not the current design; where it disagrees with [../design.md](../design.md), the design wins. A summary of what changed and why is in [history.md](history.md).

Oct 18, 2026

An independent adversarial review of the design found two critical and four high-severity problems. The biggest: refusing to serve costs a node nothing, so the anti-censorship guarantee does not yet hold. All have concrete fixes, several of which simplify the design.

**Status (Oct 18, 2026):** F1 to F6 and F8 to F11 are folded into the consolidated design (costly challenges, DA-carrying forced inclusion, per-stripe random placement with immediate repair and reshuffles, fixed-shape reads, well-formed-query fraud proofs, commit-reveal audits, shielded fees, capacity pricing, hash-only commitments). F7 (sealing margin) is moot: sealing was dropped for v1. The claims corrected below no longer appear in the design. **F12 (Critical, found Oct 19, 2026 by churn simulation): the repair ratchet.** Giving each freed slot a fresh random holder let a coalition that never leaves grow its slot share to α(λ + r)/(λα + r), about 62% for a 40% coalition with honest exits at 0.5 per year and yearly reshuffles of a third. Fixed by stake-weighted rendezvous-hashing placement, which keeps slot share equal to stake share at all times (Security games, G1 under churn). F13 (High, found Oct 19, 2026 by the G2 traffic model): A\_unlink does not hold for multi-record reads. Placement is public, so reading a file, profile or thread sends a timing burst to a known set of domains; at a 50% coalition a 1 MB file read within a minute can be picked out with advantage about 0.6, and dummy queries don't help. Two linked queries are enough to identify a file. Resolved by restating G2 without unlinkability: record privacy (G2a, from PIR, in any context) plus loudness (G2b): a 2-second service deadline, after which every refusal is escalated publicly and served from other holders. The anonymity layer was then dropped to keep the system simple; nodes see who reads. Later the same day challenges were dropped too, which reverses F1's fix: refusals are no longer punished or logged, because readers route around them (a spare piece for files, 32 other holders for single posts) and nodes are paid only per verified answer. Wrong answers are handled the same way, so F5's answer fraud proofs are no longer needed; bad-encoding fraud proofs stay. F6's commit-reveal auditors were then replaced by daily storage proofs the node posts itself: one hash-based STARK over 50,000 beacon-sampled 1 KB leaves. Sizing it exposed a gap that also affected the old audits: a node storing nothing can rebuild a sampled chunk from 32 other holders for about $0.00004, so the sample count must make faking costlier than storing (50,000 a day is about 4x for a 20 TB node).

## Second review (Oct 19): R1 to R14

A second independent adversarial review read the Oct 19 snapshot after challenges, the anonymity layer and auditors were dropped. It found the availability arithmetic sound and fourteen problems, mostly claims that had lost the mechanism behind them. The biggest change it led to is **64 MB packs**: the outer code now runs over 64 MB packs (2,048 data pieces plus 2,048 parity) instead of each file, which raises the stake needed to kill one chosen file from about 57% to about 66% and means doing so destroys more than 2,048 stripes. Packs do not stop a holder from deleting the symbols it knows belong to a file; they make that useless below the threshold.

| Finding | Severity | What it said | Resolution |
| --- | --- | --- | --- |
| R1 | Critical | Once an address is public, a holder knows its symbols for that file and can delete or corrupt just those; "smallest refusable unit is a domain" was false | Accepted and restated. Packs raise the kill threshold to about 66% and more than 2,048 dead stripes; below it, a deleted or corrupted piece is rebuilt from 32 stripe holders. The fallback leaks the reader's interest to coalition holders (documented). Later the same day, signed answers and answer fraud proofs were reinstated (F5's fix, without challenges): every wrong answer to a well-formed query is provable and slashed, and since PIR hides which queries are for the file, a node can't delete one file's record without exposing itself to its readers (Security games, Theorem 4) |
| R2 | Critical | Nothing paid nodes to serve, so honest holders might not | Reads paid per verified answer with a margin; 10-minute proof deadline keeps data online; serving stated as incentive-only, with non-serving nodes counted in β |
| R3 | High | Refusing is free but multiplies load; per-reader suppression | Documented: load (1−α)+32α, 4.1× / 10.3× / 16.5× at 10% / 30% / 50%; slower and costlier for some readers, never unavailable below the threshold |
| R4 | High | 50,000 samples per node is too few for big nodes, cheap read paths and coalitions | Samples scale with bytes (2,500 per TB per day) and are due within 10 minutes; faking would need about 1.6M PIR queries. Coalition dedup savings (5% / 17% / 33% at 33% / 40% / 50%) accepted |
| R5 | High | Moving stake after seeing identity hashes beats placement (40% stake kills a file) | Stake fixed per identity; rank key uses a beacon value revealed after the identity's stake locks |
| R6 | High | Nodes chose domain layout; readers needed the Merkle path in the clear | Layout fixed by a public rule; each PIR record carries its symbol and Merkle path |
| R7 | High | Clay repair needed all 95 helpers | Clay with d = 80 helpers (about 1.63× repair); worst case 32× budgeted |
| R8 | Medium-High | Ejection gameable through chain censorship or DDoS | Proofs via forced-inclusion DA; timestamped late proofs count; 3-day grace; a node back within grace keeps its identity and pays a fine |
| R9 | Medium | DDoS on known holders acts as adaptive corruption | Open: listed as not covered by G1 and added as a security-games obligation (DoS model) |
| R10 | Medium | "Loud" and "non-selective" claims contradicted G2 | Wording rewritten; "loud" dropped; nodes see who reads |
| R11 | Medium | Chain, DA, proof verification and payments unspecified | Open decisions: base chain and DA, proof aggregation, read-payment design |
| R12 | Medium | GPU and upload figures disagreed with benchmarks | Corrected: about 20 ms per query over 64 GB, about 50 per second unbatched; GPU is a larger-domain tier, not a speed tier |
| R13 | Low | Beacon needs pairings, contradicting "no pairings" | Assumptions now name the beacon as the only pairing-based component (or a VDF) |
| R14 | Low | Stale text, overclaims, unreproducible coercion numbers | Stale text and phone references removed; availability stated per file with a union bound; coercion counts labelled heuristic upper bounds (script not shipped) |

**Verifiable PIR considered, answer fraud proofs chosen (Oct 19, 2026).** To restore "a node can't selectively delete", verifiable PIR on every read was considered first (VeriSimplePIR, USENIX Security 2024; Rathee, Lee and Popa, ePrint 2025/1714). Both bind every answer to one committed database, but they need a per-domain client setup that streams the server's hint, about 100 MB and minutes for a 1 GB domain. Holoweave readers touch a new domain for almost every post, so this would cost about 250x a read and undo the reason for choosing hint-free YPIR. Signed answers with answer fraud proofs give the same property where it matters: a wrong answer is provable, and PIR stops the node from aiming wrong answers only at one file's readers. Normal reads cost the same as before, apart from a signature.

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

- [ ] **Keep entanglement, or switch to a systematic code?** The reviewer points out that bystander damage is a cost to strangers, not to the censor, so it doesn't deter. A systematic code plus a client-side outer code and independent holder sets would cut reads from about 36x to about 1x. Entanglement was an original goal, so this is a design choice, not a bug fix. Resolved Oct 19, 2026: mixing dropped, systematic code kept; mandatory PIR on every read now provides the non-selectivity entanglement was meant to give.
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
