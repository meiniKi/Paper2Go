# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import configparser
import streamlit as st
from io import StringIO
from pathlib import Path
from pydub import AudioSegment

def load_config(file_path='paper2go.ini'):
    config = configparser.ConfigParser()
    config.read(file_path)
    return {section: dict(config.items(section)) for section in config.sections()}

def store_config(config_dict, file_path=None, stream=False):
    config = configparser.ConfigParser()
    for section in config_dict.keys():
        config.add_section(section)

    for section in config_dict.keys():
        section_dict = config_dict[section]
        fields = section_dict.keys()
        for field in fields:
            value = section_dict[field]
            config.set(section, field, str(value))

    if file_path is not None:
        with open(file_path, 'w') as file_path:
            config.write(file_path)

    if stream:
        output = StringIO()
        config.write(output)
        return output.getvalue()


def config_ui(config_dict):
    tts_method = st.radio("Select method for TTS 👇", ["Fish-Speech", "XTTSv2"], index=0)

    tts_voice_upload = st.file_uploader(
                    label="Voice sample",
                    type=["mp3", "wav"])
    
    if tts_voice_upload is not None:
        with open("voices"/tts_voice_upload.name, "wb") as f:
            f.write(tts_voice_upload.getbuffer())
            if tts_voice_upload.type != "wav":
                f = Path("voices"/tts_voice_upload).absolute()
                AudioSegment.from_wav(f).export(f.with_suffix('.wav'), format="wav")

    col_clear, col_select = st.columns([2, 12])
    with col_clear:
        if st.button("Clear"):
            for filename in os.listdir("voices"):
                file_path = os.path.join("voices", filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
    with col_select:
        tts_voice_select = st.selectbox(
            "Select Voice to use",
            ["Default"] + [str(file) for file in Path("voices").rglob('*') if file.is_file()]
        )

    col_xtts, col_fish = st.columns(2)

    # TODO: update dict and UI