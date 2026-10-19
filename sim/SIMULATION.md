# Placement simulation and PIR benchmark

Oct 18, 2026

This folder holds a Monte Carlo check of G1 (availability under per-stripe random placement) and a SimplePIR CPU benchmark. Files:

| File | What it is |
| --- | --- |
| `placement_sim.py` | Monte Carlo simulation of per-stripe placement (numpy) |
| `results.txt` | Full output of one run (seed 7, 20,000 stripes per setting) |
| `benchmarks/bench_*.txt` | Raw SimplePIR benchmark logs |
| `churn_sim.py` | Churn-aware G1: placement under churn (Monte Carlo) and the β requirements (analytic) |
| `churn_results.txt` | Full output of one churn run |

Run with `python3 placement_sim.py` or `python3 -u churn_sim.py` (needs numpy). Each takes a few minutes.

## Update after design changes (Oct 19, 2026)

Two design decisions change some numbers below. **Mixing was dropped** (each piece is now one block in one stripe, so `d1 = 1` in `churn_sim.py`; it was 3), and **PIR domains are 1 GB minimum** (was 8 GB). Every read on every device is PIR, with no gateways. Sections further down that quote d+1 = 3 or 8 GB are kept as a record; the current numbers are:

| Quantity | Old (mixing, 8 GB) | Current (no mixing, 1 GB) |
| --- | --- | --- |
| β_max at 10⁻¹⁸, m = 32 / 64 / 128 | 0.554 / 0.578 / 0.594 | 0.576 / 0.604 / 0.624 |
| α = 50%, λ = 0.5/yr, max rebuild delay | ~79 days | ~122 days (37 days during a 10% outage) |
| α = 50%, λ = 2/yr, max rebuild delay | ~20 days | ~31 days |
| CPU per 32 KB record read | ~4.7 core-s | ~0.46 core-s |
| Upload / download per record | ~9 MB / ~370 KB | ~0.37 MB / ~120 KB |
| Cores for 5 billion views/day | ~270,000 | ~26,000 (about $1.30 per million views) |
| Blast radius of refusing one 1 MB file | ~8 TB | ~1 TB |

Dropping mixing makes G1 stronger: a piece is lost only if its one stripe fails, not any of three. The threshold where one file becomes killable moves to about 57% of stake (60% with 2 MB files).

Adaptive coercion, rerun under the current rules (operators a censor must coerce to destroy one file):

| Network | m = 32 | m = 64 |
| --- | --- | --- |
| 1,000 nodes, even stake | ~455 | ~515 |
| 10,000 nodes, even stake | ~1,640 | ~2,600 |
| 1,000 nodes, zipf 1.0 (top 10 hold 39%) | ~82 | ~85 |
| 10,000 nodes, zipf 1.0 (top 10 hold 30%) | ~265 | ~305 |

Concentrated stake is the weak point: on a 1,000-node network with zipf-distributed stake, about 82 large operators are enough.

## Churn-aware G1 (Oct 19, 2026)

Summary: under churn, availability depends on one number, β = the share of a stripe's slots that are **not** held by an honest, online, fully rebuilt holder. One file stays below 10⁻¹⁸ failure while β ≤ 0.576 (*m* = 32), 0.604 (*m* = 64) or 0.624 (*m* = 128) without mixing (0.554 / 0.578 / 0.594 with the old 3-way mixing). The run also found a critical flaw in the placement rule and validated the fix.

### Finding 1: the repair ratchet (flaw, now fixed)

The earlier rule gave every freed slot (after an exit, failed audit or reshuffle) a fresh holder drawn by stake. Honest nodes leave; a censor never has to. The censor keeps every slot it wins and new honest nodes never win slots back, so its slot share x settles at

x* = α(λ + r) / (λα + r)

where λ is the honest exit rate per node per year and r the reshuffle rate. Steady-state slot share (rows α, columns λ = 0.1 / 0.25 / 0.5 / 1 per year, each with r = 1/3, 1, 4 per year):

| α | λ = 0.1 | λ = 0.25 | λ = 0.5 | λ = 1 |
| --- | --- | --- | --- | --- |
| 0.20 | 0.25 / 0.22 / 0.20 | 0.30 / 0.24 / 0.21 | 0.38 / 0.27 / 0.22 | 0.50 / 0.33 / 0.24 |
| 0.33 | 0.39 / 0.35 / 0.34 | 0.46 / 0.38 / 0.34 | 0.55 / 0.42 / 0.36 | 0.66 / 0.50 / 0.38 |
| 0.40 | 0.46 / 0.42 / 0.41 | 0.54 / 0.45 / 0.41 | 0.62 / 0.50 / 0.43 | 0.73 / 0.57 / 0.45 |

