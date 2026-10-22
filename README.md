# Words, meaning and progress

Code for two empirical tests drawn from the notebook *Nemo vir est qui mundum non reddat meliorem* (Hamza Bassatne):

1. **Study 1, language and progress.** Does a society's command of its written language (literacy, harmonised test scores, early modern book production) predict its later economic growth and life-expectancy gains?
2. **Study 2, lyrics per song.** Do Billboard Year-End Hot 100 hits after 2010 contain more words than hits before 2000, and which mechanism (rap, song length, delivery density, repetition, energy) explains it?

The write-up is a Nature-format Google Doc held by the author. `PREREGISTRATION.md` is the analysis plan fixed before outcomes were computed; deviations are listed in the write-up's Methods.

## Main results

| Test | Result |
|---|---|
| Literacy c.1980 to growth 1980 to 2018 (71 countries) | +0.37 pp/yr per 10 pp literacy, P = 0.002; survives schooling and continent FE |
| Test scores to next-decade growth (panel, 128 countries) | 0.45 pp/yr per SD (P = 0.02), falls to 0.15 (P = 0.56) with continent FE and -0.10 within country |
| Words per hit, 1965 to 1999 vs 2010 to 2015 | 267 to 409 words (+53%, d = 1.08), replicated in 3 independent lyric sources |
| Timing | Peak in the 2000s (430 words), not after 2010 (412) |
| Share explained by hip-hop's rise | About 36% (range 17 to 41%) |
| Words per minute | 68 to 110 (+62%) |
| Repetition | Compression ratio -14% (more repetitive) |

## Run it

All commands run on a Mac or Linux machine with Python 3.11 or newer.

```bash
pip install -r requirements.txt
bash fetch_data.sh            # clones the public data sources into data/raw
python study2_lyrics.py       # writes out/study2_results.json and out/fig2_lyrics.png
python study1_language.py     # writes out/study1_results.json and out/fig1_language.png
```

The scripts expect the data in `/home/claude/data/raw`; change the `RAW` and `D` paths at the top of each script to `data/raw` and `data/raw/owid/datasets` if you run them elsewhere.

## Data sources (not redistributed here)

- Our World in Data datasets: github.com/owid/owid-datasets (Maddison 2020, Altinok-Angrist-Patrinos test scores, literacy, schooling, life expectancy, Buringh-van Zanden books)
- github.com/zhao1701/spotify-song-lyric-analysis (Billboard 1960 to 2017, lyrics + Spotify features)
- github.com/walkerkq/musiclyrics (Billboard 1965 to 2015)
- github.com/kevinschaich/billboard (Billboard to 2015, Last.fm tags)
- github.com/astromusicologist/Hidden-Hits (Billboard 2010 to 2020, Genius lyrics)

Lyrics are copyrighted and are not included in this repository; the scripts only compute counts from them.
