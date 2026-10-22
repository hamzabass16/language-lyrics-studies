# Analysis plan, fixed before any outcome was computed (22 Oct 2026, 20:40 GST)

## Study 1. Command of written language and later societal progress
Journal hypothesis: "the quality of a language expressing the eternal self" is positively related to "the society that speaks that language's progress".

Operational definitions
- Language quality, breadth: adult literacy rate (OWID cross-country literacy series).
- Language quality, depth: harmonised learning outcome score (HLO; Altinok, Angrist & Patrinos 2018; reading, maths and science linked tests, 1970 to 2015).
- Language quality, historical written output: annual per-capita book consumption (Buringh & van Zanden 2009), Europe 1475 to 1775.
- Progress: annualised growth of real GDP per capita (Maddison Project 2020); secondary: gain in life expectancy (Riley / Clio Infra / UN).

Tests
- S1-A (primary, panel, lead-lag): country x 5-year panel 1970 to 2015. Outcome: annualised GDP pc growth over the next 10 years. Regressors: HLO at t (z-scored), log GDP pc at t, mean years of schooling at t, period fixed effects; country-clustered SEs. Robustness: continent FE; country FE (within-country); reverse-direction test (does GDP growth predict later HLO change, conditional on HLO at t).
- S1-B (literacy breadth): literacy circa 1980 (closest observation 1975 to 1985) predicting GDP pc growth 1980 to 2018 and life expectancy gain 1980 to 2018, controlling log GDP pc 1980 (and LE 1980), schooling 1980; HC3 SEs.
- S1-C (historical, exploratory, small N): mean book consumption per capita 1475 to 1625 vs GDP pc growth 1500 to 1800 and GDP pc level 1820, Europe.
Decision rule: H1 supported if the HLO coefficient in S1-A is positive with p < 0.05 and survives continent FE; the within-country and reverse tests are reported as limits on causal reading.

## Study 2. Lyrics per song before 2000 vs after 2010
Journal hypothesis: post-2010 hit songs carry more lyrics than pre-2000 hits (meaning delivered through direct words rather than melody), with rival explanations: social nonchalance, shorter attention span, shorter notes, dopamine, poetry-led music (rap).

Sample: Billboard Year-End Hot 100.
- Primary source: Zhao (1960 to 2017, lyrics + Spotify features).
- Independent replication: Walker/Pavlik (1965 to 2015, separate lyric scrape).
- Extension: Hidden-Hits Genius scrape (2010 to 2020), calibrated on overlapping songs; sensitivity only.
Windows: PRE = 1965 to 1999; POST = 2010 to 2015 (common to both main sources); extended POST = 2010 to 2017 (Zhao).
Word count: our own tokenizer on raw lyrics ([A-Za-z'] runs), identical across sources; songs with fewer than 20 tokens excluded (instrumental or failed scrape).

Primary test: difference in mean words per song, POST minus PRE: Welch t-test, Mann-Whitney U, bootstrap 95% CI (10,000 resamples), Cohen's d.
Mechanism tests (Zhao only, Spotify features):
- Rap / speech-led music: speechiness >= 0.33 (Spotify's threshold for speech-heavy tracks). Twofold Oaxaca-Blinder decomposition of the word gap into rap share vs within-type change.
- Attention span: track duration.
- Shorter notes / denser delivery: words per second.
- Loss of meaning vs more meaning: unique words per song and repetitiveness (zlib compression ratio; lower = more repetitive).
- Dopamine / energy: Spotify energy and tempo.
Decision rule: H2 supported if POST > PRE in mean words with p < 0.05 in both main sources.
