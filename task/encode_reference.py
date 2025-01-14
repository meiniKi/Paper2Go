# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import subprocess
from pathlib import Path


def do_encode_reference(ifile, ofile, config_dict):
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

    cmd = ['python', str(Path(config_dict["TTS_FISH"]["inference_py"]).absolute())]
    cmd += ['-i', ifile]
    cmd += ['--checkpoint-path', str(Path(config_dict["TTS_FISH"]["generator_pth"]).absolute())]
    
    try:
        subprocess.run(cmd, cwd=str(Path(ifile).parent))
    except subprocess.CalledProcessError as e:
        return None

    os.rename(Path(ifile).parent / "fake.npy", ofile)
    return {"status": "complete"}
