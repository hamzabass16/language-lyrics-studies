#!/usr/bin/env bash
# Step 1: make the data folder
set -e
mkdir -p data/raw && cd data/raw

# Step 2: Billboard lyrics, source 2 (Walker/Pavlik)
curl -sL -o billboard_1964_2015.csv \
  https://raw.githubusercontent.com/walkerkq/musiclyrics/master/billboard_lyrics_1964-2015.csv

# Step 3: Billboard lyrics, sources 1, 3 and 4
git clone -q --depth 1 https://github.com/zhao1701/spotify-song-lyric-analysis.git repo_spotify-song-lyric-analysis
git clone -q --depth 1 https://github.com/kevinschaich/billboard.git repo_billboard
git clone -q --depth 1 https://github.com/astromusicologist/Hidden-Hits.git repo_Hidden-Hits

# Step 4: Our World in Data, only the datasets the studies use
git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/owid/owid-datasets.git owid
cd owid
git sparse-checkout init --no-cone
git sparse-checkout set \
  "datasets/Maddison Project Database 2020 (Bolt and van Zanden (2020))/*" \
  "datasets/Global Data Set on Education Quality (1965-2015) - Altinok, Angrist, and Patrinos (2018)/*" \
  "datasets/Years of Schooling - based on Lee-Lee (2016), Barro-Lee (2018) and UNDP (2018)/*" \
  "datasets/Cross-country literacy rates - World Bank, CIA World Factbook, and other sources/*" \
  "datasets/Life expectancy - Riley (2005), Clio Infra (2015), and UN (2019)/*" \
  "datasets/Books - Buringh and Van Zanden (2009)/*"
git checkout -q
echo "Data ready in data/raw"
