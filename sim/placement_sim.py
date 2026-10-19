"""Holoweave placement simulation.

Per-stripe random placement: each stripe gets n=96 distinct holders drawn by stake
(without replacement). A stripe is blockable if the coalition holds >= t = n - w + 1
of its *present* holders such that fewer than w honest present holders remain.
A piece needs all d+1 = 3 of its stripes; a file (m pieces) fails if more than m/2
pieces fail.
"""
import numpy as np
from math import comb

rng = np.random.default_rng(7)
n, w = 96, 32
m, blocks_per_piece = 32, 3


def stakes(N, kind):
    if kind == "uniform":
        s = np.ones(N)
    elif kind.startswith("zipf"):
        a = float(kind[4:])
        s = 1.0 / np.arange(1, N + 1) ** a
    return s / s.sum()


def coalition(st, alpha, kind):
    N = len(st)
    order = np.argsort(-st) if kind == "top" else rng.permutation(N)
    c = np.zeros(N, bool)
    tot = 0.0
    for i in order:
        if tot >= alpha:
            break
        c[i] = True
        tot += st[i]
    return c, tot


def sample_stripes(st, S):
    N = len(st)
    out = np.empty((S, n), dtype=np.int32)
    for k in range(S):
        out[k] = rng.choice(N, size=n, replace=False, p=st)
    return out


def binom_tail(N_, p, k):
    return sum(comb(N_, i) * p**i * (1 - p) ** (N_ - i) for i in range(k, N_ + 1))


def file_fail(p_stripe):
    q = 1 - (1 - p_stripe) ** blocks_per_piece
    return binom_tail(m, q, m // 2 + 1)


def stripe_fail_rate(holders, coal, down=None):
    """Fraction of stripes with fewer than w honest, present holders."""
    honest = ~coal[holders]
    if down is not None:
        honest &= ~down[holders]
    return np.mean(honest.sum(1) < w)


def adaptive_cost(st, trials=20):
    """Greedy: operators a censor must coerce to kill > m/2 pieces of one file."""
    N = len(st)
    costs = []
    for _ in range(trials):
        H = sample_stripes(st, m * blocks_per_piece).reshape(m, blocks_per_piece, n)
        # greedy over operators by how many of this file's slots they hold
        counts = np.bincount(H.ravel(), minlength=N)
        order = np.argsort(-counts)
        coerced = np.zeros(N, bool)
        for k, op in enumerate(order, 1):
            coerced[op] = True
            if k % 5 and k < N:  # check every few additions
                continue
            dead_stripe = (coerced[H].sum(-1) > n - w)  # >=65 coerced holders
            dead_piece = dead_stripe.any(-1)
            if dead_piece.sum() > m // 2:
                costs.append(k)
                break
    return int(np.median(costs)), int(min(costs))


if __name__ == "__main__":
    S = 20000
    for N in (1000, 10000):
        for dist in ("uniform", "zipf0.8", "zipf1.0"):
            st = stakes(N, dist)
            top10 = np.sort(st)[::-1][:10].sum()
            H = sample_stripes(st, S)
            print(f"\n=== N={N} stake={dist} (top-10 operators hold {top10:.0%})")
            for ck in ("random", "top"):
                for alpha in (0.33, 0.5, 0.55, 0.6, 0.65):
                    c, tot = coalition(st, alpha, ck)
                    p = stripe_fail_rate(H, c)
                    pb = binom_tail(n, tot, n - w + 1)
                    ff = f"{file_fail(p):.1e}" if p > 0 else f"<{file_fail(1.0 / S):.0e} (no stripe failed in {S})"
                    print(f"  coalition={ck:6s} alpha={tot:.3f} ops={c.sum():5d}  "
                          f"stripe fail MC={p:.2e} (binomial {pb:.2e})  file fail {ff}")
            # correlated outage: 10% of nodes down at once, coalition 50% random
            c, tot = coalition(st, 0.5, "random")
            for phi in (0.05, 0.10, 0.20):
                down = rng.random(N) < phi
                down &= ~c
                p = stripe_fail_rate(H, c, down)
                print(f"  outage {phi:.0%} of honest nodes + 50% coalition: stripe fail={p:.2e} file fail~{file_fail(p):.1e}")
            med, mn = adaptive_cost(st, trials=8)
            print(f"  adaptive censor must coerce ~{med} operators (min {mn}) to destroy one file")
