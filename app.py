# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import streamlit as st
from datetime import datetime
from tasks import *
from pathlib import Path
from celery import Celery


def unique_dir():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]

def main():
    st.set_page_config(page_title="Paper2Go")
    st.title("Paper2Go")
    app = Celery('tasks', broker='redis://localhost:6379/0')

    uploaded_file = st.file_uploader("Select a pdf to convert.", type=['pdf'])

    tts_method = st.radio("Select method for TTS 👇", ["Fish-Speech", "XTTSv2"], index=0)

    if uploaded_file is not None:
        working_dir = Path("data").absolute() / unique_dir()
        os.makedirs(working_dir, exist_ok=True)
        filepath = working_dir / uploaded_file.name

        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File {uploaded_file.name} uploaded successfully!")

        if st.button("Convert PDF"):
            steps = ["PDF to Text Conversion", "Reformulation", "Text-to-Speech", "ZIP"]
            # Step 1: PDF to text
            with st.spinner(f"Converting {steps[0]}..."):
                r = convert_to_markdown(filepath, working_dir / "01_extracted.md")
            st.write(f"Step 1 complete: {steps[0]}")
            # Step 2: Script
            with st.spinner(f"Scripting {steps[0]}..."):
                r = make_listenable(r["markdown"], working_dir / "02_script.md")
            st.write(f"Step 2 complete: {steps[1]}")
            # Step 3: TTS
            os.makedirs(working_dir / "audio")
            progress_bar = st.progress(0)
            with st.spinner(f"TTS {steps[0]}..."):
                r = make_tts(r['titles'], r['script'], working_dir / "audio", tts_method, progress_bar)
            st.write(f"Step 3 complete: {steps[2]}")
            progress_bar.progress(1)
            # Step 4: zip
            with st.spinner(f"TTS {steps[0]}..."):
                r = archive(working_dir / "audio", working_dir / "audio.zip")
            st.write(f"Step 4 complete: {steps[3]}")

            with open(working_dir / "audio.zip", "rb") as file:
                st.download_button(
                    label="Download Files",
                    data=file,
                    file_name=str(working_dir / "audio.zip"),
                    mime="application/zip"
                )

    st.sidebar.title("About")
    st.sidebar.write("Paper2Go converts a PDF to Markdown, re-formulates it, synthesizes it into speech, and converts it to MP3 audio.")        
    footer()

def footer():
    st.markdown(
        f"""
        <style>
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #0e1117;
            color: gray;
            text-align: center;
            padding: 10px 0;
        }}
        </style>
        
        <div class="footer">
            Developed with 🩶 by Meinhard Kissich
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
