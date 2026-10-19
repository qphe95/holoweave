"""Holoweave: per-file outer code vs. group (cross-file) outer code.
A stripe dies when the coalition holds >= 65 of its 96 slots: p(alpha) = P[Bin(96, alpha) >= 65].
Outer code at rate 1/2: a unit with K data pieces has 2K pieces, any K rebuild it.
Killing a unit = killing > K of its 2K stripes. Per-file: K = file pieces (32 for 1 MB).
Group: K = group data / 32 KB (2048 for 64 MB, 32768 for 1 GB)."""
from scipy.stats import binom
import numpy as np
n, t = 96, 65
def p_stripe(a): return binom.sf(t-1, n, a)
def p_unit(a, K): return binom.sf(K, 2*K, p_stripe(a))   # P[dead >= K+1]
def thresh(K, target):
    lo, hi = 0.3, 0.9
    for _ in range(60):
        mid=(lo+hi)/2
        if p_unit(mid,K) > target: hi=mid
        else: lo=mid
    return lo
units = [("per-file code, m = 32", 16), ("per-file code, m = 64", 32),
         ("64 MB group", 2048), ("1 GB group", 32768)]
lo,hi=0.5,0.9
for _ in range(60):
    mid=(lo+hi)/2
    if p_stripe(mid)>0.5: hi=mid
    else: lo=mid
print(f"  p_stripe = 1/2 at alpha = {lo:.3f}")
print("\nChance a chosen unit can be killed, by coalition stake:")
alphas=[0.55,0.60,0.62,0.64,0.65,0.66,0.67,0.68,0.70]
print("  unit".ljust(30)+"".join(f"{a:>10.2f}" for a in alphas))
for name,K in units:
    print("  "+name.ljust(28)+"".join(f"{p_unit(a,K):>10.1e}" for a in alphas))
print("\nLargest stake keeping one chosen unit below 1e-18 / 1e-9 / 1/2:")
for name,K in units:
    print(f"  {name:28s} {thresh(K,1e-18):.3f} / {thresh(K,1e-9):.3f} / {thresh(K,0.5):.3f}")
print("\nStripes the coalition must kill (at least) to kill the target, and the stored data those stripes hold:")
for name,K in units:
    st=K+1
    print(f"  {name:28s} {st:>6d} stripes = {st*96*32/1024/1024:8.1f} GB of stored symbols")
print("\nReader cost to rebuild a 1 MB target from its group under attack (YPIR, 1 GB domains):")
for name,K in units[2:]:
    q=K; print(f"  {name:28s} {q} PIR queries, {q*0.46/3600:.2f} core-hours, {q*0.37/1024:.2f} GB upload, {q*0.12/1024:.2f} GB download")
