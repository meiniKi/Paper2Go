# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import streamlit as st
from datetime import datetime
from pathlib import Path
from celery import Celery
import pandas as pd
import numpy as np
from config import Config
from pipelines import pipeline_from_pdf, pipeline_from_text


class App():
    def __init__(self):
        self.config = Config(voices_dir=Path("voices").absolute())

    def main(self):
        st.set_page_config(page_title="Paper2Go")
        st.title("Paper2Go")
        app = Celery("tasks", broker="redis://localhost:6379/0")

        tab_pdf, tab_text = st.tabs(["From PDF", "From Text"])

        with tab_pdf:
            source_files = st.file_uploader("Select a pdf to convert.", accept_multiple_files=True, type=["pdf"])
            if st.button("Convert PDFs" if len(source_files) > 1 else "Convert PDF"):
                working_dir = Path("data").absolute() / self.unique_dir()
                pipeline_from_pdf(source_files, working_dir, self.config_dict)

        with tab_text:
            source_text = st.text_area("Type your script here", key="tts_source_text", on_change=self.text_tts_start_pipeline)


        self.config.config_ui()
            
        
        st.sidebar.title("About")
        st.sidebar.write("Paper2Go converts a PDF to Markdown, re-formulates it, synthesizes it into speech, and converts it to MP3 audio.")        
        self.footer()

    def unique_dir(self):
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]

    def text_tts_start_pipeline(self):
        working_dir = Path("data").absolute() / self.unique_dir()
        pipeline_from_text(st.session_state.tts_source_text, working_dir, self.config.as_dict())


    def footer(self):
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
    app = App()
    app.main()

