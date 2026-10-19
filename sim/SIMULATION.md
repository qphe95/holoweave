# Simulations and benchmarks

Current as of Oct 19, 2026. These scripts check the numbers in [../docs/design.md](../docs/design.md) and [../docs/security-games.md](../docs/security-games.md).

| File | What it is | Reflects current design? |
| --- | --- | --- |
| `group_code.py`, `group_results.txt` | Packs versus coding each file on its own: thresholds, stripes to kill, rebuild cost (the script calls packs "groups"; they are not the monthly expiry groups) | Yes |
| `pack_churn.py`, `pack_churn_results.txt` | G1 under churn for 64 MB packs: β\_max, rebuild delay, outages, seizure | Yes |
| `traffic_model.py`, `traffic_results.txt` | G2 traffic model: what timing reveals about which file a reader wants | Yes |
| `churn_sim.py`, `churn_results.txt` | Placement under churn (Monte Carlo): the repair ratchet and the rendezvous fix | Yes for placement; its β tables use per-file codes |
| `placement_sim.py`, `results.txt` | Monte Carlo of per-stripe placement | Partly: it draws distinct holders (`replace=False`), the rule the run found broken; set `replace=True` for the current rule |
| `benchmarks/ypir/` | Raw YPIR logs and JSON | Yes |
| `benchmarks/bench_*.txt` | Raw SimplePIR logs | Yes (SimplePIR is ruled out) |

Run any script with `python3 <name>.py` (numpy and scipy). Each takes seconds to a few minutes.

## Packs (`group_code.py`)

The outer code runs over 64 MB packs of many files: 2,048 data pieces plus 2,048 parity, any 2,048 rebuild the pack. To kill one chosen file a coalition must fail at least 2,049 of the pack's stripes at once, about 6 GB of stored symbols.

| Unit | Largest stake keeping one chosen file below 10⁻¹⁸ | Below 10⁻⁹ | Stripes to kill |
| --- | --- | --- | --- |
| **64 MB pack (current)** | **0.663** | **0.666** | **2,049** |
| 1 GB pack | 0.669 | 0.670 | 32,769 |
| Each 1 MB file coded alone (32 pieces) | 0.576 | 0.608 | 17 |
| Each 2 MB file coded alone (64 pieces) | 0.604 | 0.626 | 33 |

