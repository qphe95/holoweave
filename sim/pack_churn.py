"""Holoweave: G1 under churn for 64 MB packs (K = 2,048 data pieces, 4,096 stripes).

Uses Theorem 1' (Security games): a slot is "not honest-available" with probability
    beta = alpha + (1 - alpha) * [1 - (1 - lam*D/(1 + lam*D)) * (1 - u0) * (1 - phi)]
and a pack is lost if more than K of its 2K stripes fail, each stripe failing when
fewer than 32 of its 96 slots are honest-available: P[Bin(96, beta) >= 65].

Run: python3 pack_churn.py   (needs scipy; takes a second)
"""
from scipy.stats import binom

N_HOLDERS, BLOCK_AT = 96, 65
K = 2048            # data pieces per 64 MB pack; the pack has 2K pieces in 2K stripes
TARGET = 1e-18


def p_stripe(beta):
    return binom.sf(BLOCK_AT - 1, N_HOLDERS, beta)


def p_pack(beta):
    return binom.sf(K, 2 * K, p_stripe(beta))       # P[more than K stripes fail]


def beta_of(alpha, lam, d_days, u0, phi):
    x = lam * d_days / 365
    return alpha + (1 - alpha) * (1 - (1 - x / (1 + x)) * (1 - u0) * (1 - phi))


def bisect(f, lo, hi, it=80):
    """Largest x in [lo, hi] with f(x) True, f monotone (True then False)."""
    for _ in range(it):
        mid = (lo + hi) / 2
        if f(mid):
            lo = mid
        else:
            hi = mid
    return lo


if __name__ == "__main__":
    print("beta_max (largest beta keeping one pack below the target):")
    for tgt in (1e-9, 1e-18, 1e-30):
        print(f"  {tgt:.0e}: {bisect(lambda b: p_pack(b) <= tgt, 0.3, 0.9):.3f}")

    print("\nLongest rebuild delay D (days) keeping one pack below 1e-18, 1% downtime:")
    print("  alpha   lam=0.1/yr   lam=0.5/yr   lam=2/yr   lam=0.5/yr + 10% outage")
    for a in (0.33, 0.40, 0.50):
        cells = []
        for lam, phi in ((0.1, 0), (0.5, 0), (2, 0), (0.5, 0.1)):
            if p_pack(beta_of(a, lam, 0, 0.01, phi)) > TARGET:
                cells.append("over budget")
            else:
                d = bisect(lambda d: p_pack(beta_of(a, lam, d, 0.01, phi)) <= TARGET, 0, 1e6)
                cells.append(f"{d:,.0f}")
        print(f"  {a:.2f}  " + "   ".join(f"{c:>10s}" for c in cells))

    print("\nTemporary outage of phi of honest stake (lam=0.5/yr, D=1 day, 1% downtime): pack loss")
    print("  alpha   " + "  ".join(f"phi={p:<5}" for p in (0.05, 0.1, 0.2, 0.3, 0.4)))
    for a in (0.0, 0.2, 0.33, 0.4, 0.5):
        row = [p_pack(beta_of(a, 0.5, 1, 0.01, phi)) for phi in (0.05, 0.1, 0.2, 0.3, 0.4)]
        print(f"  {a:.2f}  " + "  ".join(f"{x:9.1e}" for x in row))

    print("\nPermanent seizure of phi of ALL stake, coalition withholds (beta = alpha + phi): pack loss")
    print("  alpha   " + "  ".join(f"phi={p:<5}" for p in (0.1, 0.2, 0.3, 0.4)))
    for a in (0.0, 0.2, 0.33, 0.4, 0.5):
        row = [p_pack(min(a + phi, 1.0)) for phi in (0.1, 0.2, 0.3, 0.4)]
        print(f"  {a:.2f}  " + "  ".join(f"{x:9.1e}" for x in row))