**Fix:** stake-weighted rendezvous hashing. Each slot has a beacon seed; its holder is argmin over current nodes of Exp(seed, id)/stake. The holder depends only on the current node set, so joiners take slots in proportion to stake and the censor's slot share equals its stake share at all times.

Monte Carlo (500 nodes, 1,000 stripes, α = 0.4, heavy churn: λ = 4/yr abrupt exits, 30-day rebuild, 1% downtime, hourly steps for 3 years):

| Year | Fresh-draw rule: censor slot share | Stripe fail | Rendezvous: censor slot share | Stripe fail (sim) | Stripe fail (β model) |
| --- | --- | --- | --- | --- | --- |
| 0.5 | 0.706 | 0.50 | 0.403 | 3.5 × 10⁻² | 1.9 × 10⁻² |
| 1.0 | 0.832 | 1.0 | 0.400 | 2.3 × 10⁻² | 2.6 × 10⁻³ |
| 2.0 | 0.881 | 1.0 | 0.404 | 3.5 × 10⁻² | 4.6 × 10⁻² |
| 3.0 | 0.897 (predicted 0.897) | 1.0 | 0.400 | 2.5 × 10⁻² | 3.8 × 10⁻² |

The β model column uses the end-of-period snapshot of honest unavailability, which fluctuates; period averages match within about 2×.

### Finding 2: Theorem 1′ and what β is made of

Given any history of joins, exits, downtime and outages chosen without knowing slot seeds, slots are independent and Theorem 1 holds with α replaced by

β = α + (1 − α)·[1 − (1 − λD/(1 + λD))·(1 − u₀)·(1 − φ)]

(λ abrupt honest exits per year, D rebuild delay, u₀ transient downtime, φ correlated outage share of honest stake).

| Minimum pieces *m* | β_max at 10⁻⁹ | β_max at 10⁻¹⁸ | β_max at 10⁻³⁰ |
| --- | --- | --- | --- |
| 32 (1 MB) | 0.581 | 0.554 | 0.525 |
| 64 (2 MB) | 0.596 | 0.578 | 0.559 |
| 128 (4 MB) | 0.607 | 0.594 | 0.582 |

For comparison, a 32-of-112 inner code gives 0.612 and 32-of-128 gives 0.657 at 10⁻¹⁸ (*m* = 32), at 7× and 8× total storage.

### Finding 3: rebuild speed is not the binding constraint

Longest rebuild delay keeping one file below 10⁻¹⁸ (1% downtime):

| α | λ = 0.1/yr | λ = 0.5/yr | λ = 2/yr | λ = 0.5/yr, plus a 10% outage |
| --- | --- | --- | --- | --- |
| 33% | 1,773 days | 355 days | 89 days | 246 days |
| 40% | 1,207 days | 241 days | 60 days | 144 days |
| 50% | 397 days | 79 days | 20 days | 0 (already over budget) |

A 7-day rebuild target, most-degraded stripes first, leaves wide margin.

### Finding 4: correlated outages and seizures are the real risk

File failure during an outage of φ of honest stake (λ = 0.5/yr, D = 1 day, 1% downtime). This is a temporary window: offline nodes keep their data.

| α | φ = 5% | 10% | 20% | 30% | 40% |
| --- | --- | --- | --- | --- | --- |
| 0% | ≈0 | ≈0 | ≈0 | 8 × 10⁻²⁰⁴ | 2 × 10⁻¹⁰⁴ |
| 20% | ≈0 | 2 × 10⁻²²⁹ | 3 × 10⁻¹³⁹ | 5 × 10⁻⁷⁵ | 2 × 10⁻³⁰ |
| 33% | 6 × 10⁻¹³⁶ | 8 × 10⁻¹⁰⁷ | 8 × 10⁻⁶⁰ | 1 × 10⁻²⁵ | 2 × 10⁻⁴ |
| 40% | 6 × 10⁻⁸² | 3 × 10⁻⁶² | 2 × 10⁻³⁰ | 1 × 10⁻⁸ | 0.92 |
| 50% | 3 × 10⁻²⁸ | 4 × 10⁻¹⁸ | 4 × 10⁻⁴ | ≈1 | ≈1 |

