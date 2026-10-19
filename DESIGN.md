# Holoweave: a permaweb where censorship has to be all-or-nothing

Status: draft v0.1 · 2026-10-18

## 0. One-paragraph summary

Holoweave stores the whole archive as **one codeword of a locally correctable
polynomial code** (Reed–Muller family) spread across every storage node. That
codeword is bound to a **public commitment**, and every read and audit is a
query that **cannot be told apart** from any other. As a result:

1. **No byte on disk belongs to one file.** Making any single block
   unrecoverable means erasing or corrupting at least a fraction **δ** (about
   1/2 with our parameters) of *all* stored points, network-wide.
2. **Every stored point can be checked** against the public commitment. A node
   that holds back or changes data fails audits at the same rate δ, and any
   change it makes produces a public proof against it.
3. **A node can't see which file a request is for**, because queries are made
   indistinguishable (information-theoretically for small coalitions, and with
   computational PIR (private information retrieval) against everyone). A node
   that refuses to serve a file therefore refuses audits at the same rate.

So shadowbanning one file costs the same as visibly taking down about half the
network. The guarantee comes from coding theory, commitment binding and query
privacy, not from pricing.

---

## 1. What maths can and cannot guarantee (read this first)

Arweave's guarantee is economic: an endowment pays miners to keep data.
Holoweave aims at a different property, **non-selectivity**. These claims are
**not** achievable by any scheme, so we don't make them:

| Claim | Why it is impossible | What we guarantee instead |
|---|---|---|
| "No node can stop serving file F" | A node that can decode F can always refuse to answer. | It can't refuse F *without refusing everything at the same rate*. |
| "Data persists forever" | Maths can't keep hard drives powered. | Loss happens at network scale or not at all. Persistence still needs incentives or altruism (§9). |
| "Entanglement alone prevents selective deletion" | A server can decode everything, keep a private plaintext copy of everyone except the target, and re-encode. (See Aspnes–Feigenbaum–Yampolskiy–Zhong, *Towards a Theory of Data Entanglement*, which formalises all-or-nothing integrity and shows how limited it is without more structure.) | The re-encoded data **fails verification** against the fixed public commitment, and queries hide their target. Entanglement *at rest* is necessary but not sufficient. |

The design rests on three things, and dropping any one of them breaks it:

- **Code**: every block depends on a δ-fraction of all storage.
- **Commitment**: no node can swap in a different encoding without being caught.
- **Query privacy**: refusing to serve is blind to the target, so it shows up in audits.

---

## 2. Threat model

- **Censor**: a coalition 𝒜 that controls a fraction β of stored points,
  weighted by storage. It may collude completely, read all public data, decode
  every file, and choose which queries to answer. It can also coerce honest
  operators (legal pressure), which in effect moves their points into 𝒜.
- **Goal of the censor**: make a target set T of blocks unretrievable (or
  retrievable only with probability ≤ ε), while keeping the damage to other
  data and the detectable misbehaviour as small as possible.
- **Assumptions**: a collision-resistant hash and a binding vector or
  polynomial commitment; LWE for the strong-privacy tier (§5.3); a public
  randomness beacon for placement; and clients that can reach at least some
  honest nodes. Network-layer eclipse attacks are out of scope (§9).

## 3. Security goals

Let **C** be the public commitment to the fabric (the global codeword).

- **G1 Binding.** Every response a node gives can be checked against C. A wrong
  value comes with a short, publicly checkable proof of misbehaviour.
- **G2 Robust local recovery.** If at most a δ fraction of points are refused
  or wrong, every block can be recovered with high probability, and recovering
  a block never requires reading that block's own point.
- **G3 Target blindness.** For a coalition below the privacy bound (§5), the
  view of a retrieval query for block x is identically (or computationally)
  distributed for every x, and identical to the view of an audit query.
