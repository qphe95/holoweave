# Security games

Current as of Oct 19, 2026. Draft definitions and paper proofs for Holoweave's core guarantees, written to be checked by an independent cryptographer:

- **G1, availability:** a probability bound that holds against any coalition behaviour (Theorems 1 and 1′).
- **G2, record privacy and routing around refusals:** a reduction to PIR query privacy (Theorem 2) and a decoding argument (Theorem 3).
- **G3, no unpunished selective deletion:** signed answers and answer fraud proofs (Theorem 4).

## Model and notation

| Symbol | Meaning | Default |
| --- | --- | --- |
| *N*, *σ\_v* | Number of nodes; stake share of node *v* (Σ *σ\_v* = 1) |  |
| *C*, α | Coalition (set of corrupted nodes) and its total stake share |  |
| *w*, *n* | Symbols needed to decode a stripe; holders per stripe | 32, 96 |
| *t* | Blocking threshold: *n* − *w* + 1 corrupted holders | 65 |
| *K*, *m* | Data pieces per pack; pieces per pack (*m* = 2*K*); any *K* rebuild it | 2,048, 4,096 |
| *H\_s* | The holders of stripe *s* |  |
| Π | The PIR scheme: Query, Answer, Decode | YPIR |

**Packs.** The batch builder codes the pieces of many files together into packs: *K* = 2,048 data pieces (64 MB) plus 2,048 parity pieces of a systematic Reed-Solomon code, so any *K* of the *m* = 4,096 pieces rebuild the pack, and data pieces are stored as-is. Each piece is one block in its own stripe, and a pack's 4,096 stripes are distinct. A chosen file is lost only if its pack is lost, so the games take the pack as the unit.

**Placement.** Each slot *j* of stripe *s* has a seed σ\_{s,j} from the beacon, drawn after the batch is final. Its holder is chosen by **stake-weighted rendezvous hashing** over the *current* node set: holder(*s*, *j*) = argmin over nodes *v* of *E\_v* / stake\_*v*, where *E\_v* = −ln *H*(σ\_{s,j}, id\_*v*, *r\_v*) is a unit exponential. Two properties follow:

1. A slot lands on a node with probability exactly proportional to its stake, and slots with different seeds are independent. A node may hold several slots of one stripe, and the number of coalition slots in a stripe is Bin(*n*, α).
2. The holder depends only on who is in the network *now*, not on its history, so the coalition's share of slots equals its share of stake at every moment.

**Identity randomness.** *r\_v* is a beacon value revealed only after identity *v*'s stake is locked, and stake is fixed per identity. Otherwise a coalition could register many identities, see how each ranks on already-published seeds and move stake into the best ones, breaking the assumption that *C* is fixed before the placement randomness it benefits from.

**Honest behaviour.** A node outside *C* stores its symbols and answers queries correctly. Daily storage proofs keep this assumption true; they are outside the games.

**Adversary.** *C* is chosen before the placement randomness is revealed (static corruption). After that, *C* sees everything public (addresses, placements, Merkle roots, every message sent to its members) and may make its members refuse, delay, delete or corrupt anything. Adaptive corruption after placement is a separate limit (see G1).

## G1: Availability

**Game Avail(𝒜, α, F)**

1. 𝒜 chooses a coalition *C* with stake share at most α.
2. An honest client uploads *F*; it is coded into a pack, and the beacon samples placement for every stripe.
3. 𝒜 learns all public data and controls every node in *C* arbitrarily.
4. An honest reader contacts every holder of every stripe of the pack, verifies each symbol against its Merkle root, decodes the stripes it can, and decodes the pack (and so *F*) from any *K* valid pieces.
5. 𝒜 wins if the reader fails to output *F*.

**Theorem 1.** Let *p* = Pr\[Bin(*n*, α) ≥ *t*\]. For every adversary, even computationally unbounded in its strategy,

```latex
\Pr[\mathcal{A}\ \text{wins}] \;\le\; \Pr\!\left[\mathrm{Bin}(m, p) \ge K + 1\right] \;+\; \varepsilon_{\mathrm{hash}} + \varepsilon_{\mathrm{beacon}}
```

where ε\_hash bounds Merkle-path forgery (collision resistance) and ε\_beacon bounds the beacon's deviation from a random oracle.

