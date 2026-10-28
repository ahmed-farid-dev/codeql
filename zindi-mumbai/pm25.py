#!/usr/bin/env python3
"""Hourly PM2.5 forecasting for the Zindi "Google Mumbai Data Challenge".

Every prediction uses only observations strictly before its cutoff: the hour
after the last target-station observation preceding the forecast hour. So a
test hour inside a gap in Train.csv is forecast from data before the gap, never
from data released after it.

Usage:
  python pm25.py validate --data data/          # rolling-origin backtest
  python pm25.py submit   --data data/          # writes submissions/*.csv
"""
import argparse
import io
import json
import os
import re
import time
import zipfile

import lightgbm as lgb
import numpy as np
import pandas as pd

SEED = 42
P_PAD = 24 * 64  # leading NaN padding so every lookback window stays in bounds
WINS = (1, 3, 6, 12, 24, 48, 72, 168, 336, 720)
HODS = (1, 3, 7, 14, 28)
PUBLIC_H = 48  # public scoring windows are two days long

# Lakshmi Puja dates; fireworks drive the largest PM2.5 spikes of the year.
DIWALI = pd.to_datetime([
    "2014-10-23", "2015-11-11", "2016-10-30", "2017-10-19", "2018-11-07",
    "2019-10-27", "2020-11-14", "2021-11-04", "2022-10-24", "2023-11-12",
    "2024-10-31", "2025-10-20", "2026-11-08", "2027-10-29",
]).values.astype("datetime64[h]")

TIME_KEYS = ["datetime", "timestamp", "datetimeist", "date_time", "fromdate",
             "starttime", "time", "date", "ds"]
STATION_KEYS = ["stationid", "station_id", "station", "siteid", "site",
                "stationname", "location", "locationid"]
TARGET_KEYS = ["target", "pm25", "pm2.5", "pm25ugm3", "pm2_5", "value", "y"]


# ----------------------------------------------------------------- loading

def _norm(c):
    return re.sub(r"[^a-z0-9]", "", str(c).lower())


def find_col(df, keys, what, required=True, exclude=()):
    cols = {_norm(c): c for c in df.columns if c not in exclude}
    for k in keys:
        if _norm(k) in cols:
            return cols[_norm(k)]
    for k in keys:
        for n, c in cols.items():
            if _norm(k) and _norm(k) in n:
                return c
    if required:
        raise KeyError(f"no {what} column among {list(df.columns)}")
    return None


def parse_time(s):
    s = s.astype(str).str.strip()
    try:
        t = pd.to_datetime(s, format="ISO8601")
    except (ValueError, TypeError):
        # dd-mm-yyyy (CPCB exports) vs mm-dd-yyyy: decide from the data
        parts = s.str.extract(r"^(\d{1,2})[-/.](\d{1,2})[-/.]\d{4}")
        dayfirst = True
        if parts.notna().all(axis=None):
            a, b = parts[0].astype(int), parts[1].astype(int)
            dayfirst = not ((b > 12).any() and not (a > 12).any())
        t = pd.to_datetime(s, dayfirst=dayfirst, errors="coerce")
    if getattr(t.dt, "tz", None) is not None:
        t = t.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    return t.dt.floor("h")


def standardize(df, default_station=None, need_target=True):
    """Return (station, time, y?) with original row order kept."""
    tcol = find_col(df, TIME_KEYS, "time")
    t = parse_time(df[tcol])
    hcol = find_col(df, ["hour"], "hour", required=False, exclude=(tcol,))
    if hcol is not None and (t.dt.hour == 0).all():
        t = t + pd.to_timedelta(pd.to_numeric(df[hcol], errors="coerce"), unit="h")
    scol = find_col(df, STATION_KEYS, "station", required=default_station is None)
    out = pd.DataFrame({
        "station": df[scol].astype(str).str.strip() if scol else default_station,
        "time": t,
    })
    if need_target:
        ycol = find_col(df, TARGET_KEYS, "target", exclude=(tcol, scol, "ID", "id"))
        out["y"] = pd.to_numeric(df[ycol], errors="coerce")
    return out


