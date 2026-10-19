# Security games: G1 and G2

Oct 18, 2026 · @qingpinghe

Draft definitions and paper proofs for Holoweave's two core guarantees, updated Oct 19, 2026 for 64 MB packs, the independent review (R1 to R14 in the Review log), and signed answers with answer fraud proofs (Theorem 4). G1 (availability) is a probability bound that holds against any coalition behaviour; G2 has two parts: record privacy, a reduction to PIR query privacy that holds whatever else a node knows about the reader, and routing around refusals, which needs no network assumption. Both are written to be checked by an independent cryptographer.

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

**Packs.** Since Oct 19 the outer code runs over **packs** of many files rather than over each file: a pack has *K* = 2,048 data pieces (64 MB) plus 2,048 parity pieces, any *m*/2 of its *m* = 4,096 pieces rebuild it, and data pieces are stored as-is. Each piece is one block in its own stripe (mixing was dropped, so *d* = 0), and a pack's *m* stripes are distinct. A chosen file is lost only if its pack is lost, so the games below take the pack as the unit; they keep *m* and *d* general so the earlier per-file code (*m* = 32) and mixed design (*d* = 2) can be compared.

**Identity randomness.** Each identity's ranking key uses a beacon value revealed only after its stake is locked, and stake is fixed per identity. Without this, a coalition could register many identities, learn how each ranks on already-published seeds and then move stake into the best ones, which breaks the assumption below that *C* is fixed before the placement randomness it benefits from.

**Honest behaviour.** A node outside *C* stores its symbols and returns them correctly when asked. This is the assumption daily storage proofs exist to maintain; it is outside both games.

**Adversary.** *C* is chosen before the placement randomness is revealed (static corruption). After that, *C* sees everything public: addresses, placements, Merkle roots, every message sent to its members. It may make its members refuse, delay, delete or corrupt anything. Adaptive corruption after placement is treated separately in G1's limits.

## G1: Availability

**Game Avail(𝒜, α, F)**

1. 𝒜 chooses a coalition *C* with stake share at most α.
2. An honest client uploads *F*; it is coded into a pack, and the beacon samples placement for every stripe.
3. 𝒜 learns all public data and controls every node in *C* arbitrarily.
4. An honest reader runs the full read procedure: it contacts every holder of every stripe of the pack, verifies each symbol against its Merkle root, decodes the stripes it can, and decodes the pack (and so *F*) from any *m*/2 valid pieces.
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

**Numbers** (*n* = 96, *w* = 32, *t* = 65, *d* + 1 = 1, so *q* = *p*). The pack column (*m* = 4,096) is the current design; the per-file columns are the earlier design, kept for comparison.

| Coalition stake α | Stripe fails, *p* | File fails, per-file *m* = 32 | Per-file *m* = 64 | **64 MB pack, *m* = 4,096** |
| --- | --- | --- | --- | --- |
| 33% | 3.9 × 10^-12 | about 10^-186 | below 10^-300 | effectively zero |
| 50% | 3.4 × 10^-4 | 5.3 × 10^-51 | 4.7 × 10^-97 | effectively zero |
| 60% | 7.4 × 10^-2 | 1.1 × 10^-11 | 8.6 × 10^-21 | effectively zero |
| 64% | 0.26 | 9.6 × 10^-4 | 1.1 × 10^-5 | 1.1 × 10^-236 |
| 66% | 0.40 | 0.11 | 5.2 × 10^-2 | 2.1 × 10^-33 |
| 67% | 0.49 | 0.38 | 0.38 | 8.4 × 10^-2 |

A stripe fails with probability 1/2 at α ≈ 67.1%, where a coalition can black out most of the network; packs move the point at which one chosen file can be killed (below 10^-18) from 57.6% to 66.3%, almost to that line. Killing a pack needs at least 2,049 failed stripes at once. A union bound over all files multiplies the per-file figures by the number of packs.

**What G1 does not cover**