Permanent loss when φ of **all** stake is seized at once and the coalition withholds its symbols. Repair speed cannot undo this:

| α | lose 10% | 20% | 30% | 40% |
| --- | --- | --- | --- | --- |
| 0% | ≈0 | ≈0 | 8 × 10⁻²¹⁴ | 6 × 10⁻¹¹⁰ |
| 20% | 8 × 10⁻²¹⁴ | 6 × 10⁻¹¹⁰ | 7 × 10⁻⁴³ | 5 × 10⁻⁵ |
| 33% | 1 × 10⁻⁸⁶ | 2 × 10⁻²⁸ | 0.36 | ≈1 |
| 40% | 7 × 10⁻⁴³ | 5 × 10⁻⁵ | ≈1 | ≈1 |

Rebuild time after losing 10 / 20 / 30 / 40% of stake (20 TB per node, Clay repair 1.5×): 3.1 / 6.9 / 11.9 / 18.5 days at 100 Mbit/s of repair bandwidth per node; 0.3 / 0.7 / 1.2 / 1.9 days at 1 Gbit/s.

### Design changes made

- Placement is stake-weighted rendezvous hashing with beacon-assigned node identities (no grinding).
- Freed slots pass to the next-ranked current node; reshuffles re-seed a third of slots per year; joiners take over slots they now rank first on.
- Rebuild target: 7 days, most-degraded stripes first.
- Open decision: raise the minimum file to 64 pieces (2 MB bundles) for β_max 0.578 at no storage cost.
- Implementation note: argmin over all nodes per slot is O(N); production needs a sub-linear equivalent (hierarchical rendezvous hashing, or a stake-weighted hash ring with many virtual nodes), checked to keep exact stake proportionality and history independence.

## What the simulation models

- **Stripes.** Each stripe has *n* = 96 holders; any *w* = 32 honest, present holders can rebuild it. A stripe fails if fewer than 32 honest holders are present, i.e. the coalition holds at least 65 slots (or fewer, if honest nodes are offline).
- **Files.** A piece needs all *d* + 1 = 3 of its stored blocks, so it fails with probability *q* = 1 − (1 − *p*)³. A file of *m* = 32 pieces fails if at least *m*/2 + 1 = 17 pieces fail: `binom_tail(32, q, 17)`.
- **Networks.** *N* = 1,000 and 10,000 nodes. Stake is `uniform`, `zipf0.8` or `zipf1.0` (the top 10 operators hold 0–1%, 13–23% and 30–39% of stake respectively).
- **Coalitions.** `random` (random nodes until stake share α is reached) or `top` (the largest operators first), for α in {33%, 50%, 55%, 60%, 65%}.
- **Outages.** 5%, 10% or 20% of honest nodes offline at once, together with a 50% random coalition.
- **Adaptive coercion.** A greedy censor coerces the operators holding the most slots of one specific file until more than *m*/2 pieces die; the count is the number of operators it needed.

**Note on the sampling rule.** The script samples 96 *distinct* holders per stripe (`replace=False`). That is the rule the run tested and found broken under concentrated stake (finding 2 below). The design now draws slots **with replacement in proportion to stake**, which makes the coalition's slot count exactly Bin(96, α); under that rule the binomial columns below are exact, not approximations. Changing `replace=False` to `replace=True` in `sample_stripes` reproduces the fixed design.

## Findings

### 1. With even stake, G1's numbers hold

Simulated stripe failure tracks the binomial model, slightly below it.

| Coalition stake | Stripe fails, simulated (10,000 nodes) | Binomial model | File fails, *m* = 32 |
| --- | --- | --- | --- |
| 33% | 0 in 20,000 | 3.9 × 10⁻¹² | below 10⁻⁵⁶ |
| 50% | 2.0 × 10⁻⁴ | 3.4 × 10⁻⁴ | about 10⁻⁴⁶ |
| 55% | 7.5 × 10⁻³ | 7.6 × 10⁻³ | about 4 × 10⁻²⁰ |
| 60% | 7.4 × 10⁻² | 7.4 × 10⁻² | about 5 × 10⁻⁵ |
| 65% | 0.32 | 0.33 | about 0.98 |

Coalitions of the largest operators behave the same as random ones under even stake. Results at 1,000 nodes match.

