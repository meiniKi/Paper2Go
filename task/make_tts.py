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

def worker(working_dir, nr, title, text, config_dict):
    os.makedirs(working_dir)

    print(config_dict)

    if config_dict["TTS"]["tts_method"] == 'TTS_FISH':
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

        cmd = ['python', str(Path(config_dict["TTS_FISH"]["generate_py"]).absolute())]
        cmd += ['--text', text]
        cmd += ['--checkpoint-path', str(Path(config_dict["TTS_FISH"]["fishspeech_chkp_path"]).absolute())]
        cmd += ['--num-samples' , config_dict["TTS_FISH"]["num_samples"]]
        cmd += ['--top-p' , config_dict["TTS_FISH"]["top_p"]]
        cmd += ['--repetition-penalty' , config_dict["TTS_FISH"]["repetition_penalty"]]
        cmd += ['--temperature' , config_dict["TTS_FISH"]["temperature"]]
        cmd += ['--seed' , config_dict["TTS_FISH"]["seed"]]
        cmd += ['--chunk-length', config_dict["TTS_FISH"]["chunk_length"]]
        cmd += ['--compile']
        subprocess.run(cmd, cwd=working_dir)

        #TODO: voices

        cmd = ['python', str(Path(config_dict["TTS_FISH"]["inference_py"]).absolute())]
        cmd += ['-i' , working_dir/'codes_0.npy']
        cmd += ['--checkpoint-path', str(Path(config_dict["TTS_FISH"]["generator_pth"]).absolute())]
        subprocess.run(cmd, cwd=working_dir)
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        speaker_wav = str(Path(config_dict["TTS"]["voice"]).absolute()) if config_dict["TTS"]["voice"] is not "Default" \
                        else str(Path(config_dict["TTS_XTTSv2"]["default_voice"]).absolute())
        tts = TTS(config_dict["TTS_XTTSv2"]["MODEL"]).to(device)
        tts.tts_to_file(text=text,
                        file_path=working_dir/"fake.wav",
                        speaker_wav=speaker_wav,
                        language="en")

    AudioSegment.from_wav(working_dir/"fake.wav").export(working_dir/'..'/f'{nr}-{title}.mp3', format="mp3")
    shutil.rmtree(working_dir)


def do_make_tts(titles, script, odir, config_dict):
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
            worker(working_dir, i, title, text, config_dict)



