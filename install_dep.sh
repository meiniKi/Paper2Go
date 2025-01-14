#!/bin/bash
git clone --branch "v2.4.0" --single-branch https://github.com/rhasspy/gruut gruut
cd gruut || exit
sed -i "s/"jsonlines~=1.2.0"/"jsonlines==3.1.0"/g" requirements.txt

pip install .[de,en,es,fr]
cd ..
rm -rf gruut
pip install -r requirements.txt

cd models/fish-speech
pip install -e .
cd ../..
