# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import streamlit as st
from datetime import datetime
from pathlib import Path
from celery import Celery
import pandas as pd
import numpy as np
from config import load_config, store_config, config_ui
from pipelines import pipeline_from_pdf, pipeline_from_text

config_dict = None

def unique_dir():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]

def text_tts_start_pipeline():
    working_dir = Path("data").absolute() / unique_dir()
    pipeline_from_text(st.session_state.tts_source_text, working_dir, config_dict)

def main():
    global config_dict

    st.set_page_config(page_title="Paper2Go")
    st.title("Paper2Go")
    app = Celery("tasks", broker="redis://localhost:6379/0")

    config_dict = load_config('paper2go.ini')

    tab_pdf, tab_text, tab_settings = st.tabs(["From PDF", "From Text", "Settings"])

    with tab_pdf:
        source_files = st.file_uploader("Select a pdf to convert.", accept_multiple_files=True, type=["pdf"])
        if st.button("Convert PDFs" if len(source_files) > 1 else "Convert PDF"):
            working_dir = Path("data").absolute() / unique_dir()
            pipeline_from_pdf(source_files, working_dir, config_dict)

    with tab_text:
        source_text = st.text_area("Type your script here", key="tts_source_text", on_change=text_tts_start_pipeline)

    with tab_settings:
        col_down, col_restore, col_up = st.columns([2,2,8])
        with col_down:
            st.download_button(
                label="Download",
                data=store_config(config_dict, stream=True),
                file_name='config.ini',
                mime='text/plain'
            )
        with col_up:
            with st.expander("Upload"):
                uploaded_ini = st.file_uploader(
                    label="Upload Config INI",
                    type=["ini"],
                    label_visibility="hidden")
                if uploaded_ini is not None:
                    with open('paper2go.ini', "wb") as f:
                        f.write(uploaded_ini.getbuffer())
        with col_restore:
            if st.button("Restore"):
                config_dict = load_config('paper2go_defaults.ini')

        config_ui(config_dict)
       
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