A single stripe fails with probability 1/2 at 67.1% of stake, so packs put the threshold for one chosen file almost where a coalition could black out most of the network. 64 MB was chosen because 1 GB packs gain very little and make rebuilding a file under attack 16 times costlier. Rebuilding a file from its 64 MB pack takes 2,048 PIR queries and about 0.26 core-hours (the script's upload figure, 0.74 GB, assumes 0.37 MB per query; the measured query size, about 0.23 MB, gives about 0.47 GB).

Packs don't stop a holder who knows a file's address from deleting its own pieces of that file; below the threshold readers rebuild them from other holders, and a wrong signed answer is provable (Security games, Theorem 4). Packs also don't change how many *operators* hold that stake: with zipf-concentrated stake, the top 80 of 1,000 operators (or 370 of 10,000) hold two-thirds. Those operator counts are heuristic; the search script is not in this folder.

## G1 under churn for packs (`pack_churn.py`)

Under churn, availability depends on β, the share of slots not held by an honest, online, rebuilt holder:

β = α + (1 − α)·[1 − (1 − λD/(1 + λD))·(1 − u₀)·(1 − φ)]

(λ abrupt honest exits per year, *D* rebuild delay, u₀ transient downtime, φ correlated outage share of honest stake). One pack stays below 10⁻⁹ / 10⁻¹⁸ / 10⁻³⁰ while β ≤ 0.666 / 0.663 / 0.660.

**Longest rebuild delay keeping a file below 10⁻¹⁸** (1% downtime):

| α | λ = 0.1/yr | λ = 0.5/yr | λ = 2/yr | λ = 0.5/yr, plus a 10% outage |
| --- | --- | --- | --- | --- |
| 33% | 3,535 days | 707 days | 177 days | 563 days |
| 40% | 2,785 days | 557 days | 139 days | 428 days |
| 50% | 1,712 days | 342 days | 86 days | 235 days |

**Temporary outage** of φ of honest stake (λ = 0.5/yr, 1-day rebuilds, 1% downtime): file loss is below 10⁻³⁰⁰ everywhere except a 50% coalition with a 30% outage (about 3 × 10⁻⁷⁵) or 40% outage (the file can be blocked while the outage lasts), and a 40% coalition with a 40% outage (about 2 × 10⁻¹⁸⁰).

**Permanent seizure** of φ of all stake, with the coalition withholding its symbols: β = α + φ, and the result is a cliff. Safe while α + φ is below about 0.66, lost above about 0.67.

| α | lose 10% | 20% | 30% | 40% |
| --- | --- | --- | --- | --- |
| 0% to 20% | safe | safe | safe | safe |
| 33% | safe | safe | safe | lost |
| 40% | safe | safe | lost | lost |
| 50% | safe | lost | lost | lost |

## Placement under churn (`churn_sim.py`)

**The repair ratchet, and the fix.** If every freed slot went to a fresh random holder, a censor that never leaves would keep every slot it wins while honest nodes come and go. Its slot share settles at x\* = α(λ + r)/(λα + r) (λ honest exit rate, r reshuffle rate): a 40% coalition reaches about 62% with λ = 0.5/yr and yearly reshuffles of a third. Holoweave instead uses stake-weighted rendezvous hashing: each slot's holder is the current node ranking first for the slot's seed, so the coalition's slot share equals its stake share at all times.

Monte Carlo (500 nodes, 1,000 stripes, α = 0.4, heavy churn: λ = 4/yr abrupt exits, 30-day rebuild, 1% downtime, hourly steps for 3 years):

| Year | Fresh-draw rule: coalition slot share | Rendezvous: coalition slot share | Rendezvous: stripe fail (sim) | Stripe fail (β model) |
| --- | --- | --- | --- | --- |
| 0.5 | 0.706 | 0.403 | 3.5 × 10⁻² | 1.9 × 10⁻² |
| 1.0 | 0.832 | 0.400 | 2.3 × 10⁻² | 2.6 × 10⁻³ |
| 2.0 | 0.881 | 0.404 | 3.5 × 10⁻² | 4.6 × 10⁻² |
| 3.0 | 0.897 (predicted 0.897) | 0.400 | 2.5 × 10⁻² | 3.8 × 10⁻² |

The β model uses an end-of-period snapshot of honest unavailability, which fluctuates; period averages match within about 2x. The script's β\_max tables are for files coded on their own (0.576 / 0.604 / 0.624 at 10⁻¹⁸ for 32 / 64 / 128 pieces); packs are in `pack_churn.py`.

Implementation note: argmin over all nodes per slot is O(N); production needs a sub-linear equivalent (hierarchical rendezvous hashing, or a stake-weighted hash ring with many virtual nodes), checked to keep exact stake proportionality and history independence.

## Placement Monte Carlo (`placement_sim.py`)

With even stake, simulated stripe failure tracks the binomial model (20,000 stripes per setting, 10,000 nodes):

| Coalition stake | Stripe fails, simulated | Binomial model |
| --- | --- | --- |
| 33% | 0 in 20,000 | 3.9 × 10⁻¹² |
| 50% | 2.0 × 10⁻⁴ | 3.4 × 10⁻⁴ |
| 55% | 7.5 × 10⁻³ | 7.6 × 10⁻³ |
| 60% | 7.4 × 10⁻² | 7.4 × 10⁻² |
| 65% | 0.32 | 0.33 |

The same run showed why holders are drawn *with replacement* by stake. Drawing 96 distinct nodes per stripe caps a big operator at one slot per stripe, so when honest stake sits with a few big operators and the coalition is many small nodes, the coalition gets far more slots than its stake: at 1,000 nodes with the top 10 holding 39%, a 60% coalition of small nodes blocked 80% of stripes against 8% predicted. Drawing with replacement makes the coalition's slot count exactly Bin(96, α) for any stake distribution.

## G2 traffic model (`traffic_model.py`)

What a coalition can learn about which file a reader wants, in the best case for the reader: each query sent separately (for example over Tor), so a node sees only (node, domain, arrival time).

**Linking is decisive.** Expected number of *other* minimum-size files with a piece in each of j linked 1 GB domains:

| User data | j = 1 | j = 2 | j = 3 |
| --- | --- | --- | --- |
| 20 TB | 10,900 | 3.0 | 0.0008 |
| 1 PB | 10,900 | 0.06 | 3 × 10⁻⁷ |

**Timing bursts.** Placement is public, so reading a known set (a file, a profile) sends a burst to known domains. Each cell is the advantage of the best test (total variation) / share of the target's queries refusable at ≤ 1% collateral, for α = 50% and background traffic of 0.01 queries/s per domain:

| Read | W = 10 s | 1 min | 1 h | 8 h |
| --- | --- | --- | --- | --- |
| One post | 0 | 0 | 0 | 0 |
| Profile, 20 posts | 0.73 / 59% | 0.54 / 34% | 0.10 / 2% | 0.04 / 1% |
| 1 MB file | 0.78 / 72% | 0.62 / 44% | 0.13 / 2% | 0.05 / 1% |
| 10 MB file | 0.92 / 93% | 0.85 / 85% | 0.37 / 14% | 0.15 / 3% |

A Monte Carlo of the raw event streams (200,000 trials) gives 0.6157 against the exact 0.6159 for the 1 MB, 1-minute case. **Consequence:** reads of files and profiles are recognizable even over an anonymity layer, so Holoweave doesn't rely on one. G2 rests on record privacy (PIR hides the record in any context) and routing around refusals, and G3 makes deleting a recognized file's record provable.

## YPIR benchmark

Reference implementation ([menonsamir/ypir](https://github.com/menonsamir/ypir)), YPIR+SP mode, built with `target-cpu=native` on an AMD Ryzen 5 7600X (AVX-512), 2 cores, 3.9 GB RAM; server answer single-threaded. YPIR+SP retrieves 3.5 KB per *instance*; a 32 KB record is 10 instances sharing one query.

**Measured, one 3.5 KB item:**

| Domain | Rows | Server time | Scan | Ring packing | Scan rate | Upload | Download | Offline prep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 56 MB | 16,384 | 37 ms | 6 ms | 31 ms | about 9 GB/s | 588 KB | 12 KB | 1.1 s |
| 112 MB | 32,768 | 43 ms | 10 ms | 32 ms | about 11 GB/s | 702 KB | 12 KB | 1.4 s |
| 128 MB | 37,449 | 53 ms | 20 ms | 30 ms | about 6.7 GB/s | 932 KB | 12 KB | 2.0 s |
| 512 MB | 149,796 | 116 ms | 84 ms | 30 ms | about 6.4 GB/s | 2.3 MB | 12 KB | 6.1 s |

Upload includes 473 KB of packing keys that a client sends once per server and reuses. There is **no client hint**.

**Derived, one 32 KB record (10 instances):**

| Domain | Server time, 1 core | Upload (query + keys) | Download |
| --- | --- | --- | --- |
| 512 MB (16,384 rows × 10) | about 60 ms scan + 310 ms packing ≈ 370 ms | about 115 KB + 473 KB | about 120 KB |
| 1.1 GB (32,768 rows × 10) | about 100 ms scan + 320 ms packing ≈ 420 ms | about 230 KB + 473 KB | about 120 KB |

The design rounds this to about 0.46 core-seconds per record at 1 GB. Running 32 KB items directly ran out of memory on this VM, so these rows are extrapolated from per-instance runs and should be confirmed on a larger machine.

**Batching.** YPIR+SP accepts one client per pass. Standard YPIR batches up to 8 clients, sharing the memory pass (scan per client drops about 1.4x), but ring packing (about 35 ms per client) doesn't batch: net gain about 10%.

| Domain | Clients | Server time | Scan | Ring packing | Per client |
| --- | --- | --- | --- | --- | --- |
| 256 MB | 1 | 54 ms | 15 ms | 35 ms | 54 ms |
| 256 MB | 8 | 428 ms | 118 ms | 292 ms | 54 ms |
| 512 MB | 1 | 68 ms | 30 ms | 36 ms | 68 ms |
| 512 MB | 8 | 489 ms | 177 ms | 278 ms | 61 ms |

**What this means.** Private reads work without hints. Scans run at about 6.5 to 11 GB/s per core, so a 32-core node is memory-bandwidth bound at roughly 200 to 300 GB/s. Ring packing is a fixed cost per instance, about 0.3 core-seconds per 32 KB record, which dominates below a few GB of domain and favors large domains. Still to measure: YPIR at decoding error below 2^-60, which answer fraud proofs need.

## SimplePIR benchmark

Reference implementation ([ahenzinger/simplepir](https://github.com/ahenzinger/simplepir)) on a 2-core cloud VM (Intel Xeon 2.1 GHz, AVX-512), server single-threaded.

| Domain | Record size | Scan rate per core | Server time per query | Upload | Download | One-time client hint |
| --- | --- | --- | --- | --- | --- | --- |
| 128 MB | 1 bit | 9.5 GB/s | about 14 ms | 42 KB | 42 KB | 43 MB |
| 512 MB | 1 bit | 10.1 GB/s | about 50 ms | 85 KB | 85 KB | 87 MB |
| 512 MB | 32 KB | 9.7 GB/s | about 53 ms | 64 KB | 105 KB | 108 MB |

SimplePIR scans fast but needs a client hint of about 100 MB per node and domain, and a read touches many holders, so it is ruled out. The 1 GB run ran out of the VM's 7 GB of RAM.