**Proof.**

1. *A stripe fails only if* |*H\_s* ∩ *C*| ≥ *t*. Otherwise at least *n* − *t* + 1 = *w* holders are honest and return valid symbols. Corrupted symbols are rejected by Merkle verification (except with probability ε\_hash), and any *w* valid symbols decode the stripe (MDS property).
2. *Each stripe fails with probability at most p.* Slots are independent stake-weighted draws, so |*H\_s* ∩ *C*| \~ Bin(*n*, α). *C* is fixed before the beacon, so it can't depend on the draw.
3. *Stripe failures are independent within a pack.* A pack's stripes are distinct and have independent placements (random-oracle beacon), so each of its pieces fails independently with probability at most *p*.
4. *The pack fails only if at least K + 1 pieces fail*, because the pack code decodes from any *K*. The number of failed pieces is dominated by Bin(*m*, *p*). ∎

**Numbers** (*n* = 96, *w* = 32, *t* = 65, *K* = 2,048):

| Coalition stake α | Stripe fails, *p* | Chosen file lost |
| --- | --- | --- |
| 33% | 3.9 × 10^-12 | below 10^-300 |
| 50% | 3.4 × 10^-4 | below 10^-300 |
| 60% | 7.4 × 10^-2 | below 10^-300 |
| 64% | 0.26 | 1.1 × 10^-236 |
| 66% | 0.40 | 2.1 × 10^-33 |
| 67% | 0.49 | 8.4 × 10^-2 |

One chosen file stays below 10^-18 up to α = 66.3%. A stripe fails with probability 1/2 at α ≈ 67.1%, where a coalition can black out most of the network, so the threshold for one chosen file sits almost at that line. Killing a pack needs at least 2,049 failed stripes at once. A union bound over all files multiplies the per-file figure by the number of packs. (For comparison, coding each 1 MB file on its own, with 32 pieces, gives a threshold of 57.6%.)

**What G1 does not cover**

- **Churn.** Theorem 1 assumes every slot is held and served. Departures, rebuild delay, downtime, outages and nodes that store but don't serve are covered by Theorem 1′ below.
- **Adaptive corruption and DoS.** A censor who corrupts, coerces or knocks offline specific holders after placement isn't bounded by α. It must still make more than 2,048 stripes of the pack fail at once; at a 50% coalition that means knocking out about a third of all honest stake, a network-wide outage. A formal model of corruption and DoS cost over time is an open obligation.
- **Targeted deletion or corruption.** Once *F*'s address is public, a holder knows which of its symbols belong to *F* and can delete or corrupt just those. Below the threshold this can't make *F* unreadable (step 1); readers route around it (Theorem 3), and every wrong answer it causes is provable (Theorem 4).

## G1 under churn

