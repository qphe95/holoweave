# Security games: G1 and G2

Oct 18, 2026 · @qingpinghe

Draft definitions and paper proofs for Holoweave's two core guarantees. G1 (availability) is a probability bound that holds against any coalition behaviour; G2 (non-selectivity) is a reduction to PIR query privacy under an explicit unlinkability assumption. Both are written to be checked by an independent cryptographer.

## Model and notation

| Symbol | Meaning | Default |
| --- | --- | --- |
| *N*, *σ\_v* | Number of nodes; stake share of node *v* (Σ *σ\_v* = 1) |  |
| *C*, α | Coalition (set of corrupted nodes) and its total stake share |  |
| *w*, *n* | Symbols needed to decode a stripe; holders per stripe | 32, 96 |
| *t* | Blocking threshold: *n* − *w* + 1 corrupted holders | 65 |
| *m* | Pieces per file after the outer code; any *m*/2 rebuild it | at least 32 |
| *d* + 1 | Stored blocks per piece (one data block plus *d* randomizers) | 3 |
| *H\_s* | The holders of stripe *s* |  |
| *R*, *D* | Records and size of one node's PIR domain |  |
| Π | The PIR scheme: Query, Answer, Decode | YPIR or similar |

**Placement.** For each stripe *s*, the beacon draws the *n* slots of *H\_s* independently, **with replacement**, in proportion to stake, so a node may hold several slots of one stripe. The beacon is modelled as a random oracle queried on the stripe identifier, so placements of distinct stripes are independent. With this rule a coalition's share of slots equals its share of stake exactly, and the count of corrupted slots in a stripe is Bin(*n*, α). Drawing distinct nodes instead was rejected after simulation: it caps every node at one slot per stripe, so a censor running many small identities can gain slots at the expense of large honest operators (see Simulation results).

**Files.** A file *F* is outer-coded into *m* pieces. Piece *i* is recovered by XORing *d* + 1 stored blocks that live in stripes *s*(*i*, 0), …, *s*(*i*, *d*). We assume these (*d* + 1)*m* stripes are distinct; placement enforces this, and a collision only shrinks the set of stripes an adversary can attack, so it never helps it.

**Honest behaviour.** A node outside *C* stores its symbols and returns them correctly when asked. This is the assumption audits exist to maintain; it is outside both games.

**Adversary.** *C* is chosen before the placement randomness is revealed (static corruption). After that, *C* sees everything public: addresses, placements, Merkle roots, every message sent to its members. It may make its members refuse, delay, delete or corrupt anything. Adaptive corruption after placement is treated separately in G1's limits.

## G1: Availability

**Game Avail(𝒜, α, F)**

1. 𝒜 chooses a coalition *C* with stake share at most α.
2. An honest client uploads *F*; the beacon samples placement for every stripe.
3. 𝒜 learns all public data and controls every node in *C* arbitrarily.
4. An honest reader runs the full read procedure: it contacts every holder of every stripe of *F*, verifies each symbol against its Merkle root, decodes the stripes it can, XORs blocks into pieces, and decodes *F* from any *m*/2 valid pieces.
5. 𝒜 wins if the reader fails to output *F*.

**Theorem 1.** Let *p* = Pr\[Bin(*n*, α) ≥ *t*\] and *q* = 1 − (1 − *p*)^(*d*+1). For every adversary, even computationally unbounded in its strategy,

```latex
\Pr[\mathcal{A}\ \text{wins}] \;\le\; \Pr\!\left[\mathrm{Bin}(m, q) \ge \tfrac{m}{2} + 1\right] \;+\; \varepsilon_{\mathrm{hash}} + \varepsilon_{\mathrm{beacon}}
```

where ε\_hash bounds Merkle-path forgery (collision resistance) and ε\_beacon bounds the beacon's deviation from a random oracle.

**Proof.**

1. *A stripe fails only if* |*H\_s* ∩ *C*| ≥ *t*. Otherwise at least *n* − *t* + 1 = *w* holders are honest and return valid symbols. Corrupted symbols are rejected by Merkle verification (except with probability ε\_hash), and any *w* valid symbols decode the stripe (MDS property).
2. *Each stripe fails with probability at most p.* Slots are independent stake-weighted draws, so |*H\_s* ∩ *C*| \~ Bin(*n*, α). *C* is fixed before the beacon, so it cannot depend on the draw.
3. *Each piece fails with probability at most q, independently.* Piece *i* fails only if one of its *d* + 1 distinct stripes fails. Distinct stripes have independent placements (random-oracle beacon), so failures are independent across stripes and therefore across pieces.
4. *The file fails only if at least m/2 + 1 pieces fail*, because the outer code decodes from any *m*/2. The number of failed pieces is dominated by Bin(*m*, *q*). ∎

