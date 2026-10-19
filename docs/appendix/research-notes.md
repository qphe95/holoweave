# Research notes

> **Historical record.** This file records past work and is not the current design; where it disagrees with [../design.md](../design.md), the design wins. A summary of what changed and why is in [history.md](history.md).

These notes record the math behind decisions in the design. They are background, not the design itself.

| Topic | Status | Where it matters |
| --- | --- | --- |
| Sealing with a keyed slow permutation | Dropped for v1; kept as a fallback if simulations show the slot-compression attack pays | Data encoding, sealing |
| Coded PIR (the erasure code as the PIR) | Dropped: any coalition able to block a stripe can break its privacy | Explains why the private path uses LWE PIR |
| Doubly-efficient PIR | Parked until storage blowup falls about 1,000x | A possible future private path with node-wide domains |
| Audits as plain PIR queries | Superseded by commit-reveal audits; removed | Audits, refusal and accountability |

## Coded PIR (dropped)

**Status: dropped. Not part of the design.** No information-theoretic PIR can stop selective censorship on this storage (see *The barrier* below). Holoweave keeps LWE PIR in buckets. This section is kept only as a record of what was tried and why it failed.

**The idea.** Use the storage code's own structure for information-theoretic PIR (star-product and Lagrange-style constructions), private against up to *T* colluding holders, with built-in error correction. It worked, at about 2x to 3x the download of LWE PIR, but the barrier below rules it out for anti-censorship.

**The barrier.** Stripes are an MDS code of dimension *w* on *n* holders.