- **G4 Blast-radius theorem (the headline).** Under G1–G3, any strategy that
  pushes the success probability of retrieving x below 1−ε must:
  (a) withhold or corrupt at least ≈ (1−ε)·δ·N points in total, where N is the
  fabric size, and
  (b) fail at least ≈ (1−ε)·δ of *all* audits, whatever their target.

---

## 4. Construction

### 4.1 The fabric (encoding)

- Pick a field F_q (for example GF(2^12), with q = 4096), a number of variables
  m = 2, and a total degree d < q.
- Interpret the archive's blocks as the values of a polynomial
  f : F_q^m → F_q^B of total degree ≤ d. Each block is a length-B vector, and
  the code is applied coordinate-wise, so a "point" stores a whole block.
- The **fabric** is f evaluated at all N = q^m points. Message size is
  C(d+m, m) ≈ d²/2 blocks.
- Before encoding, each file goes through an **all-or-nothing transform**
  (Rivest's AONT: encrypt with a random key, then XOR the key into a hash of
  the ciphertext). Fragments of a file are then worthless on their own, and
  file contents stay opaque to casual scanning.

Why Reed–Muller: the restriction of f to any line (or low-degree curve) is a
univariate polynomial of degree ≤ d (or ≤ d·t for a degree-t curve). That
gives:

- **Local correction**: recover f(x) from any d+1 good points on a random line
  through x.
- **Smoothness**: every individual query point is uniform over F_q^m,
  whichever x is being recovered (§5.1).
- **Local testability**: if the points on a line don't fit a degree-d
  polynomial, that line is a fraud proof of bad encoding.

Higher-rate options are listed in §7: lifted Reed–Solomon codes and
multiplicity codes keep locality with rate approaching 1.

### 4.2 Commitment

- **Vector commitment**: a Merkle tree over the hashes of the N point-blocks.
  Its root is **C**. An audit response is a block plus a Merkle path.
- **Correct encoding**: either
  (a) *optimistic* checking: anyone can sample random lines, and an
  inconsistent line is a fraud proof (RM codes are locally testable), or
  (b) *validity proofs*: a binary-field polynomial commitment such as
  Binius/FRI-Binius proves that C is a degree-≤d evaluation table. Option (b)
  is preferred because it removes the fraud-proof window.
- C is anchored in an append-only log (any blockchain, or a transparency log
  with gossip). The binding property is what defeats the "re-encode without
  the target" attack.

### 4.3 Placement and replica uniqueness

- Points are assigned to nodes by a beacon-seeded pseudorandom permutation. No
  one chooses which node holds what, and every node holds a uniform sample.
