# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

from TTS.api import TTS
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to(device)
tts.tts_to_file(text='Hello World.',
                file_path='tmp.wav',
                speaker_wav='XTTS-v2/samples/de_sample.wav',
                language='en')