- **Churn.** Theorem 1 assumes every slot is held and served. Departures, rebuild delay, downtime, outages and nodes that store but don't serve are covered by Theorem 1′ in G1 under churn below.
- **Adaptive corruption and DoS.** A censor who corrupts, coerces or knocks offline specific holders after placement is not bounded by α. Destroying *F* then needs more than *m*/2 failed stripes of its pack, each with at most 31 honest holders answering. With packs that means making more than 2,048 stripes fail at once; at a 50% coalition it takes knocking out about a third of all honest stake, a network-wide outage. Formalizing this needs a model of corruption and DoS cost over time.
- **Targeted deletion or corruption.** Once *F*'s address is public, a holder knows which of its symbols belong to *F* and can delete or corrupt just those, with no collateral damage. Below the threshold this cannot make *F* unreadable (step 1: Merkle verification rejects corrupted symbols and any 32 valid ones decode); it is routed around (G2b), and every wrong answer it causes is provable and slashed (Theorem 4).

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

| Unit | β\_max at 10^-9 | β\_max at 10^-18 | β\_max at 10^-30 |
| --- | --- | --- | --- |
| Per-file, *m* = 32 (old) | 0.608 | 0.576 | 0.543 |
| Per-file, *m* = 64 (old) | 0.626 | 0.604 | 0.582 |
| Per-file, *m* = 128 (old) | 0.639 | 0.624 | 0.609 |
| **64 MB pack, *m* = 4,096** | **0.666** | **0.663** | **0.660** |

1. **Rebuild speed is not the binding constraint.** With 1% downtime, the longest rebuild delay that keeps a file below 10^-18 is about 120 days at α = 50% and λ = 0.5 per year (37 days if a 10% outage is also under way), 31 days even at λ = 2, and over a year for a 33% coalition. A protocol target of rebuilding within 7 days, most-degraded stripes first, leaves a wide margin.
2. **Correlated outages are.** With α = 50%, a simultaneous outage of 10% of honest stake gives about 5 × 10^-26 per file, 20% gives about 2 × 10^-10, and 30% about 4%: a temporary window in which the coalition could block a given file. At α = 33%, a 30% outage stays near 10^-33 and a 40% outage near 5 × 10^-11.
3. **Seizure is permanent, and repair cannot undo it.** If a fraction φ of all stake is destroyed at once, a stripe left with fewer than 32 honest holders of its data is lost as soon as the coalition withholds its symbols. Losing 20% of stake is about 2 × 10^-36 per file with α = 33% and 10^-11 with α = 40%; losing 30% with α = 33% is about 3 × 10^-5. Rebuilding after a 20% loss takes about 0.7 days at 1 Gbit/s of repair bandwidth per node and 7 days at 100 Mbit/s; that bounds exposure to further losses, not the initial one.
4. **Bigger minimum files are a free margin.** Raising the minimum from 32 to 64 pieces (2 MB bundles) moves β\_max from 0.576 to 0.604 at no storage cost. A 32-of-128 inner code would reach about 0.68, at 8x storage instead of 6x.

**With packs.** The items above use the old per-file code. With 64 MB packs, β can reach about 0.66: a 50% coalition plus a simultaneous outage of 30% of honest stake gives about 2.7 × 10^-79 per pack (3.2% per file before), and a 40% coalition plus permanent seizure of 20% of all stake is effectively zero (10^-11 before). Rebuild speed matters even less. Packs do not change the fact that seized data cannot be rebuilt if the coalition withholds its share; they make it take far more seizure.

**Model check.** A time-stepped simulation (500 nodes, 1,000 stripes, 3 years, hourly steps, heavy churn: λ = 4, *D* = 30 days, 1% downtime) matched the β model within about 2x at stripe failure rates around 10^-2 under rendezvous placement.

## G2: Record privacy and routing around refusals

