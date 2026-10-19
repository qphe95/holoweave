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
| *d* + 1 | Stored blocks per piece (one data block plus *d* randomizers; mixing dropped, so 1) | 1 |
| *H\_s* | The holders of stripe *s* |  |
| *R*, *D* | Records and size of one node's PIR domain |  |
| Π | The PIR scheme: Query, Answer, Decode | YPIR or similar |

**Placement.** Each slot *j* of stripe *s* has a seed σ\_{s,j} from the beacon, drawn after the batch is final. Its holder is chosen by **stake-weighted rendezvous hashing** over the *current* node set: holder(*s*, *j*) = argmin over nodes *v* of *E\_v* / stake\_*v*, where *E\_v* = −ln *H*(σ\_{s,j}, id\_*v*) is a unit exponential. Node identities are fixed by the beacon after the node registers its key, so nobody can grind an identity that ranks first on chosen stripes. Two properties follow. First, a slot lands on a node with probability exactly proportional to its stake, and slots with different seeds are independent, so a node may hold several slots of one stripe (drawing with replacement) and the count of coalition slots in a stripe is Bin(*n*, α). Second, the holder depends only on who is in the network *now*, not on its history, so the coalition's share of slots equals its share of stake at every moment. Two earlier rules were rejected after simulation: drawing distinct nodes per stripe lets many small identities out-slot large honest operators, and giving each freed slot a fresh random holder lets a coalition that never leaves accumulate slots over time (the repair ratchet, see G1 under churn).

**Files.** A file *F* is outer-coded into *m* pieces, and each piece is stored as one block in its own stripe (mixing was dropped on Oct 19, so *d* = 0). We assume a file's *m* stripes are distinct; placement enforces this, and a collision only shrinks the set of stripes an adversary can attack, so it never helps it. The formulas keep *d* general so the earlier mixed design (*d* = 2, each piece needing 3 blocks in 3 stripes) can be compared.

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

**Numbers** (*n* = 96, *w* = 32, *t* = 65, *d* + 1 = 1, so *q* = *p*). With the earlier mixing (*d* + 1 = 3), a 60% coalition reached 4.9 × 10^-5 for *m* = 32; dropping it makes every file harder to kill.

| Coalition stake α | Stripe fails, *p* | Piece fails, *q* | File fails, *m* = 32 | File fails, *m* = 64 |
| --- | --- | --- | --- | --- |
| 33% | 3.9 × 10^-12 | 3.9 × 10^-12 | about 10^-186 | below 10^-300 |
| 50% | 3.4 × 10^-4 | 3.4 × 10^-4 | 5.3 × 10^-51 | 4.7 × 10^-97 |
| 55% | 7.6 × 10^-3 | 7.6 × 10^-3 | 4.8 × 10^-28 | 1.6 × 10^-52 |
| 60% | 7.4 × 10^-2 | 7.4 × 10^-2 | 1.1 × 10^-11 | 8.6 × 10^-21 |
| 65% | 3.3 × 10^-1 | 3.3 × 10^-1 | 1.5 × 10^-2 | 1.6 × 10^-3 |

A union bound over all files multiplies these by the number of files; at 50% stake, even 10^12 files leave the network-wide failure probability below 10^-30.

**What G1 does not cover**

- **Churn.** Theorem 1 assumes every slot is held and served. Departures, rebuild delay, downtime and outages are covered by Theorem 1′ in G1 under churn below.
- **Adaptive corruption.** A censor who corrupts specific holders after placement is not bounded by α. Destroying *F* then needs at least *t* = 65 corrupted holders in at least one stripe of each of *m*/2 + 1 pieces. Simulation under the current rules puts the cheapest such set at about 455 operators in a 1,000-node network and about 1,640 in a 10,000-node network with even stake (2,600 with 2 MB minimum files), falling to about 265 at 10,000 nodes when the top 10 operators hold 30% of stake. Yearly reshuffles bound how long such leverage lasts. Formalizing this needs a model of corruption cost over time.
- **Targeted corruption.** Below the threshold, corrupting a file's symbols cannot make it unreadable (step 1); it only produces verification failures, which G3 turns into fraud proofs.

## G1 under churn

Nodes leave, rebuilds take time, machines go offline and whole regions fail together. This section extends G1 to a network that changes over time, and records a flaw the analysis found in the earlier placement rule.

**The repair ratchet (flaw in the earlier rule).** Previously, any freed slot (after an exit, a failed audit or a reshuffle) went to a fresh random holder drawn by stake. Honest operators eventually leave; a censor never has to. Every honest exit releases slots, a fraction α of which the censor wins and then keeps, while new honest nodes never win slots back. With honest exit rate λ per node per year and reshuffle rate *r*, the censor's slot share *x* settles at

```latex
x^\ast = \frac{\alpha\,(\lambda + r)}{\lambda\alpha + r}
```

well above its stake share α. With α = 40%, λ = 0.5 and the planned yearly reshuffle of one third (*r* = 1/3), *x*\* ≈ 62%, past the availability threshold. The simulation confirmed the formula: under heavy churn (λ = 4) the share rose from 40% to 71% in six months and 89.7% after three years, exactly the predicted 0.897, and every stripe became blockable. Reshuffling faster only shrinks the excess (*r* = 4 per year still leaves 43% to 45%).