### 2. Drawing distinct holders breaks the model under concentrated stake

With distinct holders, a node holds at most one slot per stripe, so a big operator's slot share falls below its stake share and small nodes' shares rise. When the coalition is many small nodes and honest stake sits with a few big operators, the coalition gets far more slots than its stake:

| Setting | Coalition | Stripe fails, simulated | Binomial model |
| --- | --- | --- | --- |
| 1,000 nodes, zipf1.0 (top 10 hold 39%) | 60% random | 0.80 | 0.08 |
| 1,000 nodes, zipf0.8 (top 10 hold 23%) | 65% random | 0.91 | 0.36 |
| 10,000 nodes, zipf1.0 (top 10 hold 30%) | 60% random | 0.88 | 0.07 |

The reverse also shows up: a coalition of the *biggest* operators gets fewer slots than its stake (e.g. 0 stripe failures at 60% top-coalition stake). A censor can exploit the first effect by splitting into many small identities. **Fix, now in the design:** draw slots with replacement by stake, so slot share equals stake share for any distribution.

### 3. Correlated outages matter only when large

50% random coalition plus honest nodes offline, even stake:

| Honest nodes offline | 1,000 nodes: file fails | 10,000 nodes: file fails |
| --- | --- | --- |
| 5% | about 10⁻³⁰ | about 5 × 10⁻³¹ |
| 10% | about 3 × 10⁻²⁷ | about 10⁻¹⁹ |
| 20% | about 10⁻³ | about 10⁻⁴ |

Rule of thumb: the coalition's share plus the share of honest nodes offline should stay below about 55%. This is why a churn-aware G1 with a repair-delay model is the next proof obligation.

### 4. Adaptive coercion takes hundreds to thousands of operators

Operators a censor must coerce after placement to destroy one specific file (median of 8 trials):

| Network | Even stake | zipf0.8 | zipf1.0 |
| --- | --- | --- | --- |
| 1,000 nodes | about 510 | about 275 | about 207 |
| 10,000 nodes | about 2,700 | about 1,200 | about 600 |

Concentrated stake lowers the count because large operators appear in many of a file's stripes. Yearly reshuffles bound how long such leverage lasts.

### Caveats

Correlated-outage runs used one random draw of offline nodes per setting, and concentrated-stake runs with random coalitions are noisy. Probabilities below about 5 × 10⁻⁵ per stripe are extrapolated through the binomial file formula, not observed.

## SimplePIR benchmark

