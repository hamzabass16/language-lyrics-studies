"""Study 2: lyrics per song, Billboard Year-End Hot 100, before 2000 vs after 2010.
Follows PREREGISTRATION.md. Prints every number used in the write-up and saves figures.
"""
import re, zlib, json
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW = "/home/claude/data/raw"
OUT = "/home/claude/analysis/out"
rng = np.random.default_rng(2026)
R = {}  # results collected for the write-up

# ---------- 1. Load the three sources ----------
zhao = pd.read_csv(f"{RAW}/repo_spotify-song-lyric-analysis/data/billboard-lyrics-spotify.csv")
walk = pd.read_csv(f"{RAW}/billboard_1964_2015.csv", encoding="latin-1").rename(
    columns={"Lyrics": "lyrics", "Year": "year", "Song": "song", "Artist": "artist_all", "Rank": "rank"})
hid = pd.read_csv(f"{RAW}/repo_Hidden-Hits/hot_100_with_lyrics.csv").rename(
    columns={"title": "song", "artists": "artist_all"})

# ---------- 2. One tokenizer for every source ----------
TAG = re.compile(r"\[[^\]]*\]")          # section labels like [Chorus]
WORD = re.compile(r"[a-z']+")

def tokens(text):
    if not isinstance(text, str):
        return []
    return [w for w in WORD.findall(TAG.sub(" ", text.lower())) if w.strip("'")]

def song_measures(text):
    t = tokens(text)
    n = len(t)
    if n == 0:
        return pd.Series({"words": 0, "unique": 0, "compress": np.nan, "mattr": np.nan})
    joined = " ".join(t).encode()
    compress = len(zlib.compress(joined, 9)) / len(joined)     # lower = more repetitive
    win = 50                                                    # moving-average type-token ratio
    mattr = np.mean([len(set(t[i:i + win])) / win for i in range(0, n - win + 1)]) if n >= win else np.nan
    return pd.Series({"words": n, "unique": len(set(t)), "compress": compress, "mattr": mattr})

for d in (zhao, walk, hid):
    d[["words", "unique", "compress", "mattr"]] = d["lyrics"].apply(song_measures)

def clean(d):
    return d[d["words"] >= 20].copy()

R["n_raw"] = {"zhao": len(zhao), "walker": len(walk), "hidden": len(hid)}
zhao, walk, hid = clean(zhao), clean(walk), clean(hid)
R["n_clean"] = {"zhao": len(zhao), "walker": len(walk), "hidden": len(hid)}

def period(y):
    return "PRE" if 1965 <= y <= 1999 else ("POST" if 2010 <= y <= 2015 else ("POSTX" if y in (2016, 2017) else None))

# ---------- 3. Primary test ----------
def compare(d, col, post_years=(2010, 2015), pre_years=(1965, 1999), label=""):
    pre = d[d.year.between(*pre_years)][col].dropna().values
    post = d[d.year.between(*post_years)][col].dropna().values
    diff = post.mean() - pre.mean()
    boot = [rng.choice(post, len(post)).mean() - rng.choice(pre, len(pre)).mean() for _ in range(10000)]
    t = stats.ttest_ind(post, pre, equal_var=False)
    u = stats.mannwhitneyu(post, pre, alternative="two-sided")
    sp = np.sqrt(((len(pre) - 1) * pre.var(ddof=1) + (len(post) - 1) * post.var(ddof=1)) / (len(pre) + len(post) - 2))
    return {"label": label, "col": col, "n_pre": len(pre), "n_post": len(post),
            "mean_pre": pre.mean(), "mean_post": post.mean(), "median_pre": np.median(pre), "median_post": np.median(post),
            "diff": diff, "ci": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "pct": 100 * diff / pre.mean(), "t": t.statistic, "p_t": t.pvalue, "p_u": u.pvalue, "d": diff / sp}