G2 is about refusal: whether a coalition can refuse or slow the reads of one target (a file, a post, an author's profile, or one reader) while serving everything else. Holoweave has no anonymity layer of its own (decided Oct 19, 2026, to keep the system simple), so a node knows who sends each query. G2 has two parts. **G2a, record privacy**: a node never learns which record a query wants, only its domain, whatever else it knows. **G2b, routing around refusals**: whatever a node infers from who is asking and when, a refusal never stops the read below G1's threshold, and the node isn't paid for it. Targeted deletion or corruption of stored records is handled by G1 (it can't make a file unavailable) and Theorem 4 (every wrong answer it causes is provable).

### What a node sees

For each query: the sender's address (or a Tor exit, if the reader chooses Tor), the arrival time, the node and domain, and the PIR query. PIR hides the record; everything else is visible. That allows two kinds of selection:

- **By reader.** Refuse one person, one address range or one country.
- **By pattern.** Placement is public, so reading a file, profile or thread hits a known set of domains, and a node or a coalition pooling its logs can see one reader querying them together. Two linked queries are enough to identify a file: two 1 GB domains are consistent with about 3 other minimum-size files at 20 TB of user data and 0.06 at 1 PB.

Tor hides the address but not the pattern. A traffic model of a reader on Tor, with each query sent separately, found that timing alone still picks out multi-record reads: with 50% of stake and typical domains (about 0.01 queries/s per 1 GB domain), a 1 MB file read within a minute is recognized with advantage 0.62, and a 20-post profile with 0.54. One isolated post read reveals nothing beyond its domain. Details are in the project's sim/SIMULATION.md.

### G2a: Record privacy

**Game RecPriv(𝒜, *b*)**

1. 𝒜 (controlling *C*) picks a node *v* ∈ *C*, a domain of *v*, two records *r*₀, *r*₁ in it, and the whole context of one query: who sends it, when, and every other query in the system.
2. The challenger sends, in that context, a query for *r\_b* to (*v*, domain).
3. 𝒜 runs any refusal policy and outputs a guess *b*′. It wins if *b*′ = *b*.

**Theorem 2.** For any PPT coalition policy, any context and any two records *r*₀, *r*₁ in the same domain, the probability of refusing the query differs between *r*₀ and *r*₁ by at most Adv\_priv(Π).

**Proof (reduction).** Suppose a policy *P* refuses with probabilities δ₀ and δ₁, |δ₀ − δ₁| = ε. A distinguisher ℬ against Π's query privacy receives a challenge query *Q* for *r\_b*, builds the context 𝒜 chose (it does not depend on *b*), embeds *Q*, runs *P* and outputs 1 if *P* refuses *Q*. Its advantage is ε, so ε ≤ Adv\_priv(Π). ∎

So a refusal can depend on who asks, when, and what else they asked, but not on the query itself beyond its domain.

**Corollary (blast radius of query-based refusal).** A policy that ignores who is asking and refuses queries for one record with probability δ refuses queries for every record in that domain with probability at least δ − Adv\_priv(Π): at least 1 GB of other data per domain on CPU nodes, 64 GB or more on GPU servers, provided domains follow the public layout rule (a node cannot choose what shares a domain with the target). This bounds refusals decided from the query. Deletion or corruption of a known symbol needs no query at all, so the corollary does not cover it; Theorem 4 does (every resulting wrong answer is provable), and G1 bounds its effect on availability.

### G2b: Routing around refusals

There are no challenges or public refusal logs (decided Oct 19, 2026); refusals are unpunished, while wrong answers are provable (Theorem 4). A reader treats a refusal, a late answer or an answer that fails the Merkle check the same way: it doesn't pay for that query and fetches the block another way.

**Theorem 3 (refusal is never fatal).** Fix any coalition policy, including ones that select by reader or by pattern, and let a slot count as unavailable to a reader if its holder refuses that reader. Under Theorem 1′ with β counting those slots:

1. A **read of any piece** completes whenever at least *w* = 32 of its stripe's 96 holders answer correctly: a refused, deleted or corrupted piece costs about 32 queries instead of 1, sent in parallel. Readers remember refusing nodes and skip the wait next time.
2. If the piece's stripe itself has failed, the read completes whenever its pack still has *m*/2 decodable pieces, at a cost of about 2,048 queries (0.7 GB of upload) for that file.
3. The refusing node is paid nothing for refused or wrong answers.