**Theorem 1′.** Fix any history *ℋ* of joins, exits, stake changes, downtime and outages up to time *τ*, chosen without knowledge of the slot seeds. Given *ℋ*, slots are independent (each depends only on its own seed), and each is in one of three states: coalition-held with probability α\_τ (the coalition's stake share at *τ*), honest but unavailable (rebuild pending, holder offline or not serving), or honest and available. Let β = Pr\[slot is not honest-available | *ℋ*\]. Then Theorem 1 holds at time *τ* with α replaced by β:

```latex
\Pr[\mathcal{A}\text{ blocks } F \text{ at } \tau \mid \mathcal{H}] \le \Pr\!\left[\mathrm{Bin}(m, p_\beta) \ge K + 1\right] + \varepsilon,\quad p_\beta = \Pr[\mathrm{Bin}(n, 1-\beta) < w]
```

*Proof sketch.* Given *ℋ*, the state of slot (*s*, *j*) is a fixed function of σ\_{s,j}, and seeds are independent random-oracle outputs, so slot states are independent with the stated probabilities. A stripe is blockable only if fewer than *w* slots are honest-available, which has probability *p\_β*; the rest is the proof of Theorem 1. ∎

This relies on placement being memoryless: rendezvous placement keeps the coalition's slot share at its stake share whatever the history of joins and exits, which simulation confirmed (`sim/churn_sim.py`).

**What β is made of.** With abrupt honest exits at rate λ per year, rebuild delay *D*, transient downtime *u*₀ and a correlated outage of a fraction φ of honest stake:

```latex
\beta = \alpha + (1-\alpha)\Bigl[1 - \bigl(1 - \tfrac{\lambda D}{1 + \lambda D}\bigr)(1 - u_0)(1 - \varphi)\Bigr]
```

**Requirements.** One file stays below a target failure probability while β ≤ β\_max: 0.666 at 10^-9, **0.663 at 10^-18** and 0.660 at 10^-30. The bound is a cliff: below about 0.66 failure is negligible, above 0.671 it is near certain. Figures below are from `sim/pack_churn.py`.

1. **Rebuild speed is not the binding constraint.** With 1% downtime, the longest rebuild delay that keeps a file below 10^-18:

   | α | λ = 0.1/yr | λ = 0.5/yr | λ = 2/yr | λ = 0.5/yr, plus a 10% outage |
   | --- | --- | --- | --- | --- |
   | 33% | 3,535 days | 707 days | 177 days | 563 days |
   | 40% | 2,785 days | 557 days | 139 days | 428 days |
   | 50% | 1,712 days | 342 days | 86 days | 235 days |

   The protocol's 7-day rebuild target leaves a wide margin.

2. **Temporary outages.** With λ = 0.5/yr, 1-day rebuilds and 1% downtime: a 50% coalition plus an outage of 30% of honest stake gives about 3 × 10^-75; plus 40%, the file can be blocked while the outage lasts. A 40% coalition plus a 40% outage gives about 2 × 10^-180. Below these, failure is under 10^-300.
3. **Permanent seizure.** If a fraction φ of all stake is destroyed at once and the coalition withholds its symbols, β = α + φ and repair can't undo the loss. A file is safe while α + φ stays below about 0.66 and lost once it passes about 0.67: for example a 33% coalition survives losing 30% of stake but not 40%, and a 50% coalition survives 10% but not 20%. After a 20% loss, rebuilding takes about 0.7 days at 1 Gbit/s of repair bandwidth per node and 7 days at 100 Mbit/s.

**Model check.** A time-stepped simulation (500 nodes, 1,000 stripes, 3 years, hourly steps, heavy churn: λ = 4/yr, *D* = 30 days, 1% downtime) matched the β model at stripe failure rates around 10^-2 under rendezvous placement (period averages within about 2x; single snapshots differ by up to about 9x) (`sim/churn_sim.py`).

## G2: Record privacy and routing around refusals

G2 asks whether a coalition can refuse or slow the reads of one target (a file, a post, an author's profile, or one reader) while serving everything else. Holoweave has no anonymity layer, so a node knows who sends each query. **G2a, record privacy:** a node never learns which record a query wants, only its domain, whatever else it knows. **G2b, routing around refusals:** whatever a node infers from who is asking and when, a refusal never stops the read below G1's threshold, and the node isn't paid for it.

### What a node sees

For each query: the sender's address (or a Tor exit), the arrival time, the node and domain, and the PIR query. PIR hides the record; everything else is visible. That allows two kinds of selection:

- **By reader.** Refuse one person, one address range or one country.
- **By pattern.** Placement is public, so reading a file, profile or thread hits a known set of domains, and a coalition pooling its logs can see one reader querying them together. Two linked queries are enough to identify a file: two 1 GB domains are consistent with about 3 other minimum-size files at 20 TB of user data, and 0.06 at 1 PB.

Tor hides the address but not the pattern. A traffic model of a reader on Tor sending each query separately found that timing alone still picks out multi-record reads: with 50% of stake and typical domains (about 0.01 queries/s per 1 GB domain), a 1 MB file read within a minute is recognized with advantage 0.62, and a 20-post profile with 0.54. One isolated post read reveals nothing beyond its domain (`sim/traffic_model.py`).

### G2a: Record privacy

**Game RecPriv(𝒜, *b*)**

1. 𝒜 (controlling *C*) picks a node *v* ∈ *C*, a domain of *v*, two records *r*₀, *r*₁ in it, and the whole context of one query: who sends it, when, and every other query in the system.
2. The challenger sends, in that context, a query for *r\_b* to (*v*, domain).
3. 𝒜 runs any refusal policy and outputs a guess *b*′. It wins if *b*′ = *b*.

**Theorem 2.** For any PPT coalition policy, any context and any two records *r*₀, *r*₁ in the same domain, the probability of refusing the query differs between *r*₀ and *r*₁ by at most Adv\_priv(Π).

**Proof (reduction).** Suppose a policy *P* refuses with probabilities δ₀ and δ₁, |δ₀ − δ₁| = ε. A distinguisher ℬ against Π's query privacy receives a challenge query *Q* for *r\_b*, builds the context 𝒜 chose (it doesn't depend on *b*), embeds *Q*, runs *P* and outputs 1 if *P* refuses *Q*. Its advantage is ε, so ε ≤ Adv\_priv(Π). ∎

So a refusal can depend on who asks, when, and what else they asked, but not on the query itself beyond its domain.

**Corollary (blast radius of query-based refusal).** A policy that ignores who is asking and refuses queries for one record with probability δ refuses queries for every record in that domain with probability at least δ − Adv\_priv(Π): at least 1 GB of other data per domain on CPU nodes, 64 GB or more on GPU servers. This needs domains to follow the public layout rule, so a node can't choose what shares a domain with the target. Deletion or corruption of a known symbol needs no query at all; Theorem 4 covers it.

### G2b: Routing around refusals

A reader treats a refusal, a late answer or an answer that fails the Merkle check the same way: it doesn't pay for that query and fetches the block another way. There are no challenges and no refusal logs.

**Theorem 3 (refusal is never fatal).** Fix any coalition policy, including ones that select by reader or by pattern, and let a slot count as unavailable to a reader if its holder refuses that reader. Under Theorem 1′ with β counting those slots:

1. A **read of any piece** completes whenever at least *w* = 32 of its stripe's 96 holders answer correctly: a refused, deleted or corrupted piece costs about 32 queries instead of 1, sent in parallel. Readers remember refusing nodes and skip the wait next time.
2. If the piece's stripe itself has failed, the read completes whenever its pack still has *K* decodable pieces, at a cost of about 2,048 queries.
3. The refusing node is paid nothing for refused or wrong answers.

**Argument.** Items 1 and 2 are the decoding properties of the Clay code and the pack code; whether enough symbols or pieces are served is exactly the event Theorem 1′ bounds. Item 3 holds because payment is per verified answer. No network assumption is used.

**Limits**

- **Cost amplification.** A coalition that refuses every single-piece read multiplies honest load by (1 − α) + 32α: about 4x at 10%, 10x at 30%, 16x at 50%. It can aim this at one reader, one country or one author's readers. It can't make anything unavailable below G1's threshold.
- **Fallback leaks interest.** The holders a reader turns to for a rebuild see the reader's address and learn which stripe, and roughly which file, the reader wanted. PIR hides which post a reader viewed only while no fallback is needed.
- **Reader privacy from nodes is limited.** Nodes learn who reads and which domains, and a coalition pooling logs can often infer which files and profiles a reader views.

## G3: No unpunished selective deletion

**Setup.** A client derives each query from a fresh random seed: *q* = Query(seed, *i*). A node returns its answer *a* with a signature σ on (domain, *H*(*q*), *a*). An **answer fraud proof** is (domain, *H*(*q*), *a*, σ, seed, *i*, *D*\[*i*\], Merkle path). It is valid if Query(seed, *i*) hashes to the signed value, *D*\[*i*\] verifies against the committed root, and Decode(seed, *a*) ≠ *D*\[*i*\]. Let δ be the PIR scheme's decoding-error probability for an honest answer to a well-formed query.

**Theorem 4.**

1. *No framing.* Against an honest node, a reader who tries *Q* seeds produces a valid answer fraud proof with probability at most *Q*·δ + ε\_sig + ε\_hash.
2. *Selective harm is provable.* Fix any node strategy and two records *r*, *r*′ in one domain. Let ρ(*r*) be the probability that a fresh query for *r* is refused (no answer, a late answer or an unsigned one), and ω(*r*) the probability that it gets a signed answer that decodes wrongly. If readers of *r* are served badly more often than readers of *r*′ by a gap *g*, meaning (ρ(*r*) + ω(*r*)) − (ρ(*r*′) + ω(*r*′)) = *g*, then ω(*r*) ≥ *g* − Adv\_priv(Π), and every such wrong answer gives its reader a valid answer fraud proof.

**Proof.** (1) An honest node returns Answer(*D*, *q*) for the well-formed query rebuilt from the seed; it decodes correctly except with probability δ over the seed's randomness, and each seed tried is a fresh sample, so *Q* tries succeed with probability at most *Q*·δ. Any other route to a valid proof forges σ or finds a hash collision. (2) By Theorem 2, |ρ(*r*) − ρ(*r*′)| ≤ Adv\_priv(Π), so ω(*r*) − ω(*r*′) ≥ *g* − Adv\_priv(Π), and ω(*r*′) ≥ 0. A signed answer that decodes wrongly to a query rebuilt from its seed is, by definition, a valid proof. ∎

**What it means.** If a node deletes or corrupts file *X*'s record, every signed answer to a query for *X* is wrong, so each of *X*'s readers can prove it. The node can't keep those answers away from *X*'s readers, because it can't tell their queries apart (Theorem 2). To avoid proofs it must refuse instead, and a refusal decided from the query has to cover every record of the domain about equally. Its options are: keep the record, refuse the whole domain (losing its read fees while readers route around it), or be slashed the first time a reader of *X* files a proof. The statement is mathematical; how much slashing deters is economic, bounded by the bond.

**Limits.** Someone has to read *X* and file a proof. Filing reveals to the node that the reader it served wanted *X*. A coalition above G1's threshold can still kill a file and be slashed afterwards. The design sets δ below 2^-60, which has to be checked against YPIR's actual parameters.

**Why not verifiable PIR.** Verifiable PIR (VeriSimplePIR; Rathee, Lee and Popa 2025) binds every answer to one committed database, but each reader must first stream a hint of about 100 MB per 1 GB domain. Readers touch a new domain for almost every post, so this would cost about 250x a read. Signed answers with fraud proofs give the property that matters, at the cost of one signature per answer.

## Simulation checks

- **Placement matches the model.** With slots drawn in proportion to stake, the coalition's slot count per stripe is exactly Bin(96, α) by construction. A Monte Carlo under even stake (run with distinct-holder draws, which behave the same as stake-proportional draws when stake is even) of 20,000 stripes at 10,000 nodes matched the binomial stripe-failure rate (for example 7.5 × 10^-3 simulated against 7.6 × 10^-3 at 55% of stake) (`sim/placement_sim.py`).
- **Churn.** Rendezvous placement kept a 40% coalition at 40.0% to 40.4% of slots over three simulated years of heavy churn (`sim/churn_sim.py`).
- **Coercing operators.** To kill one file a censor must control stake near two-thirds: about 663 of 1,000 operators with even stake, but only about 80 of 1,000 (or 370 of 10,000) with zipf-concentrated stake, because those operators already hold two-thirds of all stake. These counts are heuristic; the script that searched for them is not in the project. Stake concentration is an accepted risk.

## Open proof obligations

- [ ] **Pack code.** Prove the pack bound with stripes shared across packs (a failed stripe hits 32 different packs, so failures are independent within one pack but not across packs), and extend bad-encoding fraud proofs to the pack code.
- [ ] **Identity randomness.** Show that activation-time beacon randomness and fixed per-identity stake leave the coalition's slot count Bin(*n*, α) on already-published seeds.
- [ ] **Beacon model.** Bound ε\_beacon for the chosen threshold beacon or VDF, including bias by withholding.
- [ ] **Adaptive corruption and DoS.** Bound the cost of corrupting or knocking offline specific holders over time, including yearly reshuffles and the 3-day ejection grace window.
- [ ] **Correlated outages.** Treat outages whose timing the coalition can influence.
- [ ] **Answer fraud proofs.** Fix YPIR parameters with δ ≤ 2^-60 and measure their cost; specify and benchmark the STARK that rebuilds a query from its seed and decrypts the answer; make Theorem 4 precise for strategies that depend on earlier answers.
- [ ] **Storage-proof soundness.** Bound the chance a node passes a day's proof while missing part of its data, and the cost of faking it within 10 minutes. Benchmark the STARK prover.
- [ ] **PIR instantiation.** Fix the scheme and parameters, and cite its query-privacy reduction to LWE with concrete security.
- [ ] **G4.** Write the blind-ingest and inclusion game in the same style.
- [ ] **Independent review.** Have a cryptographer check the games, reductions and numbers.
