# Design history

How Holoweave reached its current design, and why each earlier idea was dropped. The current design is in [../design.md](../design.md); this file is the record. Review findings are in [review-log.md](review-log.md) (F1–F13 from the first review, R1–R14 from the second).

## Summary of decisions

| Topic | Earlier | Now | Why it changed |
| --- | --- | --- | --- |
| Network | Possibly a layer on Walrus | Holoweave's own network | A layer couldn't give node-level PIR or its own terms ([build-or-integrate.md](build-or-integrate.md)) |
| Entanglement | Each piece XORed with randomizer blocks from other files (OFF-style mixing) | None | With PIR on every read it added no protection, tripled read cost and gave each piece more blocks to lose. Entanglement alone can't stop a server dropping one document anyway (Aspnes et al.) |
| Outer code | Each file coded on its own (32 pieces for 1 MB, any half rebuild) | 64 MB packs across many files | Killing one file needed only 17 stripes and about 57.6% of stake; a pack needs 2,049 stripes and about 66.3% (R1, `sim/group_code.py`) |
| Holder draw | 96 distinct nodes per stripe | Slots drawn with replacement in proportion to stake | Distinct draws let many small identities out-slot large honest operators (`sim/placement_sim.py`) |
| Freed slots | Fresh random holder per freed slot | Stake-weighted rendezvous hashing | The repair ratchet: a coalition that never leaves would climb from 40% of stake to about 62% of slots (F12, `sim/churn_sim.py`) |
| Identity keys | Fixed by the beacon at registration | Ranking randomness revealed after stake locks; stake fixed per identity | Moving stake into well-ranked identities let 40% of stake kill a file (R5) |
| PIR scheme | SimplePIR | YPIR, no client hint | SimplePIR needs a client hint of about 100 MB per node and domain |
| PIR domains | 8 GB | 1 GB minimum, layout fixed by a public rule | Cost per read; a node choosing its own layout could isolate a target (R6) |
| Reads | A fast path and gateways alongside PIR | Every read is PIR, no gateways | A plain path lets nodes see and refuse one file |
| Anonymity layer | Required for reads | None | The traffic model showed file and profile reads are recognizable by timing even over Tor (F13, `sim/traffic_model.py`); dropped to keep the system simple |
| Refusals | On-chain challenges with penalties, public refusal logs | Readers route around refusals; nodes paid only per verified answer | Simpler, and below the threshold a refusal achieves nothing anyway |
| Wrong answers | Answer fraud proofs (F5) → dropped with challenges → restored | Signed answers and answer fraud proofs | Without them a node could silently delete one file's record (R1); with them every wrong answer is provable and PIR stops it aiming them at one file's readers (Theorem 4) |
| Verifiable PIR | — | Considered, not adopted | Each reader would stream about 100 MB per 1 GB domain before reading, about 250x a read |
| Storage checks | Commit-reveal PIR audits by assigned auditors | Daily STARK storage proof per node, 2,500 sampled leaves per TB, due within 10 minutes | No auditors to recognize or bribe; the deadline makes faking by rebuilding leaves infeasible (R4) |
| Sealing | Keyed slow permutation per node | Dropped for v1; storage deduplication by colluding operators accepted | It saves them storage but doesn't reduce availability ([research-notes.md](research-notes.md)) |
| Repair | Clay code with all 95 helpers | Clay code with 80 helpers, 32x worst case budgeted | Repair shouldn't depend on every holder cooperating (R7) |
| Ejection | Ejection on missed proofs | 3-day grace window, timestamped late proofs count, proofs via forced-inclusion DA | Chain censorship or DDoS shouldn't get honest nodes ejected (R8) |
| Phones | A design target | Out of scope for v1 | Simplicity |
| Operator independence | Open question | Accepted vulnerability | Stake can't distinguish one organization from many |

## Timeline

**Oct 18, 2026.** First consolidated design: per-file outer code with light mixing, distinct holders per stripe, sealing, challenges, auditors, a fast path and 8 GB PIR domains. The first adversarial review found F1–F11; the fixes were folded in. The build-or-integrate analysis chose a separate network over a Walrus layer. A SimplePIR benchmark confirmed scan throughput (about 10 GB/s per core) but showed its client hint rules it out.

**Oct 19, 2026 (in order).** YPIR benchmarked with no client hint. Mixing dropped, every read made PIR, domains set at 1 GB. Churn simulation found the repair ratchet (F12); placement moved to stake-weighted rendezvous hashing, and Theorem 1′ was written. The G2 traffic model showed reads are recognizable by timing (F13); G2 was restated as record privacy plus routing around refusals, and the anonymity layer was dropped. Phones taken out of scope; operator independence accepted as a vulnerability.

Next, challenges dropped: readers route around refusals and pay per verified answer. Auditors replaced by daily storage proofs.

Finally, a second independent review found R1–R14 (resolutions in the review log). Packs replaced the per-file outer code, raising the threshold for one chosen file from about 57.6% to 66.3% of stake. Verifiable PIR was considered to stop selective deletion and rejected for its per-reader setup cost; signed answers and answer fraud proofs were restored instead (Theorem 4).