Reference implementation ([ahenzinger/simplepir](https://github.com/ahenzinger/simplepir)), run with `LOG_N=… D=… go test -bench SimplePirSingle -timeout 0 -run='^$'` on a 2-core cloud VM (Intel Xeon 2.1 GHz, AVX-512). The server answer is single-threaded.

| Domain | Record size | Scan rate per core | Server time per query | Upload | Download | One-time client hint |
| --- | --- | --- | --- | --- | --- | --- |
| 128 MB | 1 bit | 9.5 GB/s | about 14 ms | 42 KB | 42 KB | 43 MB |
| 512 MB | 1 bit | 10.1 GB/s | about 50 ms | 85 KB | 85 KB | 87 MB |
| 512 MB | 32 KB | 9.7 GB/s | about 53 ms | 64 KB | 105 KB | 108 MB |

The 1 GB run was killed for running out of the VM's 7 GB of RAM.

- **Throughput estimate holds:** about 10 GB/s per core, so a 32-core node is likely memory-bandwidth bound at roughly 200–300 GB/s.
- **SimplePIR's hint rules it out:** about 100 MB per node and domain, and a read touches dozens of holders.

## YPIR benchmark

Oct 19, 2026. Reference implementation ([menonsamir/ypir](https://github.com/menonsamir/ypir)), YPIR+SP mode (`-i`), built with `target-cpu=native` on a Linux VM on an AMD Ryzen 5 7600X (AVX-512), 2 cores and 3.9 GB RAM. The server answer is single-threaded. Raw JSON and logs are in `benchmarks/ypir/`.

YPIR+SP retrieves items of 28,672 bits (3.5 KB) per *instance*; larger records are served as several instances side by side (a 32 KB record is 10 instances). The query vector is over rows and the same for every instance; each instance adds one packed response.

**Measured, one 3.5 KB item per query:**

| Domain | Rows | Server time | of which: scan | of which: ring packing | Scan rate | Upload | Download | Offline prep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 56 MB | 16,384 | 37 ms | 6 ms | 31 ms | about 9 GB/s | 588 KB | 12 KB | 1.1 s |
| 112 MB | 32,768 | 43 ms | 10 ms | 32 ms | about 11 GB/s | 702 KB | 12 KB | 1.4 s |
| 128 MB | 37,449 | 53 ms | 20 ms | 30 ms | about 6.7 GB/s | 932 KB | 12 KB | 2.0 s |
| 512 MB | 149,796 | 116 ms | 84 ms | 30 ms | about 6.4 GB/s | 2.3 MB | 12 KB | 6.1 s |

Upload includes 473 KB of public parameters (packing keys) that a client can send once per server and reuse. There is **no client hint** (SimplePIR needed about 100 MB per node and domain).

**Derived, one 32 KB record (10 instances):**

| Domain | Server time, 1 core | Upload (query + params) | Download |
| --- | --- | --- | --- |
| 512 MB (16,384 rows × 10) | about 60 ms scan + 310 ms packing ≈ 370 ms | about 115 KB + 473 KB | about 120 KB |
| 1.1 GB (32,768 rows × 10) | about 100 ms scan + 320 ms packing ≈ 420 ms | about 230 KB + 473 KB | about 120 KB |

Running YPIR+SP directly with 262,144-bit items ran out of memory on this VM at every size tried (64 MB to 512 MB, about 3.8 GB peak), so the 32 KB rows are extrapolated from per-instance runs and should be confirmed on a machine with more RAM. A 1 GB domain in one instance also does not fit in 3.9 GB (512 MB peaked at 1.8 GB).

**Batching (Oct 19, 2026).** YPIR+SP rejects more than one client per pass. Standard YPIR (1-bit items) supports batches of 1, 2, 4 or 8 clients:

| Domain | Clients | Server time | Scan (first + second pass) | Ring packing | Per client |
| --- | --- | --- | --- | --- | --- |
| 256 MB | 1 | 54 ms | 15 ms | 35 ms | 54 ms |
| 256 MB | 4 | 207 ms | 54 ms | 153 ms | 52 ms |
| 256 MB | 8 | 428 ms | 118 ms | 292 ms | 54 ms |
| 512 MB | 1 | 68 ms | 30 ms | 36 ms | 68 ms |
| 512 MB | 8 | 489 ms | 177 ms | 278 ms | 61 ms |

Batching shares the memory pass (scan per client drops about 1.4x) but packing, about 35 ms per client, does not batch at all. Net gain: about 10%. On many-core nodes the shared scan can still matter once memory bandwidth, not compute, is the limit. Raw files: `benchmarks/ypir/batch_*`.

**Cost per post view if every read is PIR** (a post sits in one 32 KB piece, read as 3 mixed blocks; 1 core; query upload grows with domain rows at about 12 bytes per row; 473 KB of reusable keys excluded):

| Record size | Domain | Core-seconds | Upload | Download |
| --- | --- | --- | --- | --- |
| 32 KB | 1 GB | 1.4 | 1.1 MB | 370 KB |
| 32 KB | 8 GB | 4.7 | 9 MB | 370 KB |
| 32 KB | 64 GB | 31 | 72 MB | 370 KB |
| 3.5 KB | 1 GB | 0.6 | 10 MB | 37 KB |
| 3.5 KB | 8 GB | 3.8 | 82 MB | 37 KB |

At 5 billion post views a day (about 10 million daily users), direct PIR for every view needs about 80,000 cores at 1 GB domains or 270,000 at 8 GB. If a caching layer absorbs 90% / 95% / 99% of views, 8 GB domains need about 27,000 / 13,000 / 2,700 cores.

**What this means for the design**

- **The private path works without hints.** YPIR removes SimplePIR's blocker; per-query traffic is a few hundred KB.
- **Scan throughput matches the budget.** About 6.5–11 GB/s per core, so a 32-core node scans roughly 200–300 GB/s and will be memory-bandwidth bound, consistent with the design's 200 GB/s assumption (about 25 hot queries/s on an 8 GB domain).
- **Ring packing is a fixed cost per instance** (about 30 ms on one core), independent of domain size. For 32 KB records it is about 0.3 core-seconds per record and dominates below a few GB of domain. It parallelizes across instances and cores. This argues for large domains (the scan then dominates) and is a reason to revisit whether private-path records should be smaller than 32 KB.
