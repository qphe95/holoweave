"""Holoweave G2 traffic model.

What a coalition node sees for each PIR query, if the protocol rules hold
(fresh anonymity circuit, fresh PIR keys and a fresh anonymous payment token per query):
    (node, domain, arrival time)          -- nothing else.
The question is how far a coalition can get by combining these across its nodes.

Part 1  Anonymity set.  If a coalition LINKS j queries as belonging to one read
        (by any side channel), how many files are consistent with the j domains hit?
Part 2  Timing.  Without any side channel, can the coalition tell, for a query
        arriving at a domain that holds a piece of target T, whether it belongs to a
        read of T?  Evidence: the number of other arrivals at T's other coalition-held
        domains in the preceding window W.  We compute the exact advantage (total
        variation distance) of the best threshold test, and the refusal it buys.
Part 3  The spread window W a reader needs to keep the advantage below eps.
"""
from math import exp, lgamma, log, sqrt, pi
import numpy as np
from scipy.special import gammaln

BLOCK = 32 * 1024
DOMAIN = 1 << 30
SYS_PER_DOMAIN = DOMAIN // BLOCK // 3   # Clay 32-of-96: 1/3 of stored symbols are systematic


def pois_pmf(mu, k):
    if mu == 0:
        return 1.0 if k == 0 else 0.0
    return exp(-mu + k * log(mu) - lgamma(k + 1))


def pmf_vec(mu, K):
    return [pois_pmf(mu, k) for k in range(K)]


# ---------------------------------------------------------------- Part 1
def anon_set(user_bytes, j, m=32):
    """Expected number of OTHER files with a piece in each of j given domains."""
    n_sys = 2 * user_bytes / BLOCK          # outer code rate 1/2
    files = n_sys / m                       # minimum-size files (worst case: most files)
    p = SYS_PER_DOMAIN / n_sys
    falling = 1.0
    for i in range(j):
        falling *= (m - i)
    return files * falling * p ** j


# ---------------------------------------------------------------- Part 2
def detector(j, c, r, W, fpr_cap=0.01):
    """A read of target T sends j queries to T's coalition-held domains (c of them),
    spread uniformly over W seconds in random order.  Background queries arrive at
    each domain as Poisson(r).  For an arriving query at a T domain, the coalition
    counts arrivals at T's OTHER c-1 domains in the preceding W seconds.
      H1 (query is part of a T read): count = S + Pois(mu), S uniform on 0..j-1
      H0 (background):                count = Pois(mu)
    Returns (TV advantage, true-refusal rate at <= fpr_cap collateral)."""
    mu = (c - 1) * r * W
    lo = max(0, int(mu - 14 * sqrt(mu + 1)) - 5)
    hi = int(mu + 14 * sqrt(mu + 1)) + j + 30
    ks = np.arange(lo, hi)
    p0 = np.exp(-mu + ks * np.log(mu) - gammaln(ks + 1)) if mu > 0 else (ks == 0).astype(float)
    # H1 = Pois(mu) convolved with uniform{0..j-1}: cumulative-sum trick
    cs = np.concatenate([[0.0], np.cumsum(p0)])
    idx = np.arange(len(ks))
    p1 = (cs[idx + 1] - cs[np.maximum(idx - j + 1, 0)]) / j
    tv = 0.5 * (np.abs(p0 - p1).sum() + (1 - p1.sum()))   # mass of p1 shifted past hi is ~0
    t0 = np.cumsum(p0[::-1])[::-1]
    t1 = np.cumsum(p1[::-1])[::-1]
    ok = t0 <= fpr_cap
    best = float(t1[ok].max()) if ok.any() else 0.0
    return float(tv), best


def spread_needed(j, c, r, eps):
    lo, hi = 0.1, 1e9
    if detector(j, c, r, hi)[0] > eps:
        return float("inf")
    for _ in range(80):
        mid = sqrt(lo * hi)
        if detector(j, c, r, mid)[0] > eps:
            lo = mid
        else:
            hi = mid
    return hi


def fmt_t(s):
    if s == float("inf"):
        return "never"
    if s < 120:
        return f"{s:.0f} s"
    if s < 7200:
        return f"{s/60:.0f} min"
    if s < 172800:
        return f"{s/3600:.1f} h"
    return f"{s/86400:.0f} d"


if __name__ == "__main__":
    print("=== Part 1: files consistent with j linked queries (min-size files, m = 32) ===")
    for name, U in (("20 TB", 20e12), ("1 PB", 1e15), ("10 PB", 1e16)):
        row = " / ".join(f"{anon_set(U, j):.3g}" for j in (1, 2, 3))
        print(f"  {name} of user data: j = 1 / 2 / 3: {row}")

    # per-domain query rate: real queries spread over all 1 GB domains
    print("\n=== Per-domain background rate r (real queries / s per 1 GB domain) ===")
    for name, U, views in (("launch: 20 TB, 50M views/day", 20e12, 5e7),
                           ("scale: 1 PB, 5B views/day", 1e15, 5e9)):
        domains = 6 * U / DOMAIN            # x2 outer code, x3 Clay
        print(f"  {name}: {domains:,.0f} domains, r = {views/86400/domains:.4f}/s")

    targets = [("one post", 1), ("profile, 20 posts", 20), ("1 MB file (32 pieces)", 32),
               ("10 MB file (320 pieces)", 320)]
    print("\n=== Part 2: selective-refusal advantage (TV) / share of T's queries refused at <=1% collateral ===")
    for alpha in (0.33, 0.5):
        for r, rname in ((0.01, "typical r=0.01/s"), (1.0, "hot r=1/s"), (1e-4, "cold r=1e-4/s")):
            print(f"  alpha={alpha}, {rname}")
            for tname, k in targets:
                j = max(1, round(alpha * k))
                c = j
                if k == 1:
                    j = c = 1
                cells = []
                for W in (10, 60, 3600, 8 * 3600):
                    tv, refused = detector(j, c, r, W)
                    cells.append(f"{tv:.2f}/{refused:.2f}")
                print(f"    {tname:26s} W=10s/1min/1h/8h: {'  '.join(cells)}")

    print("\n=== Part 3: spread window W needed for advantage <= eps ===")
    for alpha in (0.33, 0.5):
        for r in (0.01, 1.0):
            for tname, k in targets[1:]:
                j = round(alpha * k)
                cells = [fmt_t(spread_needed(j, j, r, eps)) for eps in (0.25, 0.1, 0.05)]
                print(f"  alpha={alpha} r={r}/s {tname:26s} eps=0.25/0.1/0.05: {' / '.join(cells)}")
