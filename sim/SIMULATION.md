# Placement simulation and PIR benchmark

Oct 18, 2026

This folder holds a Monte Carlo check of G1 (availability under per-stripe random placement) and a SimplePIR CPU benchmark. Files:

| File | What it is |
| --- | --- |
| `placement_sim.py` | Monte Carlo simulation of per-stripe placement (numpy) |
| `results.txt` | Full output of one run (seed 7, 20,000 stripes per setting) |
| `benchmarks/bench_*.txt` | Raw SimplePIR benchmark logs |

Run with `python3 placement_sim.py` (needs numpy). A run takes a few minutes.

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

## YPIR benchmark (to run)

YPIR could not be built in the cloud environment or the linked VM (crates.io is blocked). To run it natively on a machine with AVX-512 (e.g. Ryzen 7600X):

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
git clone https://github.com/menonsamir/ypir.git && cd ypir
# 512 MB domain, 32 KB records, YPIR+SP
cargo run --release -- 149796 28672 1 3 out_512MB.json -i
# 1 GB domain
cargo run --release -- 299593 28672 1 3 out_1GB.json -i
```

Save the JSON outputs into `sim/benchmarks/`.