**Argument.** Items 1 and 2 are the decoding properties of the outer code and the Clay code; whether enough pieces or symbols are served is exactly the event Theorem 1′ bounds. Item 3 holds because payment is per verified answer. No network assumption is used.

**What the two parts give together.** A node can single out a reader or a file read and refuse it. Below G1's threshold this never stops the read: it costs the reader about 32 queries per refused piece, and it costs the node the read fee. Refusals are private between node and reader and are not punished, but they achieve nothing below the threshold.

### Theorem 4: no unpunished selective deletion

Added Oct 19, 2026, when signed answers and answer fraud proofs were restored.

**Setup.** A client derives each query from a fresh random seed: *q* = Query(seed, *i*). A node returns its answer *a* with a signature σ on (domain, *H*(*q*), *a*). An **answer fraud proof** is (domain, *H*(*q*), *a*, σ, seed, *i*, *D*\[*i*\], Merkle path). It is valid if Query(seed, *i*) hashes to the signed value, *D*\[*i*\] verifies against the committed root, and Decode(seed, *a*) ≠ *D*\[*i*\]. Let δ be the PIR scheme's decoding-error probability for an honest answer to a well-formed query.

**Theorem 4.**

1. *No framing.* Against an honest node, a reader who tries *Q* seeds produces a valid answer fraud proof with probability at most *Q*·δ + ε\_sig + ε\_hash.
2. *Selective harm is provable.* Fix any node strategy and two records *r*, *r*′ in one domain. Let ρ(*r*) be the probability that a fresh query for *r* is refused (no answer, a late answer, or an unsigned one), and ω(*r*) the probability that it gets a signed answer that decodes wrongly. If readers of *r* are served badly more often than readers of *r*′ by a gap *g*, meaning (ρ(*r*) + ω(*r*)) − (ρ(*r*′) + ω(*r*′)) = *g*, then ω(*r*) ≥ *g* − Adv\_priv(Π), and every such wrong answer gives its reader a valid answer fraud proof.

**Proof.** (1) An honest node returns Answer(*D*, *q*) for the well-formed query rebuilt from the seed; it decodes correctly except with probability δ over the seed's randomness, and each seed the reader tries is a fresh sample, so *Q* tries succeed with probability at most *Q*·δ. Any other route to a valid proof forges σ or finds a hash collision. (2) By Theorem 2, |ρ(*r*) − ρ(*r*′)| ≤ Adv\_priv(Π), so ω(*r*) − ω(*r*′) ≥ *g* − Adv\_priv(Π), and ω(*r*′) ≥ 0. A signed answer that decodes wrongly to a query rebuilt from its seed is, by definition, a valid proof. ∎

**What it means.** If a node deletes or corrupts file *X*'s record, every signed answer to a query for *X* is wrong, so each of *X*'s readers can prove it. The node can't keep those answers away from *X*'s readers, because it can't tell their queries apart (Theorem 2). To avoid proofs it must refuse instead, and a refusal decided from the query has to cover every record of the domain about equally. Its options are: keep the record, refuse the whole domain (losing its read fees, while readers route around it), or be slashed the first time a reader of *X* files a proof. The statement is mathematical. How much slashing deters is economic: it is bounded by the bond.

**Limits.** Someone has to read *X* and file. Filing reveals to the node that the reader it served wanted *X*. A coalition above G1's threshold can still kill a file and be slashed afterwards. The design sets δ below 2^-60, which has to be checked against YPIR's actual parameters (open obligation).

**Limits**

