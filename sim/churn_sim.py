"""Holoweave churn-aware G1.

Static model (slots drawn with replacement by stake): each of the n = 96 slots of a
stripe is independently
    - held by the coalition                      w.p. x   (x = coalition SLOT share)
    - held by an honest node that is unavailable w.p. (1 - x) * u
    - held by an honest node that is available   w.p. (1 - x) * (1 - u)
A stripe is blockable when fewer than w = 32 slots are honest-available, so only
beta = x + (1 - x) u  matters.

Part A shows that under churn the slot share x need NOT equal the stake share alpha:
  policy "fresh":  a released slot (exit, repair, reshuffle) gets a fresh stake-weighted
                   holder.  A coalition that never leaves keeps every slot it wins while
                   honest exits keep releasing slots: the REPAIR RATCHET.
                   Steady state x = alpha (lam + r) / (lam alpha + r), r = reshuffle rate.
  policy "hrw":    stake-weighted rendezvous hashing: slot holder = argmin_v Exp_v(seed)/stake_v
                   over the CURRENT node set.  Joiners take slots in proportion to stake,
                   so x = alpha at all times regardless of history.
It also checks the static model against the simulated stripe failure rate.

Part B derives requirements from the static model with x = alpha (hrw policy).
"""
import numpy as np
from math import comb

n, w, d1 = 96, 32, 1  # d1 = blocks per piece; 1 since mixing was dropped (was 3)
HOURS_PER_YEAR = 8760


def binom_cdf_lt(N, p, k):
    return sum(comb(N, i) * p**i * (1 - p) ** (N - i) for i in range(k))


def binom_tail(N, p, k):
    return sum(comb(N, i) * p**i * (1 - p) ** (N - i) for i in range(k, N + 1))


def stripe_fail(x, u):
    return binom_cdf_lt(n, (1 - x) * (1 - u), w)