- Each node *seals* its points with a slow, node-specific encoding (as in
  Filecoin's proof-of-replication). One physical copy then can't be passed off
  as many Sybil nodes, so β measures real disk.
- **Consequence:** no file has "its" set of holders that can be targeted. To
  censor one file you must coerce operators who together hold a δ-fraction of
  *the entire network*. That is the blast radius as it applies to legal
  coercion.

### 4.4 Audits

Auditors (clients, volunteers, other nodes) send a stream of challenges for
uniformly random points, using **secret** randomness and **the same query
format as retrievals** (§5). A node's pass rate is public reputation and
eviction input. Answers are checked against C (G1).

Audits must not be derivable from the public beacon. Otherwise a node could
tell audits from retrievals and serve only the audits.

### 4.5 Appending: log-structured fabrics

One global codeword can't be cheaply updated block by block. We use an
LSM-style hierarchy (log-structured merge, as in LSM trees):

```
L0  small fabrics (minutes of uploads)        weak blast radius
L1  merged fabrics, 2^k × larger
...
Lk  top fabric: whole archive                 full blast radius
```

- When level i fills up, its fabrics are decoded and re-encoded into one
  level-(i+1) fabric. The new commitment is checked against the old ones by
  random-point equality tests: two distinct low-degree polynomials agree at a
  random point with probability ≤ d/q (Schwartz–Zippel).
- Each byte is re-encoded O(log N) times over its life (amortised).
- **Known weakness:** new uploads sit in small fabrics and have a small blast
  radius until they merge upward. Mitigations: merge quickly, and
  cross-entangle each L0 fabric with a beacon-chosen sample of top-level
  blocks (Tangler / alpha-entanglement style).

### 4.6 Index and discovery

Shadowbanning usually happens at the *discovery* layer, not in storage. So:

- The name → (fabric, point range) index is itself stored in the fabric and
  covered by C.
- Index lookups use the same private-query path as data. Otherwise the lookup
  would reveal the target.
- Gateways and search engines are optional caches. Clients can always fall
  back to direct private retrieval.

---

## 5. Retrieval: making refusal blind

There are three paths. Every client uses the fast path first, and the private
paths double as cover traffic for audits.

### 5.1 Tier A: information-theoretic private correction

To recover f(x), the client picks a random degree-t curve γ with γ(0) = x and
sends γ(λ₁), …, γ(λ_k) to k different nodes, with k ≥ d·t + 1 plus slack.

- Any ≤ t of those points are jointly uniform and independent of x (the same
  argument as Shamir secret sharing). This is the Chor–Goldreich–Kushilevitz–Sudan
  multi-server PIR from Reed–Muller codes, where smooth locally decodable codes
  are equivalent to PIR (Katz–Trevisan).
- Each node sees a single uniformly random point, exactly like an audit.
- **Limit:** privacy only holds while the coalition sees ≤ t points of the
  curve, which roughly means β ≲ 1/d. Against large coalitions, Tier A gives
  robustness (they can't block a curve unless they hold more than k−d·t−1 of
  its points) but not privacy.

### 5.2 Tier B: computational PIR per node (the strong guarantee)

The client fetches specific points from a node using single-server lattice
PIR (SimplePIR- or FrodoPIR-style, based on LWE). Its **anonymity bucket** is
the node's whole PIR database, or a configured sub-bucket.

- The node computes over the entire bucket for every query and learns nothing
  about which point was asked for, **even if all nodes collude**.
- Audits use the same PIR format. Refusal is then per-bucket at most, and a
  node refusing a bucket fails exactly that bucket's share of audits.
- **Bucket size is the blast-radius knob for serving-layer refusal.** Since the
  target is also recoverable from *other* points via §5.1 or §5.3, one node
  refusing does nothing. A coalition must refuse a δ-fraction of buckets
  network-wide.
- Cost: server work grows linearly with bucket size per query, with batching
  (§7). This is the path for censored content and for audits, not for bulk
  traffic.

### 5.3 Fast path: plain reads (no privacy)

Direct Merkle-proven reads of a block's own point, or of a cached file. These
are cheap and selectively refusable. That's fine: refusing the fast path can't
remove data. It only pushes the client onto Tier A or B, where refusal costs
the censor everything.

---

## 6. The blast-radius argument (proof sketch of G4)

Fix target x. Let S be the set of points the coalition withholds or corrupts.
Because of G1, corruptions are detected and become erasures.

**(a) Storage cost.** The lines through x split F_q^m \ {x} into
(q^m − 1)/(q − 1) disjoint lines of q−1 points each. A line can be decoded
unless it has more than q−1−d erasures. To make a random line through x fail
with probability ≥ 1−ε, S must contain more than q−1−d points on at least a
(1−ε) fraction of those lines:

  |S| ≥ (1−ε) · (q−1−d)/(q−1) · (q^m−1) ≈ (1−ε) · δ · N,  where δ = 1 − d/q.

δ is also the relative distance of the code. So the erasure set needed to deny
**one** block is about as large as the set that voids the code's
unique-recovery guarantee for the **whole fabric**. There is no cheap
"surgical" erasure.

**(b) Visibility.** Under G3, the coalition's decision to answer a query can
depend only on the query's distribution, which is the same for audits and for
retrievals of any block. Its refusal rate on audits therefore equals its
refusal rate on retrievals, which by (a) is ≥ (1−ε)·δ. Under G1, a wrong
answer is a transferable proof of misbehaviour.

**(c) No re-encoding escape.** A node that drops x's information can't
reproduce the committed points, because essentially every point's value
depends on x through f. A proof-of-retrievability extractor (Juels–Kaliski;
Shacham–Waters) turns "passes ≥ 1−δ of audits" into "x can be extracted from
this node's storage." Passing audits *is* holding x.

**What we do *not* claim:** that every other file is guaranteed to die when x
does. The guarantee is about the censor's **cost** (δ·N points) and
**visibility** (δ audit failure rate). Collateral loss is likely but not
proven. Turning it into a theorem is open problem #1 (§10).

---

## 7. Parameters and costs (example top-level fabric)

| Parameter | Value |
|---|---|
| Field, variables, degree | GF(2^12), m = 2, d = 2047 (d/q ≈ 1/2) |
| Points N | q² = 2^24 |
| Message blocks | C(d+2, 2) ≈ 2^21 |
| Rate / storage overhead | ≈ 1/8 / 8× |
| δ (denial threshold = code distance) | ≈ 1/2 |
| Block size | 256 KiB |
| Data per fabric / stored | 512 GiB / 4 TiB network-wide |
| Tier A read amplification | ≈ d+1 = 2048 blocks per block (512 MiB per 256 KiB). Last-resort path |
| Tier B per-query server work | linear in bucket size, e.g. 64 GiB bucket ≈ seconds of SIMD work per core |
| Fast path | 1 block + Merkle path |

Tuning levers:

- **Rate vs. δ vs. locality.** Plain RM codes trade these off badly. Lifted
  Reed–Solomon codes (Guo–Kopparty–Sudan) and multiplicity codes
  (Kopparty–Saraf–Yekhanin) reach rate close to 1 with n^ε locality. The
  Kopparty–Meir–Ron-Zewi–Saraf high-rate LDCs reach 2^{Õ(√log n)} queries.
  Each gives up some δ for rate. Choose δ ≥ 1/3 at minimum.
- **Tier B batching.** Answering many PIR queries in one pass over the bucket
  (matrix–matrix instead of matrix–vector) cuts per-query cost by a large
  factor.
- **Bucket size** trades anonymity and blast radius for PIR cost.

---

## 8. Comparison

| System | Durability basis | Selective deletion | Our difference |
|---|---|---|---|
| Arweave | Economic endowment plus random-recall mining | Nodes may drop any chunk they dislike (content policies are explicitly allowed) | Data is mixed globally, so dropping one item breaks commitments |
| Filecoin | Per-deal proofs of replication and spacetime | Per-deal, so holders are known and targetable | No per-file holders |
| IPFS | None (pinning) | Trivial | Entire design |
| Tangler / Dagster (2001) | Entangle new blocks with old ones | Raises cost but doesn't bind or hide queries (re-encode attack) | Adds commitment and query privacy |
| Alpha entanglement codes | Local XOR lattices | Cost is local, so blast radius is small | Global, smooth code |
| Ethereum data-availability sampling (2D RS + KZG) | Short-term availability | Not for permanent storage | Same toolbox, used for permanence plus PIR |

## 9. Still not guaranteed (honest residuals)

1. **Persistence.** If half the network goes offline because nobody pays for
   it, data is lost, but non-selectively. Pair Holoweave with an endowment
   (Arweave-style) or an altruistic set of mirrors.
2. **A coalition above δ** can still destroy the network. It just can't do so
   quietly or selectively. Choose δ and decentralisation together.
3. **Proving refusal.** A wrong answer is provable. A *non-answer* isn't
   provable to third parties (the fair-exchange problem). Options: witness
   committees, or relaying challenges through a public bulletin with response
   deadlines. Either needs care so audits stay indistinguishable.
4. **Network-layer censorship.** ISPs or eclipse attacks blocking clients from
   honest nodes. Use mixnets or Tor-style transports for Tier A/B.
5. **New uploads** have a weaker blast radius until merged (§4.5).
6. **Operators can't comply with takedowns of single items.** That is the
   design goal, but it also means operators face legal exposure for unlawful
   content they can't remove without leaving the network. Expect a
   policy/legal workstream (for example, operators in jurisdictions with
   intermediary-liability protection, and client-side content filtering at
   the display layer) before deployment.

## 10. Open problems

1. **Collateral theorem.** Give a code family and an erasure model in which
   denying any block provably destroys a constant fraction of *all other*
   blocks. Candidates: non-systematic RM, where every message coefficient
   depends on every point, plus an argument based on the structure of minimal
   erasure patterns.
2. **Tier B cost.** Reduce per-query PIR work using preprocessing PIR (for
   example offline/online "piano"-style schemes) without breaking audit
   indistinguishability.
3. **Merge proofs.** Concrete, cheap proofs that a level-(i+1) commitment
   contains exactly the union of the level-i fabrics.
4. **Publicly verifiable refusal** that doesn't let nodes tell audits apart.
5. **Incentive layer** that pays for audit pass rate, so the economic and
   mathematical guarantees reinforce each other.

## 11. Prototype plan

1. Reference RM encoder and local corrector over GF(2^12), coordinate-wise on
   blocks. Measure throughput.
2. Merkle commitment plus line-test fraud proofs. Then evaluate a Binius-style
   validity proof.
3. Simulator: N points, M nodes, a coalition strategy, audit stream. Measure
   empirically the δ needed for denial, audit failure rates, and collateral
   loss (this feeds open problem #1).
4. Integrate a SimplePIR-style Tier B client and server. Benchmark per-bucket
   cost.
5. LSM merge pipeline and Schwartz–Zippel equality checks.

## References

- J. Aspnes, J. Feigenbaum, A. Yampolskiy, S. Zhong. *Towards a Theory of Data Entanglement.* ESORICS 2004 / TCS 2007.
- M. Waldman, D. Mazières. *Tangler: A Censorship-Resistant Publishing System Based on Document Entanglements.* CCS 2001.
- A. Stubblefield, D. Wallach. *Dagster: Censorship-Resistant Publishing Without Replication.* 2001.
- V. Estrada-Galiñanes et al. *Alpha Entanglement Codes.* DSN 2018.
- B. Chor, O. Goldreich, E. Kushilevitz, M. Sudan. *Private Information Retrieval.* FOCS 1995 / JACM 1998.
- J. Katz, L. Trevisan. *On the Efficiency of Local Decoding Procedures for Error-Correcting Codes.* STOC 2000.
- S. Yekhanin. *Locally Decodable Codes* (survey). 2012.
- S. Kopparty, S. Saraf, S. Yekhanin. *High-Rate Codes with Sublinear-Time Decoding* (multiplicity codes). STOC 2011.
- A. Guo, S. Kopparty, M. Sudan. *New Affine-Invariant Codes from Lifting.* ITCS 2013.
- S. Kopparty, O. Meir, N. Ron-Zewi, S. Saraf. *High-Rate Locally Correctable and Locally Testable Codes with Sub-Polynomial Query Complexity.* STOC 2016 / JACM 2017.
- A. Juels, B. Kaliski. *PORs: Proofs of Retrievability for Large Files.* CCS 2007.
- H. Shacham, B. Waters. *Compact Proofs of Retrievability.* ASIACRYPT 2008.
- R. Rivest. *All-or-Nothing Encryption and the Package Transform.* FSE 1997.
- A. Henzinger et al. *One Server for the Price of Two: Simple and Fast Single-Server PIR* (SimplePIR). USENIX Security 2023.
- B. Diamond, J. Posen. *Succinct Arguments over Towers of Binary Fields* (Binius). 2023.
- Protocol Labs. *Filecoin: proof-of-replication and proof-of-spacetime.*