def clean_y(obs):
    y = obs["y"].where((obs["y"] > 0) & (obs["y"] < 1500))
    # a sensor stuck on one value for a day or more is reporting garbage
    o = obs.assign(y=y).sort_values(["station", "time"])
    run = (o["y"] != o.groupby("station")["y"].shift()).cumsum()
    stuck = o.groupby(run)["y"].transform("size") >= 24
    o.loc[stuck & o["y"].notna(), "y"] = np.nan
    return o.dropna(subset=["y", "time"])


def load_additional(path):
    """Every CSV inside AdditionalHistory.zip that has a time and PM2.5 column."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=["station", "time", "y"])
    frames = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.lower().endswith(".csv"):
                continue
            df = pd.read_csv(io.BytesIO(z.read(name)))
            try:
                frames.append(standardize(df, default_station=os.path.basename(name)[:-4]))
            except KeyError as e:
                print(f"  skip {name}: {e}")
    if not frames:
        return pd.DataFrame(columns=["station", "time", "y"])
    out = pd.concat(frames, ignore_index=True)
    out["station"] = "x_" + out["station"].astype(str)
    return out


# ------------------------------------------------------------------ panels

class Panel:
    """S x T hourly matrix with prefix sums giving O(1) window statistics.

    Grid index g is stored at padded index g + P_PAD.
    """

    def __init__(self, Y):
        S, T = Y.shape
        V = np.concatenate([np.full((S, P_PAD), np.nan), Y], axis=1)
        M = ~np.isnan(V)
        V0 = np.where(M, V, 0.0)
        z = np.zeros((S, 1))
        self.V = V
        self.cs = np.concatenate([z, V0.cumsum(1)], 1)
        self.cs2 = np.concatenate([z, (V0 ** 2).cumsum(1)], 1)
        self.cn = np.concatenate([z, M.cumsum(1)], 1)
        Tp = V.shape[1]
        n = -(-Tp // 24) * 24

        def cum24(A):  # cum24[p] = A[p] + A[p-24] + A[p-48] + ...
            B = np.zeros((S, n))
            B[:, :Tp] = A
            return B.reshape(S, -1, 24).cumsum(1).reshape(S, n)[:, :Tp]

        self.c24 = cum24(V0)
        self.n24 = cum24(M.astype(float))
        self.last_idx = np.maximum.accumulate(np.where(M, np.arange(Tp), -1), axis=1)

    def win(self, s, a, b):
        n = self.cn[s, b] - self.cn[s, a]
        m = np.where(n > 0, (self.cs[s, b] - self.cs[s, a]) / np.maximum(n, 1), np.nan)
        m2 = np.where(n > 0, (self.cs2[s, b] - self.cs2[s, a]) / np.maximum(n, 1), np.nan)
        return m, m2, n

    def hod(self, s, q, D):
        n = self.n24[s, q] - self.n24[s, q - 24 * D]
        return np.where(n > 0, (self.c24[s, q] - self.c24[s, q - 24 * D]) / np.maximum(n, 1), np.nan)


def panel_feats(P, s, c, tt, pre, full=True):
    cp = c + P_PAD
    F = {}
    for W in (WINS if full else (6, 24, 168)):
        m, m2, n = P.win(s, cp - W, cp)
        F[f"{pre}m{W}"] = m
        if W in (24, 168):
            F[f"{pre}sd{W}"] = np.sqrt(np.maximum(m2 - m ** 2, 0))
    li = P.last_idx[s, cp - 1]
    F[pre + "last"] = np.where(li >= 0, P.V[s, np.maximum(li, 0)], np.nan)
    F[pre + "age"] = np.where(li >= 0, cp - 1 - li, 9999)
    q = cp - 24 + (tt - c) % 24  # latest same-hour-of-day slot before the cutoff
    for D in (HODS if full else (1, 7)):
        F[f"{pre}hod{D}"] = P.hod(s, q, D)
    if full:
        wk = tt + P_PAD - 168
        F[pre + "wk"] = np.where(wk < cp, P.V[s, np.minimum(wk, cp - 1)], np.nan)
        F[pre + "trend"] = F[pre + "m24"] - F[pre + "m168"]
    return F


def calendar_feats(t):
    t = pd.DatetimeIndex(t)
    th = t.values.astype("datetime64[h]")
    i = np.clip(np.searchsorted(DIWALI, th), 1, len(DIWALI) - 1)
    d0 = (th - DIWALI[i - 1]).astype(float) / 24
    d1 = (th - DIWALI[i]).astype(float) / 24
    dd = np.where(np.abs(d0) < np.abs(d1), d0, d1)
    doy = t.dayofyear.values
    return {
        "hour": t.hour.values, "dow": t.dayofweek.values, "month": t.month.values,
        "doy_s": np.sin(2 * np.pi * doy / 365.25), "doy_c": np.cos(2 * np.pi * doy / 365.25),
        "diwali_dd": np.clip(dd, -45, 45),
    }


# ----------------------------------------------------------------- context

class Ctx:
    def __init__(self, data_dir, augment=True):
        tr_raw = pd.read_csv(os.path.join(data_dir, "Train.csv"))
        te_raw = pd.read_csv(os.path.join(data_dir, "Test.csv"))
        ss = pd.read_csv(os.path.join(data_dir, "SampleSubmission.csv"))
        self.id_col = find_col(te_raw, ["ID"], "ID")
        self.sample = ss

        obs = clean_y(standardize(tr_raw))
        extra = load_additional(os.path.join(data_dir, "AdditionalHistory.zip"))
        extra = clean_y(extra) if len(extra) else extra
        test = standardize(te_raw, need_target=False)
        test["ID"] = te_raw[self.id_col].values

        self.stations = sorted(obs["station"].unique())
        unknown = set(test["station"]) - set(self.stations)
        if unknown:
            raise ValueError(f"test stations missing from train: {unknown}")
        x_st = sorted(extra["station"].unique()) if len(extra) else []

        t0 = min(obs["time"].min(), extra["time"].min() if len(extra) else obs["time"].min())
        t1 = max(obs["time"].max(), test["time"].max())
        self.times = pd.date_range(t0, t1, freq="h")
        self.T = len(self.times)

        def grid(df, sts):
            g = df.pivot_table(index="time", columns="station", values="y", aggfunc="mean")
            return g.reindex(index=self.times, columns=sts).to_numpy(float).T

        Yt = grid(obs, self.stations)
        Yx = grid(extra, x_st) if x_st else np.empty((0, self.T))
        self.S = len(self.stations)
        # training rows may come from the extra stations; scoring is target-only
        self.Y = np.vstack([Yt, Yx]) if augment else Yt
        self.train_names = self.stations + (x_st if augment else [])
        self.tp = Panel(self.Y)
        with np.errstate(all="ignore"):
            city = np.nanmean(np.vstack([Yt, Yx]), axis=0)[None, :]
        self.city = Panel(city)

        # cutoff for hour g = 1 + last hour < g with any target-station reading
        anyobs = ~np.isnan(Yt).all(0)
        last = np.maximum.accumulate(np.where(anyobs, np.arange(self.T), -1))
        self.cutoff_of = np.concatenate([[0], last[:-1] + 1])
        self.data_end = int(last[-1]) + 1
        self.test = test
        tt = self.times.get_indexer(test["time"])
        if (tt < 0).any():
            raise ValueError("test times not on the hourly grid")
        self.test_s = np.array([self.stations.index(x) for x in test["station"]])
        self.test_tt = tt
        self.test_c = self.cutoff_of[tt]
        print(f"train {obs['time'].min()} .. {obs['time'].max()} | {self.S} target + "
              f"{len(x_st)} extra stations | test {test['time'].min()} .. {test['time'].max()} "
              f"({len(test)} rows, horizons {(tt - self.test_c).min()}..{(tt - self.test_c).max()}h)")

    def features(self, s, c, tt):
        F = {"station": s, "h": tt - c, "cut_hour": self.times[c].hour.values}
        F.update(panel_feats(self.tp, s, c, tt, "s_"))
        F.update(panel_feats(self.city, np.zeros_like(s), c, tt, "c_", full=False))
        F.update(calendar_feats(self.times[tt]))
        X = pd.DataFrame(F)
        X["s_rel"] = X["s_m168"] / X["c_m168"]
        X["station"] = X["station"].astype("category")
        return X

    def samples(self, h_max, step, n_far, rng, end=None):
        """Training rows: cutoffs every `step` hours, all short horizons plus
        `n_far` random longer ones, keeping only observed targets before `end`."""
        end = self.data_end if end is None else end
        cuts = np.arange(720, end, step)
        S = self.Y.shape[0]
        s = np.repeat(np.arange(S), len(cuts))
        c = np.tile(cuts, S)
        near = np.arange(min(PUBLIC_H, h_max))
        hs = [np.broadcast_to(near, (len(s), len(near)))]
        if h_max > PUBLIC_H and n_far:
            hs.append(rng.integers(PUBLIC_H, h_max, size=(len(s), n_far)))
        h = np.hstack(hs)
        s = np.repeat(s, h.shape[1])
        c = np.repeat(c, h.shape[1])
        tt = c + h.ravel()
        ok = tt < end
        s, c, tt = s[ok], c[ok], tt[ok]
        ok = ~np.isnan(self.Y[s, tt])
        return s[ok], c[ok], tt[ok]


# ------------------------------------------------------------------ models

LGB_PARAMS = dict(
    objective="regression", learning_rate=0.03, num_leaves=63, min_data_in_leaf=200,
    feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0,
    seed=SEED, deterministic=True, num_threads=os.cpu_count(), verbose=-1,
)


def fit_predict(X, y, Xp, rounds):
    preds = {}
    m = lgb.train(LGB_PARAMS, lgb.Dataset(X, y), rounds)
    preds["lgb"] = m.predict(Xp)
    ml = lgb.train(LGB_PARAMS, lgb.Dataset(X, np.log1p(y)), rounds)
    # expm1 of a log-space fit estimates the median; rescale to the mean for RMSE
    k = y.mean() / np.expm1(ml.predict(X)).mean()
    preds["lgb_log"] = np.expm1(ml.predict(Xp)) * k
    preds["blend"] = 0.5 * preds["lgb"] + 0.5 * preds["lgb_log"]
    imp = pd.Series(m.feature_importance("gain"), index=X.columns).sort_values(ascending=False)
    return {k: np.clip(v, 0, None) for k, v in preds.items()}, imp


def baselines(X):
    m24 = X["s_m24"].fillna(X["c_m24"])
    return {"persist24": m24.values, "hod7": X["s_hod7"].fillna(m24).values}


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


# --------------------------------------------------------------- commands

def fold_cutoffs(ctx, n_recent, h_long):
    """Recent weekly midnight cutoffs plus the same Oct-Nov season in past years."""
    end = ctx.times[ctx.data_end - 1].normalize()
    cuts = [end - pd.Timedelta(days=2 + 7 * k) for k in range(n_recent)]
    for y in sorted({t.year for t in ctx.times})[:-1]:
        for md in ("10-22", "11-01", "11-08"):
            cuts.append(pd.Timestamp(f"{y}-{md}"))
    idx = sorted({int(ctx.times.get_indexer([c])[0]) for c in cuts})
    return [i for i in idx if i > 24 * 120 and i + PUBLIC_H <= ctx.data_end]


def cmd_validate(ctx, a):
    rng = np.random.default_rng(SEED)
    h_max = max(int((ctx.test_tt - ctx.test_c).max()) + 1, PUBLIC_H)
    s, c, tt = ctx.samples(h_max, a.step, a.n_far, rng)
    X = ctx.features(s, c, tt)
    y = ctx.Y[s, tt]
    print(f"{len(X):,} training rows, {X.shape[1]} features, h_max={h_max}")
    rows, allp = [], []
    for cf in fold_cutoffs(ctx, a.folds, h_max):
        trm = tt < cf
        H = min(h_max, ctx.data_end - cf)
        vs = np.repeat(np.arange(ctx.S), H)
        vc = np.full(len(vs), cf)
        vt = vc + np.tile(np.arange(H), ctx.S)
        ok = ~np.isnan(ctx.Y[vs, vt])
        vs, vc, vt = vs[ok], vc[ok], vt[ok]
        if len(vs) < 24:
            continue
        Xv = ctx.features(vs, vc, vt)
        yv = ctx.Y[vs, vt]
        preds, _ = fit_predict(X[trm], y[trm], Xv, a.rounds)
        preds.update(baselines(Xv))
        df = pd.DataFrame(preds).assign(y=yv, h=vt - vc, fold=str(ctx.times[cf].date()))
        allp.append(df)
        near = df[df.h < PUBLIC_H]
        r = {"fold": str(ctx.times[cf].date()), "n": len(near)}
        r.update({k: rmse(near[k], near.y) for k in preds})
        rows.append(r)
        print("  " + "  ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in r.items()))
    res = pd.DataFrame(rows)
    P = pd.concat(allp)
    models = [k for k in res.columns if k not in ("fold", "n")]
    near, far = P[P.h < PUBLIC_H], P[P.h >= PUBLIC_H]
    summary = {
        "h<48 (public-like)": {m: rmse(near[m], near.y) for m in models},
        "h>=48 (long range)": {m: rmse(far[m], far.y) for m in models} if len(far) else {},
    }
    print("\nRMSE (pooled over folds)")
    print(pd.DataFrame(summary).round(3).to_string())
    os.makedirs(a.reports, exist_ok=True)
    res.to_csv(os.path.join(a.reports, "validation_folds.csv"), index=False)
    with open(os.path.join(a.reports, "validation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


def cmd_submit(ctx, a):
    rng = np.random.default_rng(SEED)
    h_max = max(int((ctx.test_tt - ctx.test_c).max()) + 1, PUBLIC_H)
    s, c, tt = ctx.samples(h_max, a.step, a.n_far, rng)
    X = ctx.features(s, c, tt)
    y = ctx.Y[s, tt]
    print(f"fitting on {len(X):,} rows")
    Xt = ctx.features(ctx.test_s, ctx.test_c, ctx.test_tt)
    preds, imp = fit_predict(X, y, Xt, a.rounds)
    pred = preds[a.model]
    sub = pd.DataFrame({"ID": ctx.test["ID"].values, "Target": pred})
    sub = ctx.sample[["ID"]].merge(sub, on="ID", how="left")
    assert sub["Target"].notna().all() and len(sub) == len(ctx.sample)
    os.makedirs(a.out_dir, exist_ok=True)
    out = os.path.join(a.out_dir, f"sub_{a.model}_{time.strftime('%Y%m%d_%H%M')}.csv")
    sub.to_csv(out, index=False)
    os.makedirs(a.reports, exist_ok=True)
    imp.to_csv(os.path.join(a.reports, "feature_importance.csv"))
    print(f"wrote {out}  (mean {sub.Target.mean():.2f}, min {sub.Target.min():.2f}, max {sub.Target.max():.2f})")
    print("top features:", ", ".join(imp.index[:10]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["validate", "submit"])
    p.add_argument("--data", default="data")
    p.add_argument("--out-dir", default="submissions")
    p.add_argument("--reports", default="reports")
    p.add_argument("--model", default="blend", choices=["lgb", "lgb_log", "blend"])
    p.add_argument("--rounds", type=int, default=600)
    p.add_argument("--step", type=int, default=6, help="hours between training cutoffs")
    p.add_argument("--n-far", type=int, default=16, help="random long horizons per cutoff")
    p.add_argument("--folds", type=int, default=6, help="recent weekly validation folds")
    p.add_argument("--no-augment", action="store_true", help="train on target stations only")
    a = p.parse_args()
    ctx = Ctx(a.data, augment=not a.no_augment)
    {"validate": cmd_validate, "submit": cmd_submit}[a.cmd](ctx, a)


if __name__ == "__main__":
    main()