**Numbers** (*n* = 96, *w* = 32, *t* = 65, *d* + 1 = 3):

| Coalition stake α | Stripe fails, *p* | Piece fails, *q* | File fails, *m* = 32 | File fails, *m* = 64 |
| --- | --- | --- | --- | --- |
| 33% | 3.9 × 10^-12 | 1.2 × 10^-11 | about 10^-177 | below 10^-300 |
| 50% | 3.4 × 10^-4 | 1.0 × 10^-3 | 6.8 × 10^-43 | 2.5 × 10^-81 |
| 55% | 7.6 × 10^-3 | 2.3 × 10^-2 | 4.4 × 10^-20 | 4.5 × 10^-37 |
| 60% | 7.4 × 10^-2 | 2.1 × 10^-1 | 4.9 × 10^-5 | 4.1 × 10^-8 |
| 65% | 3.3 × 10^-1 | 7.0 × 10^-1 | 0.99 | about 1 |

A union bound over all files multiplies these by the number of files; at 50% stake, even 10^12 files leave the network-wide failure probability below 10^-30.

**What G1 does not cover**

- **Churn.** The game assumes all 96 holders are present. If a stripe is down to 90 holders, blocking needs 59 of them: at α = 50% that stripe fails with probability 2.1 × 10^-3 instead of 3.4 × 10^-4. Immediate repair keeps stripes near 96; a churn-aware version of the theorem needs a model of repair delay.
- **Adaptive corruption.** A censor who corrupts specific holders after placement is not bounded by α. Destroying *F* then needs at least *t* = 65 corrupted holders in at least one stripe of each of *m*/2 + 1 pieces. Simulation puts the cheapest such set at about 510 operators in a 1,000-node network and about 2,700 in a 10,000-node network with even stake, falling to about 600 at 10,000 nodes when the top 10 operators hold 30% of stake. Yearly reshuffles bound how long such leverage lasts. Formalizing this needs a model of corruption cost over time.
- **Targeted corruption.** Below the threshold, corrupting a file's symbols cannot make it unreadable (step 1); it only produces verification failures, which G3 turns into fraud proofs.

## G2: Non-selectivity

G2 says that on the private path, a coalition's decision to refuse a query can depend on which node and domain it hits, but not on which record inside the domain is wanted. It covers refusal only; targeted corruption of stored records is handled by G1 (it can't block below the threshold) and G3 (it produces fraud proofs).

**Leakage.** Each private query reveals to the coalition its **leakage** ℓ = (node, domain). We make two assumptions:

- **Query privacy of Π (standard).** For any two record indices *r*₀, *r*₁ in the same domain, the distributions of Query(*r*₀) and Query(*r*₁) are computationally indistinguishable; Adv\_priv(Π) is negligible under LWE.
- **Unlinkability (A\_unlink, protocol assumption).** Fixed-shape reads make every query look like an independent event: the coalition sees each query's ℓ and an arrival time drawn from a public distribution, through a fresh anonymity circuit, plus cover queries. Formally, the joint view of all queries in all reads is simulatable from the multiset of their ℓ values alone. This is the weakest link: it rests on the anonymity layer and traffic shaping, not on cryptography.

**Game NonSel(𝒜, *b*)**

1. 𝒜 (controlling *C*) picks a node *v* ∈ *C*, a domain of *v*, and two records *r*₀, *r*₁ in it.
2. The challenger runs honest background traffic, plus one query for *r\_b* to (*v*, domain), shaped as A\_unlink requires.
3. 𝒜 runs any refusal policy over the queries its nodes receive, and outputs a guess *b*′. It wins if *b*′ = *b*.

A policy is ε-**selective** if, for some domain, its refusal probability for queries targeting *r*₀ and *r*₁ differs by more than ε.

**Theorem 2.** Under A\_unlink, for any PPT coalition policy and any two records *r*₀, *r*₁ in the same domain, the refusal probabilities differ by at most Adv\_priv(Π). A read consisting of *k* queries can be singled out with advantage at most *k* · Adv\_priv(Π).

**Proof (reduction).**

1. Suppose a policy *P* refuses queries for *r*₀ with probability δ₀ and for *r*₁ with probability δ₁, with |δ₀ − δ₁| = ε.
2. Build a distinguisher ℬ against Π's query privacy. ℬ receives a challenge query *Q* for *r\_b*. It simulates the rest of *P*'s view from leakage alone, which A\_unlink permits, embeds *Q* as the query arriving at (*v*, domain), runs *P*, and outputs 1 if *P* refuses *Q*.
3. ℬ's advantage is exactly ε, so ε ≤ Adv\_priv(Π).
4. For a read of *k* queries, a hybrid argument switches the target of one query at a time; each step costs at most Adv\_priv(Π), for *k* · Adv\_priv(Π) in total. ∎

