# Monthly sd of USOIL log returns (power line for I-68); development data only (< 2021-09-14).
import glob
import os

import numpy as np
import pandas as pd

files = sorted(glob.glob("data/cache/histdata_presample/USOIL/*/*.parquet") + glob.glob("data/cache/histdata/USOIL/*/*.parquet"),
               key=os.path.basename)
by_month = {}
for f in files:
    d = os.path.basename(f)[:10]
    if d < "2021-09-14":
        by_month.setdefault(d[:7], []).append(f)
closes = {}
for m, fs in by_month.items():
    for f in reversed(fs):
        df = pd.read_parquet(f, columns=["bid_close"])
        if len(df):
            closes[m] = float(df["bid_close"].iloc[-1]); break
s = pd.Series(closes).sort_index()
r = np.log(s[s > 0]).diff().dropna()
print(s.index[0], s.index[-1], len(r), f"monthly sd {r.std():.4f}", f"annual {r.std() * 12 ** 0.5:.3f}")
