# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import configparser
import subprocess
from multiprocessing import Pool, Manager
import random
import shutil
from pydub import AudioSegment
from TTS.api import TTS
import torch
from pathlib import Path

def worker(method, config, working_dir, nr, title, text):
    os.makedirs(working_dir)

    if method == 'Fish-Speech':
        GENERATE_PY = str(Path(config.get('TTS_FISH','GENERATE_PY')).absolute())
        INFERENCE_PY = str(Path(config.get('TTS_FISH','INFERENCE_PY')).absolute())
        CHKP = str(Path(config.get('TTS_FISH','FISHSPEECH_CHKP_PATH')).absolute())
        GENERATOR_PTH = str(Path(config.get('TTS_FISH','GENERATOR_PTH')).absolute())

        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

        cmd = ['python', GENERATE_PY]
        cmd += ['--text', text]
        cmd += ['--checkpoint-path', CHKP]
        cmd += ['--num-samples' , '2']
        cmd += ['--compile']
        subprocess.run(cmd, cwd=working_dir)

        cmd = ['python', INFERENCE_PY]
        cmd += ['-i' , working_dir/'codes_0.npy']
        cmd += ['--checkpoint-path', GENERATOR_PTH]
        subprocess.run(cmd, cwd=working_dir)
    else:
        MODEL_XTTS = config.get('TTS_XTTSv2','MODEL')
        SPEAKER_WAV = config.get('TTS_XTTSv2','SPEAKER_WAV')
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts = TTS(MODEL_XTTS).to(device)
        tts.tts_to_file(text=text,
                        file_path=working_dir/"fake.wav",
                        speaker_wav=SPEAKER_WAV,
                        language="en")

    AudioSegment.from_wav(working_dir/"fake.wav").export(working_dir/'..'/f'{nr}-{title}.mp3', format="mp3")
    shutil.rmtree(working_dir)


def do_make_tts(titles, script, odir, method, bar):
    config = configparser.ConfigParser()
    config.read('paper2go.ini')
    length = len(script)
    
    if False:
        with Manager() as manager:
            with Pool(NR_WORKER) as pool:
                for i, (title, text) in enumerate(zip(titles, script)):
                    working_dir = odir / ("%x" % random.randrange(2 ** 32))
                    _ = pool.apply_async(worker, (working_dir, i, title, text))

                pool.close()
                pool.join()
    else:
        for i, (title, text) in enumerate(zip(titles, script)):
            working_dir = odir / ("%x" % random.randrange(2 ** 32))
            worker(method, config, working_dir, i, title, text)
            bar.progress(i/length)