**Corollary (blast radius).** If a policy blocks queries for a file's record in a domain with probability δ, it blocks queries for *every* record in that domain with probability at least δ − Adv\_priv(Π). Combined with G1: to block a file on the private path, a coalition must refuse, with near-certainty, whole domains on at least 65 holders of a stripe for each of *m*/2 + 1 pieces. Every refused domain takes all its other records with it: at least 8 GB per hot domain or 1 TB per cold domain on CPU nodes, 64 GB or more on GPU servers.

**Limits**

- G2 says nothing about the fast path, where nodes see which record is requested; there the protection is G1 plus public challenges.
- If A\_unlink fails, for example through traffic analysis that links a read's queries across nodes, a coalition could recognize the *pattern* of a particular file's read and refuse only matching queries. The bound then degrades to how well the pattern identifies the file. This is why fixed-shape reads and cover traffic are part of the protocol, not optional.

## Simulation results

A Monte Carlo simulation of placement (20,000 stripes per setting) checked G1 at 1,000 and 10,000 nodes, under even stake and two concentrated distributions where the top 10 operators hold 13% to 39%.

**1. With even stake, G1's numbers hold.** Simulated stripe failure rates match the binomial model, slightly below it:

| Coalition stake | Stripe fails, simulated (10,000 nodes) | Binomial model | File fails, *m* = 32 |
| --- | --- | --- | --- |
| 50% | 2.0 × 10^-4 | 3.4 × 10^-4 | about 10^-46 |
| 55% | 7.5 × 10^-3 | 7.6 × 10^-3 | about 4 × 10^-20 |
| 60% | 7.4 × 10^-2 | 7.4 × 10^-2 | about 5 × 10^-5 |
| 65% | 0.32 | 0.33 | about 0.98 |

**2. Drawing distinct holders breaks the model when stake is concentrated.** If each stripe takes 96 *different* nodes, a large operator can hold at most one slot per stripe, so slot share stops tracking stake share. When honest stake sits with a few big operators and the coalition is many small nodes, the coalition gets far more slots than its stake: at 1,000 nodes with the top 10 holding 39%, a 60% coalition of small nodes blocked 80% of stripes, against 8% predicted. A censor can get the same effect by splitting into many identities. **Fix, now in the design:** draw slots with replacement in proportion to stake, so slot share equals stake share and G1's binomial bound holds for any stake distribution. This also resolves the open obligation on sampling without replacement.

**3. Correlated outages matter only when large.** With even stake and a 50% coalition, taking 5% or 10% of honest nodes offline at once still leaves file failure around 10^-19 to 10^-31. Taking 20% offline raises it to about 10^-3 to 10^-4, so repair speed after large outages matters. Rule of thumb: the coalition's share plus the share of honest nodes offline should stay below about 55%.

**4. Adaptive coercion takes hundreds to thousands of operators.** The cheapest set of operators a censor must coerce to destroy one file is about 510 (1,000 nodes) to 2,700 (10,000 nodes) with even stake, and about 600 at 10,000 nodes with concentrated stake, because large operators appear in many of a file's stripes.

The simulation is approximate: correlated-outage runs used one random draw per setting, and concentrated-stake runs with random coalitions are noisy. The script and full output are kept with the project files.

## Open proof obligations

- [ ] **Stake-weighted sampling without replacement.** Resolved by simulation: the design now draws slots with replacement by stake, which makes the count of corrupted slots exactly Bin(*n*, α).
- [ ] **Beacon model.** Bound ε\_beacon for the chosen threshold beacon or VDF, including bias by withholding.
- [ ] **Churn-aware G1.** Model repair delay and node failures, and restate Theorem 1 with stripes that may be temporarily below 96 holders.
- [ ] **Adaptive corruption.** Define a corruption-cost model over time and bound the cost of destroying one file, including yearly reshuffles.
- [ ] **A\_unlink.** Make the traffic model concrete (arrival distributions, cover-query rate, circuit reuse) and bound what an observer of all coalition nodes can link.
- [ ] **PIR instantiation.** Fix the scheme and parameters, and cite its query-privacy reduction to LWE with concrete security.
- [ ] **Mixing randomizers.** Confirm that drawing randomizer blocks from earlier uploads doesn't let an adversary choose which stripes a target file depends on.
- [ ] **Independent review.** Have a cryptographer check both games, the reductions and the numbers.
- [ ] **G3 and G4.** Write accountability and blind-ingest games in the same style.