def file_fail(p, m=32):
    q = 1 - (1 - p) ** d1
    return binom_tail(m, q, m // 2 + 1)


def u_pending(lam_per_year, D_hours):
    y = lam_per_year * D_hours / HOURS_PER_YEAR
    return y / (1 + y)


def u_total(lam, D, u0, phi=0.0):
    return 1 - (1 - u_pending(lam, D)) * (1 - u0) * (1 - phi)


def ratchet_share(alpha, lam, r):
    return alpha * (lam + r) / (lam * alpha + r)


def fmt(x):
    return "0" if x == 0 else f"{x:.1e}"


# ---------------------------------------------------------------- Part A
def monte_carlo(policy, N=500, S=1000, alpha=0.4, lam=4.0, D=720, u0=0.01,
                r=1 / 3, down_mean_h=4, years=3, seed=1, report_every_years=0.5):
    """Hourly simulation. Honest nodes exit at rate lam/yr (abruptly: their slots are
    unavailable for D hours while being rebuilt) and are replaced by a fresh honest
    identity at the same index and stake.  Coalition nodes never leave.
    Returns list of (year, coalition slot share, stripe fail rate over the last period)."""
    rng = np.random.default_rng(seed)
    stake = np.ones(N)
    coal = np.zeros(N, bool)
    coal[rng.choice(N, int(round(alpha * N)), replace=False)] = True
    if policy == "hrw":
        score = (rng.exponential(size=(S * n, N)) / stake).astype(np.float32)
        holder = score.argmin(1)
        hscore = score[np.arange(S * n), holder]
    else:
        holder = rng.integers(0, N, size=S * n)
    ready_at = np.full(S * n, -1, dtype=np.int64)  # slot unavailable until this hour
    online = rng.random(N) > u0
    p_back = 1 / down_mean_h
    p_down = u0 / (1 - u0) * p_back
    p_depart = lam / HOURS_PER_YEAR
    p_resh = r / HOURS_PER_YEAR
    T = int(years * HOURS_PER_YEAR)
    step = int(report_every_years * HOURS_PER_YEAR)
    out, fails, looks = [], 0, 0
    for t in range(T):
        rr = rng.random(N)
        online = np.where(online, rr > p_down, rr < p_back)
        for j in np.flatnonzero((rng.random(N) < p_depart) & ~coal):
            mine = np.flatnonzero(holder == j)
            online[j] = True
            if policy == "hrw":
                # new identity at index j: fresh scores; its old slots go to the new argmin
                score[:, j] = rng.exponential(size=S * n) / stake[j]
                if mine.size:
                    holder[mine] = score[mine].argmin(1)
                    hscore[mine] = score[mine, holder[mine]]
                    ready_at[mine] = t + D  # rebuilt from the stripe
                stolen = np.flatnonzero(score[:, j] < hscore)
                stolen = stolen[holder[stolen] != j]
                if stolen.size:
                    # joiner takes slots it now ranks first on; handoff is immediate from an
                    # honest holder, a coalition holder refuses so the slot is rebuilt
                    ready_at[stolen[coal[holder[stolen]]]] = t + D
                    holder[stolen] = j
                    hscore[stolen] = score[stolen, j]
            else:
                if mine.size:
                    holder[mine] = rng.integers(0, N, size=mine.size)
                    ready_at[mine] = t + D
        if policy == "fresh":
            # yearly reshuffle of 1/3 of slots, by direct transfer
            sh = np.flatnonzero(rng.random(S * n) < p_resh)
            if sh.size:
                refuse = sh[coal[holder[sh]]]
                holder[sh] = rng.integers(0, N, size=sh.size)
                ready_at[refuse] = t + D
        avail = (ready_at <= t) & ~coal[holder] & online[holder]
        fails += np.count_nonzero(avail.reshape(S, n).sum(1) < w)
        looks += S
        if (t + 1) % step == 0:
            out.append(((t + 1) / HOURS_PER_YEAR, coal[holder].mean(), fails / looks,
                        1 - avail[~coal[holder]].mean()))
            fails = looks = 0
    return out


# ---------------------------------------------------------------- Part B
def max_beta(target, m=32):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if file_fail(binom_cdf_lt(n, 1 - mid, w), m) <= target:
            lo = mid
        else:
            hi = mid
    return lo


def max_delay_hours(alpha, lam, u0, target, phi=0.0, m=32):
    umax = 1 - (1 - max_beta(target, m)) / (1 - alpha)
    amax = 1 - (1 - umax) / ((1 - u0) * (1 - phi))
    if amax <= 0:
        return 0.0
    y = amax / (1 - amax)
    return y * HOURS_PER_YEAR / lam


if __name__ == "__main__":
    import sys
    print("=== Part A: placement policy under churn (N=500 nodes, 1,000 stripes, alpha=0.4,")
    print("    honest exits lam=4/yr abrupt, rebuild D=30 days, 1% transient downtime) ===")
    for policy in ("fresh", "hrw"):
        res = monte_carlo(policy)
        pred = ratchet_share(0.4, 4.0, 1 / 3) if policy == "fresh" else 0.4
        print(f" policy={policy}: predicted steady coalition slot share {pred:.3f}")
        for yr, x, sf, u in res:
            model = stripe_fail(x, u)
            print(f"   year {yr:.1f}: coalition slot share {x:.3f}  honest-unavailable {u:.3f}  "
                  f"stripe fail MC={fmt(sf)}  model(x,u)={fmt(model)}")
        sys.stdout.flush()

    print("\n=== A2: ratchet steady state, policy 'fresh' (x = alpha (lam + r)/(lam alpha + r)) ===")
    for alpha in (0.2, 0.33, 0.4):
        cells = []
        for lam in (0.1, 0.25, 0.5, 1.0):
            for r in (1 / 3, 1.0, 4.0):
                cells.append(f"{ratchet_share(alpha, lam, r):.2f}")
        print(f"  alpha={alpha}: lam=0.1/0.25/0.5/1 x r=1/3,1,4 per yr: {' '.join(cells)}")

    print("\n=== B1: tolerated beta = x + (1-x) u for one file (m pieces) ===")
    for m in (32, 64, 128):
        print(f"  m={m}: beta_max @1e-9={max_beta(1e-9, m):.3f}  @1e-18={max_beta(1e-18, m):.3f}"
              f"  @1e-30={max_beta(1e-30, m):.3f}")

    print("\n=== B2: steady-state churn under hrw, u0 = 1% transient downtime ===")
    for alpha in (0.33, 0.5):
        for lam in (0.1, 0.5, 2.0):
            row = [fmt(file_fail(stripe_fail(alpha, u_total(lam, D, 0.01))))
                   for D in (1, 24, 24 * 7, 24 * 30)]
            print(f"  alpha={alpha} lam={lam}/yr  file fail with rebuild delay 1h/1d/7d/30d: {' / '.join(row)}")

    print("\n=== B3: maximum rebuild delay for file failure <= 1e-18 (u0 = 1%) ===")
    for alpha in (0.33, 0.4, 0.5):
        for lam in (0.1, 0.5, 2.0):
            D = max_delay_hours(alpha, lam, 0.01, 1e-18)
            Dphi = max_delay_hours(alpha, lam, 0.01, 1e-18, phi=0.10)
            print(f"  alpha={alpha} lam={lam}/yr: D_max = {D/24:8.1f} days   "
                  f"(also surviving a 10% outage: {Dphi/24:8.1f} days)")

    print("\n=== B4: correlated outage of phi of honest stake (u0=1%, lam=0.5/yr, D=1 day) ===")
    for alpha in (0.0, 0.2, 0.33, 0.4, 0.5):
        row = [fmt(file_fail(stripe_fail(alpha, u_total(0.5, 24, 0.01, phi))))
               for phi in (0.05, 0.10, 0.20, 0.30, 0.40)]
        print(f"  alpha={alpha:.2f}: phi=5/10/20/30/40%: {' / '.join(row)}")

    print("\n=== B5: mass permanent loss (seizure) of phi of ALL stake ===")
    for alpha in (0.0, 0.2, 0.33, 0.4):
        row = [fmt(file_fail(binom_cdf_lt(n, max(1 - alpha - phi, 0), w)))
               for phi in (0.10, 0.20, 0.30, 0.40)]
        print(f"  alpha={alpha:.2f}: lose 10/20/30/40% of stake: {' / '.join(row)}")
    print("  rebuild time after losing phi of stake, 20 TB per node, Clay repair 1.5x:")
    for bw_mbps in (100, 1000):
        row = []
        for phi in (0.10, 0.20, 0.30, 0.40):
            secs = phi / (1 - phi) * 20e12 * 1.5 / (bw_mbps * 1e6 / 8)
            row.append(f"{secs/86400:.1f}d")
        print(f"    {bw_mbps} Mbit/s per node for repair: {' / '.join(row)}")