**The fix: memoryless placement.** With rendezvous hashing (see Placement), a slot's holder is a function of its seed and the current node set only. A joining node takes slots from every holder in proportion to its stake, so whatever the history, each slot is coalition-held with probability exactly α. Simulated under the same heavy churn, the coalition's share stayed at 40.0% to 40.4% for three years.

**Theorem 1′ (G1 under churn).** Fix any history *ℋ* of joins, exits, stake changes, downtime and outages up to time *τ*, chosen without knowledge of the slot seeds. Given *ℋ*, slots are independent (each depends only on its own seed), and each is in one of three states: coalition-held with probability α\_τ (the coalition's stake share at *τ*), honest but unavailable (rebuild pending or holder offline), or honest and available. Let β = Pr\[slot is not honest-available | *ℋ*\]. Then Theorem 1 holds at time *τ* with α replaced by β:

```latex
\Pr[\mathcal{A}\text{ blocks } F \text{ at } \tau \mid \mathcal{H}] \le \Pr\!\left[\mathrm{Bin}(m, q_\beta) \ge \tfrac{m}{2} + 1\right] + \varepsilon,\quad q_\beta = 1 - \left(1 - \Pr[\mathrm{Bin}(n, 1-\beta) < w]\right)^{d+1}
```

*Proof sketch.* Given *ℋ*, the state of slot (*s*, *j*) is a fixed function of σ\_{s,j}, and seeds are independent random-oracle outputs, so slot states are independent with the stated probabilities. A stripe is blockable only if fewer than *w* slots are honest-available, which has probability Pr\[Bin(*n*, 1 − β) < *w*\]; the rest is the proof of Theorem 1. ∎ Adaptive corruption after seeds are known is outside *ℋ* and stays a separate limit.

**What β is made of.** With abrupt honest exits at rate λ per year, rebuild delay *D*, transient downtime *u*₀ and a correlated outage of a fraction φ of honest stake:

```latex
\beta = \alpha + (1-\alpha)\Bigl[1 - \bigl(1 - \tfrac{\lambda D}{1 + \lambda D}\bigr)(1 - u_0)(1 - \varphi)\Bigr]
```

**Requirements.** Only β matters, and one file stays below 10^-18 failure while β ≤ β\_max:

| Minimum pieces per file *m* | β\_max at 10^-9 | β\_max at 10^-18 | β\_max at 10^-30 |
| --- | --- | --- | --- |
| 32 (1 MB) | 0.608 | 0.576 | 0.543 |
| 64 (2 MB) | 0.626 | 0.604 | 0.582 |
| 128 (4 MB) | 0.639 | 0.624 | 0.609 |

1. **Rebuild speed is not the binding constraint.** With 1% downtime, the longest rebuild delay that keeps a file below 10^-18 is about 120 days at α = 50% and λ = 0.5 per year (37 days if a 10% outage is also under way), 31 days even at λ = 2, and over a year for a 33% coalition. A protocol target of rebuilding within 7 days, most-degraded stripes first, leaves a wide margin.
2. **Correlated outages are.** With α = 50%, a simultaneous outage of 10% of honest stake gives about 5 × 10^-26 per file, 20% gives about 2 × 10^-10, and 30% about 4%: a temporary window in which the coalition could block a given file. At α = 33%, a 30% outage stays near 10^-33 and a 40% outage near 5 × 10^-11.
3. **Seizure is permanent, and repair cannot undo it.** If a fraction φ of all stake is destroyed at once, a stripe left with fewer than 32 honest holders of its data is lost as soon as the coalition withholds its symbols. Losing 20% of stake is about 2 × 10^-36 per file with α = 33% and 10^-11 with α = 40%; losing 30% with α = 33% is about 3 × 10^-5. Rebuilding after a 20% loss takes about 0.7 days at 1 Gbit/s of repair bandwidth per node and 7 days at 100 Mbit/s; that bounds exposure to further losses, not the initial one.
4. **Bigger minimum files are a free margin.** Raising the minimum from 32 to 64 pieces (2 MB bundles) moves β\_max from 0.576 to 0.604 at no storage cost. A 32-of-128 inner code would reach about 0.68, at 8x storage instead of 6x.

**Model check.** A time-stepped simulation (500 nodes, 1,000 stripes, 3 years, hourly steps, heavy churn: λ = 4, *D* = 30 days, 1% downtime) matched the β model within about 2x at stripe failure rates around 10^-2 under rendezvous placement.

## G2: Non-selectivity

G2 says that for every read (all reads are PIR), a coalition's decision to refuse a query can depend on which node and domain it hits, but not on which record inside the domain is wanted. It covers refusal only; targeted corruption of stored records is handled by G1 (it can't block below the threshold) and G3 (it produces fraud proofs).

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