R["primary_zhao"] = compare(zhao, "words", label="Zhao 1965-99 vs 2010-15")
R["primary_walker"] = compare(walk, "words", label="Walker 1965-99 vs 2010-15")
R["zhao_ext"] = compare(zhao, "words", post_years=(2010, 2017), label="Zhao 1965-99 vs 2010-17")
R["zhao_90s"] = compare(zhao, "words", pre_years=(1990, 1999), post_years=(2010, 2017), label="Zhao 1990-99 vs 2010-17")
R["walker_90s"] = compare(walk, "words", pre_years=(1990, 1999), label="Walker 1990-99 vs 2010-15")
R["zhao_2000s"] = compare(zhao, "words", pre_years=(2000, 2009), post_years=(2010, 2017), label="Zhao 2000-09 vs 2010-17")

# Agreement between the two scrapes on the same songs
key = lambda d: d["song"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + "_" + d["year"].astype(str)
zhao["k"], walk["k"] = key(zhao), key(walk)
m = zhao.merge(walk[["k", "words"]], on="k", suffixes=("_z", "_w"))
R["source_agreement"] = {"n_matched": len(m), "r_words": stats.pearsonr(m.words_z, m.words_w)[0],
                         "median_ratio_w_over_z": float(np.median(m.words_w / m.words_z))}

# Hidden-Hits (Genius) calibration on overlap 2010-2017, then 2018-2020 extension
hid["k"] = key(hid)
mh = zhao.merge(hid[["k", "words"]], on="k", suffixes=("_z", "_h"))
ratio = float(np.median(mh.words_h / mh.words_z))
hid["words_cal"] = hid["words"] / ratio
R["genius_calibration"] = {"n_overlap": len(mh), "median_ratio_genius_over_zhao": ratio,
                           "r": stats.pearsonr(mh.words_z, mh.words_h)[0]}
R["genius_2018_20_calibrated_mean"] = float(hid[hid.year.between(2018, 2020)]["words_cal"].mean())
R["genius_2010_17_calibrated_mean"] = float(hid[hid.year.between(2010, 2017)]["words_cal"].mean())

# ---------- 4. Mechanisms (Zhao, Spotify features) ----------
z = zhao.copy()
z["rap"] = (z["speechiness"] >= 0.33).astype(int)
z["wps"] = z["words"] / (z["duration_min"] * 60)
z = z[(z.duration_min > 1) & (z.duration_min < 12)]  # drop extended or broken durations
z["P"] = z.year.apply(period)
zz = z[z.P.isin(["PRE", "POST", "POSTX"])].copy()
zz["post"] = zz.P.isin(["POST", "POSTX"]).astype(int)  # POST = 2010-2017 here

mech = {}
for col in ["duration_min", "wps", "unique", "compress", "mattr", "energy", "tempo", "speechiness", "rap"]:
    mech[col] = compare(zz.rename(columns={}), col, post_years=(2010, 2017), label=col)
R["mechanisms"] = mech

# rap share and words within type
R["rap_share"] = {"pre": zz[zz.post == 0].rap.mean(), "post": zz[zz.post == 1].rap.mean()}
R["words_by_type"] = zz.groupby(["post", "rap"])["words"].agg(["mean", "count"]).reset_index().to_dict("records")
R["within_nonrap"] = compare(zz[zz.rap == 0], "words", post_years=(2010, 2017), label="non-rap only")
R["within_rap"] = compare(zz[zz.rap == 1], "words", post_years=(2010, 2017), label="rap only")

# Oaxaca-Blinder twofold (pooled coefficients), single regressor: rap
pre, post = zz[zz.post == 0], zz[zz.post == 1]
pooled = smf.ols("words ~ rap", data=zz).fit()
gap = post.words.mean() - pre.words.mean()
explained = pooled.params["rap"] * (post.rap.mean() - pre.rap.mean())
R["oaxaca"] = {"gap": gap, "explained_by_rap_share": explained, "share_explained": explained / gap}

# regression with HC3
ols = smf.ols("words ~ post * rap", data=zz).fit(cov_type="HC3")
R["ols_post_rap"] = {k: {"b": ols.params[k], "se": ols.bse[k], "p": ols.pvalues[k]} for k in ols.params.index}
ols2 = smf.ols("words ~ post + speechiness + duration_min", data=zz).fit(cov_type="HC3")
R["ols_controls"] = {k: {"b": ols2.params[k], "se": ols2.bse[k], "p": ols2.pvalues[k]} for k in ols2.params.index}
# duration-adjusted: words per second as the outcome removes the length channel
R["words_per_minute_pre_post"] = {"pre": 60 * pre.wps.mean(), "post": 60 * post.wps.mean()}

# ---------- 4b. Genre from Last.fm tags (third source, Schaich) ----------
import glob
rows = []
for f in glob.glob(f"{RAW}/repo_billboard/data/years/*.json"):
    rows += json.load(open(f))
sch = pd.DataFrame(rows)
sch["year"] = sch["year"].astype(int)
sch = sch.rename(columns={"title": "song"})
HH = r"'(?:rap|hip[- ]?hop|hip hop|gangsta rap|southern rap|dirty south|trap|crunk|east coast rap|west coast rap)'"
sch["hiphop"] = sch["tags"].astype(str).str.lower().str.contains(HH).astype(int)
sch[["words", "unique", "compress", "mattr"]] = sch["lyrics"].apply(song_measures)
sch = clean(sch)
R["n_clean"]["schaich"] = len(sch)
R["primary_schaich"] = compare(sch, "words", label="Schaich 1965-99 vs 2010-15")
R["hiphop_share_schaich"] = {"pre": sch[sch.year.between(1965, 1999)].hiphop.mean(),
                             "post": sch[sch.year.between(2010, 2015)].hiphop.mean()}

# attach the genre tag to Zhao songs, then decompose with a real genre label
sch["k"] = key(sch)
zg = zz.merge(sch[["k", "hiphop"]], on="k", how="inner")
R["n_zhao_with_genre"] = len(zg)
pre_g, post_g = zg[zg.post == 0], zg[zg.post == 1]
gap_g = post_g.words.mean() - pre_g.words.mean()
pooled_g = smf.ols("words ~ hiphop", data=zg).fit()
expl_g = pooled_g.params["hiphop"] * (post_g.hiphop.mean() - pre_g.hiphop.mean())
R["oaxaca_genre"] = {"gap": gap_g, "explained_by_hiphop_share": expl_g, "share_explained": expl_g / gap_g,
                     "hiphop_pre": pre_g.hiphop.mean(), "hiphop_post": post_g.hiphop.mean(),
                     "hiphop_coef": pooled_g.params["hiphop"]}
# Oaxaca with both group-specific coefficients (post-period weights) as a check
b_post = smf.ols("words ~ hiphop", data=post_g).fit().params
b_pre = smf.ols("words ~ hiphop", data=pre_g).fit().params
R["oaxaca_genre_alt"] = {"explained_pre_weights": b_pre["hiphop"] * (post_g.hiphop.mean() - pre_g.hiphop.mean()),
                         "explained_post_weights": b_post["hiphop"] * (post_g.hiphop.mean() - pre_g.hiphop.mean())}
R["within_non_hiphop"] = compare(zg[zg.hiphop == 0], "words", post_years=(2010, 2017), label="non-hip-hop (tags)")
R["within_hiphop"] = compare(zg[zg.hiphop == 1], "words", post_years=(2010, 2017), label="hip-hop (tags)")
R["within_non_hiphop_wps"] = compare(zg[zg.hiphop == 0], "wps", post_years=(2010, 2017), label="non-hip-hop wps")
R["within_non_hiphop_duration"] = compare(zg[zg.hiphop == 0], "duration_min", post_years=(2010, 2017), label="non-hip-hop duration")
R["within_non_hiphop_compress"] = compare(zg[zg.hiphop == 0], "compress", post_years=(2010, 2017), label="non-hip-hop compress")
ols3 = smf.ols("words ~ post + hiphop + duration_min", data=zg).fit(cov_type="HC3")
R["ols_genre_controls"] = {k: {"b": ols3.params[k], "se": ols3.bse[k], "p": ols3.pvalues[k]} for k in ols3.params.index}
# decade trajectory for the main figure
dec = zhao[zhao.year >= 1960].groupby(zhao.year // 10 * 10)["words"].agg(["mean", "median", "count"])
R["zhao_decades"] = dec.reset_index().to_dict("records")
dec_w = walk.groupby(walk.year // 10 * 10)["words"].agg(["mean", "count"])
R["walker_decades"] = dec_w.reset_index().to_dict("records")

# ---------- 5. Figures ----------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
C1, C2, C3 = "#1f4e79", "#c0504d", "#7f7f7f"

def yearly(d, col):
    g = d.groupby("year")[col]
    return g.mean(), 1.96 * g.std() / np.sqrt(g.count())

fig, ax = plt.subplots(2, 2, figsize=(7.2, 5.6))
a = ax[0, 0]
for d, c, lab in [(zhao, C1, "Source 1 (Zhao)"), (walk, C2, "Source 2 (Walker)")]:
    mu, ci = yearly(d[d.year >= 1965], "words")
    a.plot(mu.index, mu, color=c, lw=1.4, label=lab); a.fill_between(mu.index, mu - ci, mu + ci, color=c, alpha=.15, lw=0)
a.axvspan(1965, 1999.5, color=C3, alpha=.07); a.axvspan(2009.5, 2017, color=C2, alpha=.07)
a.set_ylabel("Words per song"); a.set_title("a  Words per Year-End Hot 100 song", loc="left", fontweight="bold"); a.legend(frameon=False, fontsize=7)

a = ax[0, 1]
bins = range(1965, 2016, 5)  # genre tags end in 2015; last full bin 2010-14
s2 = sch[sch.year >= 1965].groupby(pd.cut(sch[sch.year >= 1965].year, bins, right=False))["hiphop"].mean()
a.bar([iv.left + 2 for iv in s2.index], 100 * s2.values, width=4, color=C1)
a.set_ylabel("Hip-hop / rap tagged (%)"); a.set_title("b  Hip-hop share of hits", loc="left", fontweight="bold")

a = ax[1, 0]
zall = z.merge(sch[["k", "hiphop"]], on="k", how="inner")
for r_, c, lab in [(0, C1, "Not hip-hop"), (1, C2, "Hip-hop / rap")]:
    sub = zall[(zall.hiphop == r_) & (zall.year >= 1965)]
    g = sub.groupby(pd.cut(sub.year, bins, right=False))["words"].agg(["mean", "count"])
    g = g[g["count"] >= 5]
    a.plot([iv.left + 2 for iv in g.index], g["mean"].values, marker="o", ms=3, color=c, lw=1.4, label=lab)
a.set_ylabel("Words per song"); a.set_title("c  Words by genre", loc="left", fontweight="bold"); a.legend(frameon=False, fontsize=7)

a = ax[1, 1]
mu, ci = yearly(z[z.year >= 1965], "duration_min")
a.plot(mu.index, mu, color=C1, lw=1.4, label="Duration (min)")
a2 = a.twinx(); mu2, _ = yearly(z[z.year >= 1965], "compress")
a2.plot(mu2.index, mu2, color=C2, lw=1.4, label="Compression ratio")
a.set_ylabel("Duration (min)", color=C1); a2.set_ylabel("Compression (low = repetitive)", color=C2)
a2.spines["top"].set_visible(False)
a.set_title("d  Length and repetition", loc="left", fontweight="bold")
for a in ax.flat: a.set_xlabel("Chart year")
fig.tight_layout(); fig.savefig(f"{OUT}/fig2_lyrics.png", dpi=220)

json.dump(R, open(f"{OUT}/study2_results.json", "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=lambda x: round(float(x), 4)))