- *Blocking* a stripe needs at least *n* − *w* + 1 = 65 refusing holders. With fewer, *w* honest symbols remain.
- *Any* information-theoretic PIR that is private against *T* colluders and downloads less than the whole batch needs *T* ≤ *n* − *w* = 64. The sketch: if *T* ≥ *n* − *w* + 1, the honest holders number at most *w* − 1, and in evaluation form that leaves every individual piece undetermined. The coalition's answers must be independent of the target, yet the reader must decode whichever piece it chose. So the coalition's answers must carry essentially every piece, which means downloading the batch. This matches the known capacity results for coded PIR with colluders, which fall to the trivial rate once (*w* + *T* − 1)/*n* ≥ 1. Formalizing the sketch is a contained exercise.
- So every coalition that can block can also see which file a coded read targets. That is precisely the regime where PIR matters: below 65, honest holders serve X anyway; at 65 or above, PIR is what forces the censor to refuse whole buckets instead of X alone.
- LWE PIR escapes the barrier because its privacy is computational and holds against any number of colluders. It is also already safe against quantum computers, so idea 2 had no quantum advantage either.

**Verdict: dropped.** It is not part of the design, either for anti-censorship or as an optional mode. Construction details were removed in cleanup and remain in the document history.

## Sealing with a keyed slow permutation (dropped for v1)

Sealing is needed after all, against an attack the design doc missed, and it can be made compatible with PIR. The tool is a keyed permutation that is slow in one direction and fast in the other: sealing costs about 160 ms per record and unsealing about 0.5 ms.

**The attack: compressing the code across slots.** An operator holding *|J|* > *w* evaluation points of a batch stores only *w* symbols per stripe and computes the rest from them on demand, with cheap field arithmetic. Every answer it gives is exact, so audits and fraud proofs never fire. With 64 slots it stores half of what it is paid for, and the network's redundancy is fake.

**Construction.** Use a Sloth-style permutation on a prime field with *p* ≡ 3 (mod 4). It is built from *k* rounds, each keyed by a round constant *c\_i* derived from the node's registered key, the batch, the record index and the element index:

```latex
\text{seal (slow)}: \; x \leftarrow \sqrt{x + c_i} \quad\quad \text{unseal (fast)}: \; x \leftarrow x^2 - c_i
```

- A square root costs one exponentiation (about 255 squarings). Undoing it costs one squaring, so the asymmetry is roughly 250x. Non-residues are handled with Sloth's sign-flip rule.
- Node *j* stores, for every record and element, the sealed value *s* = Seal(*y*) and never *y* itself.
- PIR runs over the sealed records as they are. A reader or auditor unseals the one record it received and checks it against the commitment. Fraud proofs stay public, because anyone can unseal.
- The keys bind each sealed replica to one node identity, so two slots never store the same bytes, even for the same evaluation point after a repair.

**The bound.** To pass a bucket scan without storing a record, the operator must re-seal it in time, *k* square roots per element. Skipping a bucket of *B* bytes and *R* records pays only if re-sealing it for every scan in a period costs less than storing it:

```latex
\text{scans} \cdot R \cdot L \cdot k \cdot t_{\sqrt{}} \cdot c_{\text{cpu}} \;>\; B \cdot c_{\text{store}} \quad\Rightarrow\quad \text{storing is cheaper}
```

Partial skipping (a fraction *f* of records) instead fails each audit with probability *f* (see audits in the design), and slashing covers it.

**Parameters.** Assume storage at $2 per TB-month, CPU at $0.01 per core-hour, weekly scans, *L* ≈ 1,024 elements per 32 KB record and *t*√ ≈ 12 µs on a CPU (to be measured).

| Attacker's hardware | Work needed per element | Rounds *k* |
| --- | --- | --- |
| CPU | 4.9 µs | 1 |
| 30x cheaper per square root (GPU-class) | 147 µs | 13 |

**Default *k* = 13.** Honest costs at that setting:

- Sealing 20 TB once: about 27,000 core-hours (about $270), spread over onboarding. Repairs carry the same cost per rebuilt symbol, so new holders take hours to days to come online.
- Unsealing: about 0.5 ms per record. A 1 MB private read is about 0.5 core-seconds; fast-path serving runs at about 64 MB/s per core.

**Limits**

- Security rests on cost, not latency: records seal independently, so an attacker with enough parallel hardware can re-seal quickly; it just pays for it. Hardware advantage is the main risk, and a square-root ASIC far beyond 30x would break the parameters. Speedups of exactly this kind are a known concern with Sloth-style encodings.
- A latency-based alternative chains records through a depth-robust graph (Fisch's PoRep constructions). Unsealing a record then needs its parents, so each private read costs about (*d* + 1)x more. That is rejected for v1.
- Sealing proves the bytes exist, not that they sit on independent hardware. One operator can still put many sealed slots on one disk. Stake caps per batch address that, not sealing.

## Doubly-efficient PIR (parked)

**Status: parked. Not part of v1.** Every known family fails on Holoweave's large records:

- Public-key doubly-efficient PIR (DEPIR) still needs storage thousands of times larger than the data.
- Information-theoretic multi-server DEPIR is ruled out by the coded-PIR barrier.
- The one constant-overhead family is secret-key: it clashes with a public permaweb, and at published parameters a single read touches hundreds of thousands of positions.

The payoff is also smaller than it first looked: bucket refusal is already visible and slashed.

**What it would buy.** Today a node learns which \~1 GB bucket is read, so its smallest refusal is one bucket. PIR at polylogarithmic cost over the whole node would raise that to all 20 TB, and drop the bucket scan from every read. Availability and P6 don't change, because audits and reader escalation already catch bucket refusal.

**State of the art**

| Scheme | Setting | Storage | Query cost | Fit for Holoweave |
| --- | --- | --- | --- | --- |
| [Lin, Mook, Wichs (STOC 2023)](https://dl.acm.org/doi/10.1145/3564246.3585175) | Public-key, one server | Naively over 10^78 entries for about 2^20 items | Polylogarithmic | Theory only |
| [Okada, Player, Pohmann, Weinert (FC 2024)](https://fc24.ifca.ai/preproceedings/148.pdf) | Public-key | About 5 × 10^5 stored entries per item; 873 TB for 15 M two-byte items (extrapolated) | About 32 s amortized | No |
| [Xiao et al. (ePrint 2026/243)](https://eprint.iacr.org/2026/243) | Public-key, batched | 171 GB for 2^23 items (prior work: 733 TB) | 112 s per batch of 5,461; 21 ms amortized | Closer, still far above 3x |
| [Lazzaretti et al. (TCC 2025)](https://eprint.iacr.org/2024/829) | Multi-server, information-theoretic | N^(1+o(1)) | N^(o(1)) | Ruled out by the coded-PIR barrier |
| [Chen, Ishai, Jain, Mour, Rosen, Xing (ePrint 2026/1480)](https://eprint.iacr.org/2026/1480) | Secret-key | 4.2x | Under 600 KB read per query, for 18-bit items in a 37 GB database | Storage fits; key model and read volume don't |

**Can storage and preprocessing be one object?**

- **Public-key DEPIR: no.** LMW's table is the database polynomial over *record indices*, evaluated at every point of several small-prime domains, on one server. Holoweave's code runs over *node indices* within a stripe, at 3x. They encode different axes, and using LMW's table as the storage code would put storage overhead in the thousands.
- **Secret-key DEPIR: yes, in principle.** The "permuted code" blueprint stores a Reed-Muller-style locally decodable codeword, secretly permuted and masked. At 4.2x that codeword is itself an erasure code, so it could replace the stripe encoding outright, with each node holding a slice.

**Obstacle 1: who holds the key.** Secret-key schemes are private only if the server lacks the key, but every reader must be able to read and a censor can pose as a reader. The candidate fix is a committee holding the key in shares:

1. **Placement.** The committee computes the permutation in MPC, about 1,500 PRP evaluations a second for 1 TB of daily uploads at 4.2x. Each member adds its own mask keyed by physical position.
2. **Read.** The reader secret-shares its decoding query to the committee. The committee checks inside MPC that the query is a valid decoding query, maps it to physical positions, and returns those positions plus one combined mask. The reader fetches the masked symbols, decodes linearly and removes the mask.
3. **Why the check in step 2 matters.** A reader free to choose positions or coefficients could unmask single symbols, or differences of two, and match them against the publicly computable codeword. That maps out the permutation in roughly (codeword size) ÷ (positions per read) reads, about 10^4 for a 20 TB node. After that, the reader could recognize X's queries.

**Obstacle 2: read volume.** At the published parameters a query reads under 600 KB of 18-bit items, i.e. about 270,000 positions. If locality scales similarly with 32 KB records as symbols, a single record read fetches gigabytes over the network, worse than today's local 1 GB scan. Splitting records into small symbols makes it worse, not better.

**Verdict: parked.** Revisit if (a) public-key DEPIR storage falls by about three more orders of magnitude, or (b) a permuted-code scheme appears with locality suited to large records and a key that can be public or held without MPC. The committee-keyed construction is a reasonable research question in its own right, but it would add a trust assumption for a modest gain.

## Open problems and what to prove next

1. **Measure before fixing parameters:** square-root time *t*√ on CPU and GPU, YPIR response size and scan throughput on 1 GB buckets, unseal throughput. Each feeds a bound above.
2. **Sealing soundness proof.** Model the permutation as an ideal cipher with a per-call cost, and show an operator storing *(1 − ε)* of its sealed bytes either pays the re-sealing cost or fails audits with probability at least ε per query. This joins P7 in the security games.
3. **Hardware advantage.** Get a credible estimate of the best ASIC speedup for modular square roots, or switch to a slow permutation with a better-understood hardware ratio.
4. **Idea 2 barrier, formal version** (idea 2). Turn the sketch (any T-private information-theoretic PIR on this storage with T ≥ n − w + 1 must download the batch) into a full proof. It is short and a good first Lean target.
5. **Update the security games.** Guarantees G1 and G2 must model sealing and commit-reveal audits: a coalition's strategies become storing, re-sealing, corrupting or refusing, each with the detection rates above.
