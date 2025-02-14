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

    # Fish-Speed
    if config_dict["TTS"]["tts_method"] == 'TTS_FISH':
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

        cmd = ['python', str(Path(config_dict["TTS_FISH"]["generate_py"]).absolute())]
        cmd += ['--text', text]

        if os.path.isfile(config_dict["TTS"]["voice"] + ".txt") and os.path.isfile(config_dict["TTS"]["voice"] + ".wav"):
            with open(config_dict["TTS"]["voice"] + ".txt", "r") as f:
                cmd += ['--prompt-text', ' '.join(f.readlines())]
            cmd += ['--prompt-tokens', Path(config_dict["TTS"]["voice"] + ".npy").absolute()]

        cmd += ['--checkpoint-path', str(Path(config_dict["TTS_FISH"]["fishspeech_chkp_path"]).absolute())]
        cmd += ['--num-samples' , config_dict["TTS_FISH"]["num_samples"]]
        cmd += ['--top-p' , config_dict["TTS_FISH"]["top_p"]]
        cmd += ['--repetition-penalty' , config_dict["TTS_FISH"]["repetition_penalty"]]
        cmd += ['--temperature' , config_dict["TTS_FISH"]["temperature"]]
        cmd += ['--seed' , config_dict["TTS_FISH"]["seed"]]
        cmd += ['--chunk-length', config_dict["TTS_FISH"]["chunk_length"]]
    

        if config_dict["TTS_FISH"]["compile"] == "True":
            cmd += ['--compile']

        subprocess.run(cmd, cwd=working_dir)

        cmd = ['python', str(Path(config_dict["TTS_FISH"]["inference_py"]).absolute())]
        cmd += ['-i' , working_dir/'codes_0.npy']
        cmd += ['--checkpoint-path', str(Path(config_dict["TTS_FISH"]["generator_pth"]).absolute())]
        subprocess.run(cmd, cwd=working_dir)

    # XTTS
    elif config_dict["TTS"]["tts_method"] == 'TTS_XTTSv2':
        device = "cuda" if torch.cuda.is_available() else "cpu"

        speaker_wav = str(Path(config_dict["TTS"]["voice"]+".wav").absolute()) if config_dict["TTS"]["voice"].split("/")[-1] != "Default" \
                        else str((Path(config_dict["TTS_XTTSv2"]["default_voice"])).absolute())
        tts = TTS(config_dict["TTS_XTTSv2"]["model"]).to(device)

        tts.tts_to_file(text=text,
                        file_path=working_dir/"fake.wav",
                        speaker_wav=speaker_wav,
                        language=config_dict["TTS_XTTSv2"]["lang"],
                        emotion=config_dict["TTS_XTTSv2"]["emotion"],
                        speed=config_dict["TTS_XTTSv2"]["speed"],
                        split_sentences=(config_dict["TTS_XTTSv2"]["split_sentences"] == "True"))
    # OpenAI API
    else:
        import openai
        client = openai.OpenAI(
            api_key=config_dict["TTS_OPENAI"]["api_key"],
            base_url=config_dict["TTS_OPENAI"]["base_url"]
        )

        with client.audio.speech.with_streaming_response.create(
            model=config_dict["TTS_OPENAI"]["model"],
            voice=config_dict["TTS_OPENAI"]["voice"],
            speed=config_dict["TTS_OPENAI"]["speed"],
            response_format="mp3",
            input=text,
        ) as response:
            response.stream_to_file(working_dir/".."/f"{nr}-{title}.mp3")

    if not os.path.exists(working_dir/".."/f"{nr}-{title}.mp3"):
        AudioSegment.from_wav(working_dir/"fake.wav").export(working_dir/".."/f"{nr}-{title}.mp3", format="mp3")
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
            working_dir = Path(odir) / ("%x" % random.randrange(2 ** 32))
            worker(working_dir, i, title, text, config_dict)