**Corollary (blast radius).** If a policy blocks queries for a file's record in a domain with probability δ, it blocks queries for *every* record in that domain with probability at least δ − Adv\_priv(Π). Combined with G1: to block a file, a coalition must refuse, with near-certainty, whole domains on at least 65 holders of a stripe for each of *m*/2 + 1 pieces. Every refused domain takes all its other records with it: at least 1 GB per domain on CPU nodes, 64 GB or more on GPU servers. Blocking one 1 MB file this way refuses about 1 TB of unrelated data; a 2 MB file, about 2 TB.

**Limits**

- Every read is a PIR read (there is no plain fast path), so G2 covers all reads on all devices, and audit queries are indistinguishable from real ones by construction.
- If A\_unlink fails, for example through traffic analysis that links a read's queries across nodes, a coalition could recognize the *pattern* of a particular file's read and refuse only matching queries. The bound then degrades to how well the pattern identifies the file. This is why fixed-shape reads and cover traffic are part of the protocol, not optional.

## Simulation results

These first runs used the earlier rules (distinct holders, three mixed blocks per piece); items 1 to 3 are kept as the record of why those rules changed, and item 4 has been rerun under the current rules. A Monte Carlo simulation of placement (20,000 stripes per setting) checked G1 at 1,000 and 10,000 nodes, under even stake and two concentrated distributions where the top 10 operators hold 13% to 39%.

**1. With even stake, G1's numbers hold.** Simulated stripe failure rates match the binomial model, slightly below it:

| Coalition stake | Stripe fails, simulated (10,000 nodes) | Binomial model | File fails, *m* = 32 |
| --- | --- | --- | --- |
| 50% | 2.0 × 10^-4 | 3.4 × 10^-4 | about 10^-46 |
| 55% | 7.5 × 10^-3 | 7.6 × 10^-3 | about 4 × 10^-20 |
| 60% | 7.4 × 10^-2 | 7.4 × 10^-2 | about 5 × 10^-5 |
| 65% | 0.32 | 0.33 | about 0.98 |

**2. Drawing distinct holders breaks the model when stake is concentrated.** If each stripe takes 96 *different* nodes, a large operator can hold at most one slot per stripe, so slot share stops tracking stake share. When honest stake sits with a few big operators and the coalition is many small nodes, the coalition gets far more slots than its stake: at 1,000 nodes with the top 10 holding 39%, a 60% coalition of small nodes blocked 80% of stripes, against 8% predicted. A censor can get the same effect by splitting into many identities. **Fix, now in the design:** draw slots with replacement in proportion to stake, so slot share equals stake share and G1's binomial bound holds for any stake distribution. This also resolves the open obligation on sampling without replacement.

**3. Correlated outages matter only when large.** With even stake and a 50% coalition, taking 5% or 10% of honest nodes offline at once still leaves file failure around 10^-19 to 10^-31. Taking 20% offline raises it to about 10^-3 to 10^-4, so repair speed after large outages matters. Rule of thumb: the coalition's share plus the share of honest nodes offline should stay below about 55% (about 57% under the current rules; see G1 under churn).

**4. Adaptive coercion.** Rerun under the current rules (slots drawn with replacement by stake, one block per piece), the cheapest set of operators a censor must coerce after placement to destroy one file is:

| Network | *m* = 32 | *m* = 64 |
| --- | --- | --- |
| 1,000 nodes, even stake | about 455 | about 515 |
| 10,000 nodes, even stake | about 1,640 | about 2,600 |
| 1,000 nodes, top 10 hold 39% | about 82 | about 85 |
| 10,000 nodes, top 10 hold 30% | about 265 | about 305 |

With concentrated stake the count is small because the largest operators hold several slots of many stripes; those few operators also hold a large share of all stake. The count measures how many parties a censor must coerce, so concentration matters here even though it does not change G1. Yearly reshuffles bound how long such leverage lasts, and 2 MB minimum files help most in large, even networks.

The simulation is approximate: correlated-outage runs used one random draw per setting, and concentrated-stake runs with random coalitions are noisy. The script and full output are kept with the project files.

## Open proof obligations

- [ ] **Stake-weighted sampling without replacement.** Resolved by simulation: the design now draws slots with replacement by stake, which makes the count of corrupted slots exactly Bin(*n*, α).
- [ ] **Beacon model.** Bound ε\_beacon for the chosen threshold beacon or VDF, including bias by withholding.
- [ ] **Churn-aware G1.** Done: Theorem 1′ and its requirements are in G1 under churn. Remaining: a formal treatment of correlated outages whose timing the coalition can influence.
- [ ] **Adaptive corruption.** Define a corruption-cost model over time and bound the cost of destroying one file, including yearly reshuffles.
- [ ] **A\_unlink.** Make the traffic model concrete (arrival distributions, cover-query rate, circuit reuse) and bound what an observer of all coalition nodes can link.
- [ ] **PIR instantiation.** Fix the scheme and parameters, and cite its query-privacy reduction to LWE with concrete security.
- [ ] **Mixing randomizers.** Moot: mixing was dropped on Oct 19.
- [ ] **Independent review.** Have a cryptographer check both games, the reductions and the numbers.
- [ ] **G3 and G4.** Write accountability and blind-ingest games in the same style.
