#!/usr/bin/env python3
"""Synthetic stand-in for the competition files, for testing the pipeline.

Mimics the known layout: 4 target stations, Train.csv missing 22-23 Oct 2026,
Test.csv = 4 stations x 27 days (22 Oct - 17 Nov 2026) = 2,592 rows, and an
AdditionalHistory.zip of CPCB-style exports (dd-mm-yyyy times).
Hidden truth for the test rows goes to <out>/_truth.csv.
"""
import io
import os
import sys
import zipfile

import numpy as np
import pandas as pd

out = sys.argv[1] if len(sys.argv) > 1 else "data_synth"
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(0)
times = pd.date_range("2022-01-01", "2026-11-17 23:00", freq="h")
T = len(times)
doy = times.dayofyear.values
hr = times.hour.values
season = 45 + 35 * np.cos(2 * np.pi * (doy - 15) / 365.25)  # winter peak, monsoon trough
diurnal = 1 + 0.25 * np.exp(-((hr - 9) ** 2) / 6) + 0.35 * np.exp(-((hr - 22) ** 2) / 8)
diwali = pd.to_datetime(["2022-10-24", "2023-11-12", "2024-10-31", "2025-10-20", "2026-11-08"])
spike = np.zeros(T)
for d in diwali:
    dh = (times - (d + pd.Timedelta(hours=22))) / pd.Timedelta(hours=1)
    spike += 2.0 * np.exp(-(dh ** 2) / (2 * 6 ** 2))


def ar(phi, sig):
    e = rng.normal(0, sig, T)
    x = np.zeros(T)
    for i in range(1, T):
        x[i] = phi * x[i - 1] + e[i]
    return x


common = ar(0.97, 0.06)
names = ["Bandra", "Colaba", "Powai", "Worli", "Andheri", "Chembur", "Sion"]
series = {}
for k, n in enumerate(names):
    base = 0.8 + 0.1 * k
    v = base * season * diurnal * np.exp(common + ar(0.9, 0.08) + spike) * rng.lognormal(0, 0.1, T)
    v[rng.random(T) < 0.03] = np.nan
    gap = rng.integers(0, T - 500)
    v[gap:gap + rng.integers(24, 300)] = np.nan
    series[n] = np.round(v, 2)

targets = names[:4]
gap = (times >= "2026-10-22") & (times < "2026-10-24")
test_mask = (times >= "2026-10-22") & (times <= "2026-11-17 23:00")
train_end = times <= "2026-10-26 23:00"
tr, te = [], []
for i, n in enumerate(targets):
    sid = f"site_{100 + i}"
    keep = train_end & ~gap
    tr.append(pd.DataFrame({"station_id": sid, "datetime": times[keep], "pm2_5": series[n][keep]}))
    te.append(pd.DataFrame({"station_id": sid, "datetime": times[test_mask], "truth": series[n][test_mask]}))
tr = pd.concat(tr, ignore_index=True)
te = pd.concat(te, ignore_index=True)
tr.insert(0, "ID", [f"ID_{s}_{t:%Y%m%d%H}" for s, t in zip(tr.station_id, tr.datetime)])
te.insert(0, "ID", [f"ID_{s}_{t:%Y%m%d%H}" for s, t in zip(te.station_id, te.datetime)])
tr.to_csv(f"{out}/Train.csv", index=False)
te[["ID", "station_id", "datetime"]].to_csv(f"{out}/Test.csv", index=False)
te[["ID"]].assign(Target=0).to_csv(f"{out}/SampleSubmission.csv", index=False)
te[["ID", "truth"]].to_csv(f"{out}/_truth.csv", index=False)
pd.DataFrame({"station_id": [f"site_{100 + i}" for i in range(4)], "name": targets,
              "lat": 19.0 + 0.03 * np.arange(4), "lon": 72.85 + 0.02 * np.arange(4)}
             ).to_csv(f"{out}/Stations.csv", index=False)
with zipfile.ZipFile(f"{out}/AdditionalHistory.zip", "w") as z:
    for n in names[4:]:
        m = times <= "2026-10-26 23:00"
        df = pd.DataFrame({"From Date": times[m].strftime("%d-%m-%Y %H:%M"),
                           "To Date": (times[m] + pd.Timedelta(hours=1)).strftime("%d-%m-%Y %H:%M"),
                           "PM2.5 (ug/m3)": series[n][m]})
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        z.writestr(f"AdditionalHistory/{n}.csv", buf.getvalue())
print(f"wrote {out}: train {len(tr)} rows, test {len(te)} rows")
