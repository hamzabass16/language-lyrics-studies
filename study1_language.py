"""Study 1: command of written language and later societal progress.
Follows PREREGISTRATION.md. Prints every number used in the write-up and saves figures.
"""
import json
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
import pycountry_convert as pc
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = "/home/claude/data/raw/owid/datasets"
OUT = "/home/claude/analysis/out"
R = {}

def load(name, cols):
    d = pd.read_csv(f"{D}/{name}/{name}.csv")
    d = d.iloc[:, :len(cols)]
    d.columns = cols
    return d

mad = load("Maddison Project Database 2020 (Bolt and van Zanden (2020))", ["c", "y", "gdppc", "pop", "gdp"])
hlo = load("Global Data Set on Education Quality (1965-2015) - Altinok, Angrist, and Patrinos (2018)", ["c", "y", "hlo"])
sch = load("Years of Schooling - based on Lee-Lee (2016), Barro-Lee (2018) and UNDP (2018)", ["c", "y", "school"])
lit = load("Cross-country literacy rates - World Bank, CIA World Factbook, and other sources", ["c", "y", "lit"])
le = load("Life expectancy - Riley (2005), Clio Infra (2015), and UN (2019)", ["c", "y", "le"])
books = load("Books - Buringh and Van Zanden (2009)", ["c", "y", "manus", "printed", "books_pc"])

def continent(name):
    try:
        return pc.country_alpha2_to_continent_code(pc.country_name_to_country_alpha2(name))
    except Exception:
        return None

def value_at(df, col, country, year, window=5):
    """closest observation to `year` within +/- window years"""
    s = df[(df.c == country) & (df.y.between(year - window, year + window))].dropna(subset=[col])
    if s.empty:
        return np.nan
    return s.iloc[(s.y - year).abs().argsort()].iloc[0][col]

madi = mad.dropna(subset=["gdppc"]).set_index(["c", "y"])["gdppc"]
def gdp(c, y):
    return madi.get((c, y), np.nan)

# ---------- S1-A: panel lead-lag with HLO ----------
rows = []
for _, r in hlo.dropna(subset=["hlo"]).iterrows():
    c, t = r.c, int(r.y)
    y0, y10, ym10 = gdp(c, t), gdp(c, t + 10), gdp(c, t - 10)
    rows.append({"c": c, "t": t, "hlo": r.hlo, "lny": np.log(y0) if y0 > 0 else np.nan,
                 "g_fwd": 100 * (np.log(y10) - np.log(y0)) / 10 if (y0 > 0 and y10 > 0) else np.nan,
                 "g_back": 100 * (np.log(y0) - np.log(ym10)) / 10 if (y0 > 0 and ym10 > 0) else np.nan,
                 "school": value_at(sch, "school", c, t)})
P = pd.DataFrame(rows)
P["cont"] = P.c.apply(continent)
# HLO 10 years later for the reverse test
hl = hlo.set_index(["c", "y"])["hlo"]
P["hlo_fwd_change"] = [hl.get((c, t + 10), np.nan) - h for c, t, h in zip(P.c, P.t, P.hlo)]
sd_hlo = P.hlo.std()
P["z"] = (P.hlo - P.hlo.mean()) / sd_hlo
R["hlo_sd_points"] = sd_hlo

def fit(formula, data, cluster="c"):
    d = data.dropna(subset=[v for v in ["g_fwd", "z", "lny", "school", "cont", "g_back", "hlo_fwd_change"] if v in formula])
    m = smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[cluster])[0]})
    return m, d

specs = {
    "A1_base": "g_fwd ~ z + lny + C(t)",
    "A2_school": "g_fwd ~ z + lny + school + C(t)",
    "A3_continent": "g_fwd ~ z + lny + school + C(t) + C(cont)",
    "A4_countryFE": "g_fwd ~ z + lny + school + C(t) + C(c)",
    "A0_school_only": "g_fwd ~ lny + school + C(t)",
}
R["S1A"] = {}
for k, f in specs.items():
    m, d = fit(f, P)
    out = {"n_obs": int(m.nobs), "n_countries": int(d.c.nunique()), "r2": m.rsquared}
    for v in ["z", "school", "lny"]:
        if v in m.params:
            out[v] = {"b": m.params[v], "se": m.bse[v], "p": m.pvalues[v],
                      "ci": list(m.conf_int().loc[v])}
    R["S1A"][k] = out

