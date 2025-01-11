# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

from pydub import AudioSegment

def do_convert_mp3(ifile, ofile):
    AudioSegment.from_wav(ifile).export(ofile, format="mp3")
    return {"status": "complete"}