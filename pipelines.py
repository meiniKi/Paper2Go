# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import streamlit as st
from tasks import *


def pipeline_from_pdf(file_list, working_dir, config):
    def update_spinner(file:int, of_files:int, step_name:str, step:int, of_steps:int):
        st.spinner(f"Processing File ({file}/{of_files}) Step {step_name} ({step}/{of_steps})")

    os.makedirs(working_dir, exist_ok=True)
    for i, file in enumerate(file_list):
        update_spinner(i, len(file_list, "PDF to Text Conversion", 1, 3))
        r = convert_to_markdown(file.getbuffer(), working_dir / "01_extracted.md", config)
        update_spinner(i, len(file_list, "Reformulation", 2, 3))
        r = make_listenable(r["markdown"], working_dir / "02_script.md", config)
        update_spinner(i, len(file_list, "Text-to-Speech", 3, 3))
        os.makedirs(working_dir / "audio" / f"{i}")
        r = make_tts(r["titles"], r["script"], working_dir / "audio" / f"{i}", config)

    st.spinner("Preparing Download...")
    r = archive(working_dir / "audio", working_dir / "audio.zip", config)
    with open(working_dir / "audio.zip", "rb") as file:
        st.download_button(
            label="Download Files",
            data=file,
            file_name=str(working_dir / "audio.zip"),
            mime="application/zip"
        )

def pipeline_from_text(source_text, working_dir, config):
    os.makedirs(working_dir, exist_ok=True)

    st.spinner(f"Processing...")
    r = make_tts(["tts"], [source_text], working_dir, config)
    st.audio(working_dir/"tts.mp3", format="audio/mpeg", loop=False)