# reverse direction: does past growth predict later improvement in test scores?
m, d = fit("hlo_fwd_change ~ g_back + hlo + lny + C(t)", P)
R["S1A"]["reverse"] = {"n_obs": int(m.nobs), "n_countries": int(d.c.nunique()),
                       "g_back": {"b": m.params["g_back"], "se": m.bse["g_back"], "p": m.pvalues["g_back"]},
                       "note": "HLO points per 1 pp of past annual growth"}
# forward analogue in comparable units: growth (pp) per 10 HLO points
m, d = fit("g_fwd ~ hlo + lny + school + C(t)", P)
R["S1A"]["per10points"] = {"b10": 10 * m.params["hlo"], "se10": 10 * m.bse["hlo"], "p": m.pvalues["hlo"]}

# leave-one-continent-out stability
loo = {}
for ct in sorted(P.cont.dropna().unique()):
    m, d = fit("g_fwd ~ z + lny + school + C(t)", P[P.cont != ct])
    loo[ct] = {"b": m.params["z"], "p": m.pvalues["z"], "n": int(m.nobs)}
R["S1A"]["leave_one_continent_out"] = loo

# ---------- S1-B: literacy breadth circa 1980 ----------
rows = []
for c in lit.c.unique():
    L = value_at(lit, "lit", c, 1980)
    y80, y18 = gdp(c, 1980), gdp(c, 2018)
    l80, l18 = value_at(le, "le", c, 1980, 0), value_at(le, "le", c, 2018, 1)
    rows.append({"c": c, "lit": L, "lny80": np.log(y80) if y80 > 0 else np.nan,
                 "g": 100 * (np.log(y18) - np.log(y80)) / 38 if (y80 > 0 and y18 > 0) else np.nan,
                 "le80": l80, "dle": l18 - l80, "school80": value_at(sch, "school", c, 1980)})
B = pd.DataFrame(rows).dropna(subset=["lit", "g"])
B["cont"] = B.c.apply(continent)
B = B[B.cont.notna()]  # drop regional aggregates
R["S1B"] = {"n": len(B)}
for k, f in {"B1": "g ~ lit + lny80", "B2": "g ~ lit + lny80 + school80", "B3": "g ~ lit + lny80 + C(cont)",
             "B4_le": "dle ~ lit + le80 + lny80"}.items():
    d = B.dropna(subset=[v for v in ["g", "lit", "lny80", "school80", "dle", "le80"] if v in f])
    m = smf.ols(f, data=d).fit(cov_type="HC3")
    R["S1B"][k] = {"n": int(m.nobs), "lit_per10pp": {"b": 10 * m.params["lit"], "se": 10 * m.bse["lit"], "p": m.pvalues["lit"]},
                   "r2": m.rsquared}

# ---------- S1-C: books per capita, early modern Europe (exploratory) ----------
bk = books.dropna(subset=["books_pc"])
early = bk[bk.y.between(1475, 1625)].groupby("c").books_pc.mean()
MAP = {"Great Britain": "United Kingdom"}
madg = mad.dropna(subset=["gdppc"])
rows = []
for c, b in early.items():
    if c in ("Other countries", "Western Europe"):
        continue                                   # regional aggregates
    mc = MAP.get(c, c)
    rows.append({"c": c, "books": b,
                 "y1500": value_at(madg, "gdppc", mc, 1500, 20), "y1800": value_at(madg, "gdppc", mc, 1800, 20),
                 "y1870": value_at(madg, "gdppc", mc, 1870, 0)})
EB = pd.DataFrame(rows)
R["S1C_table"] = EB.round(3).to_dict("records")
from scipy import stats
cc = EB.dropna(subset=["y1500", "y1800"])
cc = cc.assign(g=100 * (np.log(cc.y1800) - np.log(cc.y1500)) / 300)
R["S1C"] = {"n_growth": len(cc)}
rho = stats.spearmanr(cc.books, cc.g)
R["S1C"].update({"spearman_books_growth1500_1800": rho.statistic, "p": rho.pvalue})
c2 = EB.dropna(subset=["y1870"])
rho2 = stats.spearmanr(c2.books, c2.y1870)
R["S1C"].update({"n_level1870": len(c2), "spearman_books_gdp1870": rho2.statistic, "p_1870": rho2.pvalue})

# ---------- S1-D (exploratory, not preregistered): Hanushek-Woessmann style long-run cross-section ----------
avg = hlo.dropna(subset=["hlo"]).groupby("c").hlo.mean()
rows = []
for c, h in avg.items():
    y70, y18 = gdp(c, 1970), gdp(c, 2018)
    rows.append({"c": c, "hlo": h, "lny70": np.log(y70) if y70 > 0 else np.nan,
                 "g": 100 * (np.log(y18) - np.log(y70)) / 48 if (y70 > 0 and y18 > 0) else np.nan,
                 "school70": value_at(sch, "school", c, 1970)})