- **Cost amplification.** A coalition that refuses every single-piece read multiplies honest load by (1 − α) + 32α: about 4x at 10%, 10x at 30%, 16x at 50%. It can aim this at one reader, one country or one author's readers. It cannot make anything unavailable below G1's threshold.
- **Fallback leaks interest.** The holders a reader turns to for a rebuild see the reader's address and learn which stripe, and roughly which file, the reader wanted. PIR hides which post a reader viewed only while no fallback is needed.
- **Reader privacy from nodes is limited.** Nodes learn who reads and which domains, and a coalition pooling logs can often infer which files and profiles a reader views.
- **Storage proofs.** A node proves storage with a STARK over 2,500 beacon-sampled leaves per TB each day, due within 10 minutes, so there are no auditors to recognize; faking by rebuilding sampled leaves on demand would take about 1.6 million PIR queries in those 10 minutes for a 20 TB node. Colluding operators holding 32 or more slots of a stripe can store 32 symbols and compute the rest, saving about 17% of storage at 40% of stake and 33% at 50%; this is accepted (it does not reduce availability).

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

These counts came from a greedy search over the old per-file code, so they are upper bounds on the cheapest coercion set, and the script that produced them is not yet in the project files. With 64 MB packs a censor must make more than 2,048 stripes fail at once, which needs coalition stake near two-thirds: about 663 operators of 1,000 with even stake, but only about 80 of 1,000 (or 370 of 10,000) with zipf-concentrated stake, because those operators already hold two-thirds of all stake. Stake concentration is an accepted risk.

The simulation is approximate: correlated-outage runs used one random draw per setting, and concentrated-stake runs with random coalitions are noisy. The script and full output are kept with the project files.

## Open proof obligations

- [ ] **Stake-weighted sampling without replacement.** Resolved by simulation: the design now draws slots with replacement by stake, which makes the count of corrupted slots exactly Bin(*n*, α).
- [ ] **Beacon model.** Bound ε\_beacon for the chosen threshold beacon or VDF, including bias by withholding.
- [ ] **Churn-aware G1.** Done: Theorem 1′ and its requirements are in G1 under churn. Remaining: a formal treatment of correlated outages whose timing the coalition can influence.
- [ ] **Adaptive corruption.** Define a corruption-cost model over time and bound the cost of destroying one file, including yearly reshuffles.
- [x] **A\_unlink.** Done Oct 19, 2026. The traffic model showed unlinkability fails for file and profile reads even over an anonymity layer, and Holoweave dropped the anonymity layer to stay simple. G2 no longer assumes unlinkability: record privacy (G2a) holds in any context, and routing around refusals (G2b) covers selection by reader or pattern.
- [ ] **Pack code.** Prove the pack bound with stripes shared across packs (a failed stripe hits 32 different packs, so stripe failures are independent within one pack but not across packs), and extend bad-encoding fraud proofs to the pack code.
- [ ] **Identity randomness.** Show that activation-time beacon randomness and fixed per-identity stake leave the coalition's slot count Bin(*n*, α) on already-published seeds.
- [ ] **DoS model.** Bound the cost of knocking specific holders offline, and the effect of the 3-day ejection grace window.
- [ ] **Storage-proof soundness.** Bound the chance a node passes a day's proof while missing a share of its data, and the cost of faking it by rebuilding sampled leaves on demand (the design samples 2,500 leaves per TB per day, due within 10 minutes, so faking would need about 1.6 million PIR queries in that window for a 20 TB node). Benchmark the STARK prover.
- [ ] **PIR instantiation.** Fix the scheme and parameters, and cite its query-privacy reduction to LWE with concrete security.
- [ ] **Mixing randomizers.** Moot: mixing was dropped on Oct 19.
- [ ] **Independent review.** Have a cryptographer check both games, the reductions and the numbers.
- [ ] **Answer fraud proofs.** Fix YPIR parameters with decoding error δ ≤ 2^-60 and measure what they cost; specify the STARK that rebuilds a query from its seed and decrypts the answer, and benchmark it; make Theorem 4's reduction to Theorem 2 precise for strategies that depend on earlier answers.
- [ ] **G3 and G4.** Write accountability and blind-ingest games in the same style.