X = pd.DataFrame(rows).dropna()
X["cont"] = X.c.apply(continent); X = X[X.cont.notna()]
X["z"] = (X.hlo - X.hlo.mean()) / X.hlo.std()
R["S1D"] = {}
for k, f in {"D1": "g ~ z + lny70 + school70", "D2": "g ~ z + lny70 + school70 + C(cont)"}.items():
    m = smf.ols(f, data=X).fit(cov_type="HC3")
    R["S1D"][k] = {"n": int(m.nobs), "z": {"b": m.params["z"], "se": m.bse["z"], "p": m.pvalues["z"]},
                   "school70": {"b": m.params["school70"], "p": m.pvalues["school70"]}, "r2": m.rsquared}

# ---------- Figures ----------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
C1, C2, C3 = "#1f4e79", "#c0504d", "#7f7f7f"
fig, ax = plt.subplots(2, 2, figsize=(7.2, 6.0))

def partial(ax_, d, y, x, ctrl, xl, yl, title, s=9):
    ry = smf.ols(f"{y} ~ {ctrl}", data=d).fit().resid; rx = smf.ols(f"{x} ~ {ctrl}", data=d).fit().resid
    ax_.scatter(rx, ry, s=s, color=C1, alpha=.55, lw=0)
    b = np.polyfit(rx, ry, 1); xs = np.linspace(rx.min(), rx.max(), 50); ax_.plot(xs, np.polyval(b, xs), color=C2, lw=1.6)
    ax_.set_xlabel(xl); ax_.set_ylabel(yl); ax_.set_title(title, loc="left", fontweight="bold")

partial(ax[0, 0], X, "g", "z", "lny70 + school70", "Mean test score 1970–2015 (SD), residual",
        "Growth 1970–2018 (pp/yr), residual", "a  Long-run cross-section")

a = ax[0, 1]
rows_ = [("Cross-section 1970–2018*", R["S1D"]["D1"]["z"]["b"], R["S1D"]["D1"]["z"]["se"], C3),
         ("Panel: base", R["S1A"]["A1_base"]["z"]["b"], R["S1A"]["A1_base"]["z"]["se"], C1),
         ("Panel: + schooling", R["S1A"]["A2_school"]["z"]["b"], R["S1A"]["A2_school"]["z"]["se"], C1),
         ("Panel: + continent FE", R["S1A"]["A3_continent"]["z"]["b"], R["S1A"]["A3_continent"]["z"]["se"], C1),
         ("Panel: country FE", R["S1A"]["A4_countryFE"]["z"]["b"], R["S1A"]["A4_countryFE"]["z"]["se"], C2)]
for i, (lab, b, se, col) in enumerate(rows_):
    a.errorbar(b, i, xerr=1.96 * se, fmt="o", color=col, ms=4, capsize=2)
a.axvline(0, color=C3, lw=.8, ls="--"); a.set_yticks(range(len(rows_))); a.set_yticklabels([r[0] for r in rows_], fontsize=8)
a.invert_yaxis(); a.set_xlabel("Growth (pp/yr) per 1 SD of test score")
a.set_title("b  Respecting timing", loc="left", fontweight="bold")

partial(ax[1, 0], B.dropna(subset=["g", "lit", "lny80"]), "g", "lit", "lny80", "Literacy c.1980 (pp), residual",
        "Growth 1980–2018 (pp/yr), residual", "c  Literacy breadth")

a = ax[1, 1]
d = EB.dropna(subset=["y1870"])
a.scatter(1000 * d.books, d.y1870 / 1000, s=18, color=C1)
short = {"Great Britain": "GB", "Netherlands": "NL", "Belgium": "BE", "Ireland": "IE", "Sweden": "SE", "Spain": "ES", "Poland": "PL"}
for _, r in d.iterrows():
    if r.c in short:
        a.annotate(short[r.c], (1000 * r.books, r.y1870 / 1000), fontsize=7, xytext=(4, 2), textcoords="offset points")
a.annotate("FR, DE, IT, CH", (31, 2.9), fontsize=7, xytext=(-10, -16), textcoords="offset points")
a.set_xlabel("Books per 1,000 people/yr, 1475–1625"); a.set_ylabel("GDP pc 1870 (k 2011 $)")
a.set_title("d  Early books, Europe", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(f"{OUT}/fig1_language.png", dpi=220)

json.dump(R, open(f"{OUT}/study1_results.json", "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=lambda x: round(float(x), 4)))
