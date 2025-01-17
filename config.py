# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os

import streamlit as st
from io import StringIO
from pathlib import Path
from pydub import AudioSegment
import streamlit_nested_layout
from collections import namedtuple
from datetime import datetime
import time
from celery import Celery
from typing import List
from config_io import ConfigIO
from config_helper import ConfigHelper
class Config:

    tts_methods_lut = {"OpenAI API": "TTS_OPENAI", "Fish-Speech": "TTS_FISH", "XTTSv2": "TTS_XTTSv2"}

    slider_config_setup = namedtuple("SliderConfigSetup", "section key label type min max")
    checkbox_config_setup = namedtuple("CheckboxConfigSetup", "section key label")
    selectbox_config_setup = namedtuple("SelectboxConfigSetup", "section key label type options")
    input_config_setup = namedtuple("InputConfigSetup", "section key label")
    input_area_config_setup = namedtuple("InputConfigSetup", "section key label")

    config_sliders = { "TTS_FISH" :   [slider_config_setup("TTS_FISH", "num_samples", "Num. Samples", int, 1, 10),
                                       slider_config_setup("TTS_FISH", "top_p", "Top P", float, 0.0, 1.0),
                                       slider_config_setup("TTS_FISH", "repetition_penalty", "Repetition Penalty", float, 1.0, 1.9),
                                       slider_config_setup("TTS_FISH", "temperature", "Temperature", float, 0.0, 1.0),
                                       slider_config_setup("TTS_FISH", "seed", "Seed", int, 1, 1000),
                                       slider_config_setup("TTS_FISH", "chunk_length", "Chunk Length", int, 1, 1000)],
                       "TTS_XTTSv2" : [slider_config_setup("TTS_XTTSv2", "speed", "Speed", float, 0.1, 4.0)],
                       "TTS_OPENAI":  [slider_config_setup("TTS_OPENAI", "speed", "Speed", float, 0.5, 4.0)]
                     }

    config_checkboxes = { "TTS_FISH" :   [checkbox_config_setup("TTS_FISH", "compile", "Compile")],
                          "TTS_XTTSv2" : [checkbox_config_setup("TTS_XTTSv2", "split_sentences", "Split Sentence")]}
    
    config_selectboxes = { "TTS_XTTSv2" : [selectbox_config_setup("TTS_XTTSv2", "lang", "Language", List[str], ["de", "en"])] }

    config_inputboxes = { "TTS_XTTSv2" : [input_config_setup("TTS_XTTSv2", "emotion", "Emotion")],
                          "TTS_OPENAI" : [input_config_setup("TTS_OPENAI", "api_key", "API Key"),
                                          input_config_setup("TTS_OPENAI", "base_url", "Base URL"),
                                          input_config_setup("TTS_OPENAI", "model", "Model"),
                                          input_config_setup("TTS_OPENAI", "voice", "Voice")] }

    ollama_inputboxes = [input_config_setup("LISTENABLE", "model", "Ollama Model"),
                         input_config_setup("LISTENABLE", "host", "Ollama Host"),
                         input_config_setup("LISTENABLE", "filters", "Sections to ignore")]

    ollama_inputareas = [input_config_setup("LISTENABLE", "system_prompt", "System Prompt"),
                         input_config_setup("LISTENABLE", "user_prompt_template", "User Prompt")]


    def __init__(self, voices_dir:Path):
        self.voices_dir = voices_dir
        self.celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
        ConfigIO.load_config()

    def as_dict(self):
        return st.session_state["config"]
        
    @st.dialog("Upload your INI File")
    def config_upload_ini_dialog(self):
        uploaded_ini = st.file_uploader(
            label="Upload INI",
            type=["ini"],
            label_visibility="hidden")
        st.session_state.uploaded_ini = uploaded_ini
        if uploaded_ini is not None:
            with open('paper2go.ini', "wb") as f:
                f.write(uploaded_ini.getbuffer())
            del st.session_state.uploaded_ini
            ConfigIO.load_config()
            st.rerun()

    @st.dialog("Update your Ollama Settings and Prompts", width="large")
    def ollama_settings_prompts_dialog(self):
        st.caption("🚧 No check yet. Make sure the model is available.")
        ConfigHelper.make_text_inputs(self.ollama_inputboxes)
        ConfigHelper.make_text_ares(self.ollama_inputareas)

    @st.dialog("Record your voice")
    def voice_record(self):
        transcript = st.text_input("⚠️ First, write what you are going to say", placeholder="Type here and press Enter...")
        tts_voice_record = st.audio_input("Record a voice", label_visibility="hidden")
        if tts_voice_record:
            os.makedirs(self.voices_dir, exist_ok=True)
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(self.voices_dir / (filename + ".wav"), 'wb') as f:
                f.write(tts_voice_record.getbuffer())
            with open(self.voices_dir / (filename + ".txt"), 'w') as f:
                f.write(transcript)
            
            task_convert = self.__encode_reference(
                str(self.voices_dir / (filename + ".wav")),
                str(self.voices_dir / (filename + ".npy")),
                self.as_dict())
            if task_convert is None:
                st.error("Cannot convert.")
            st.success(f"Voice successfully saved as {filename}")
            st.rerun()

    def __tts_label_to_section(label_txt):
        return Config.tts_methods_lut[label_txt]
    
    def __tts_section_to_label(section_txt):
        return dict((v,k) for k,v in Config.tts_methods_lut.items())[section_txt]
    
    def __clear_voices(self):
        for filename in os.listdir(self.voices_dir):
            file_path = self.voices_dir / filename
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
        st.rerun()

    def __encode_reference(self, ifile, ofile, config_dict):
        return self.celery_app.send_task('tasks.encode_reference', args=[ifile, ofile, config_dict])


    def update_voice_transcript(self, voice_selection):
        if os.path.isfile(self.voices_dir / (voice_selection + ".txt")):
            with open(self.voices_dir / (voice_selection + ".txt"), "w") as f:
                f.write(st.session_state["voice_transcript_text"])

    def config_ui(self):
        with st.sidebar:
            st.title("Settings")

            with st.expander("💾 Store / Restore"):
                if st.button("⚙️ Restore Defaults"):
                    ConfigIO.load_config(defaults=True)

                with open(ConfigIO.config_path, "rb") as file:
                    st.download_button(
                        label="💾 Download Config",
                        data=file,
                        file_name='config.ini',
                        mime='text/plain'
                    )

                if "config_upload_ini_dialog" not in st.session_state:
                    if st.button("📁 Upload Config INI"):
                        self.config_upload_ini_dialog()

            with st.expander("Basic Settings", expanded=True):
                st.radio("Select method for TTS 👇",
                            Config.tts_methods_lut.keys(), 
                            index=list(Config.tts_methods_lut.values()).index(
                                st.session_state["config"]["TTS"]["tts_method"]),
                            key="TTS/tts_method",
                            on_change=ConfigHelper.update_config,
                            args=["TTS/tts_method", Config.__tts_label_to_section]
                )
                st.markdown("OpenAI with local OpenedAI-Speech is fastest in default.")

            with st.expander("Voice Cloning"):
                st.markdown("Only for Fish-Speech & XTTS")
                tts_voice_upload = st.file_uploader(
                                label="Voice sample",
                                type=["mp3", "wav"])

                if tts_voice_upload is not None:
                    with open(self.voices_dir/tts_voice_upload.name, "wb") as f:
                        f.write(tts_voice_upload.getbuffer())
                        if tts_voice_upload.type != "wav":
                            f = Path(self.voices_dir/tts_voice_upload).absolute()
                            AudioSegment.from_wav(f).export(f.with_suffix('.wav'), format="wav")

                if "voice_record" not in st.session_state:
                    if st.button("🎤 Record Voice", use_container_width=True):
                        self.voice_record()

                voice_selection = st.selectbox(
                    label="Select Voice to use",
                    options=["Default"] + list({str(file.stem) for file in Path(self.voices_dir).rglob('*.wav') if file.is_file()}),
                    key="TTS/voice",
                    on_change=ConfigHelper.update_config,
                    args=["TTS/voice", lambda x: self.voices_dir/x]
                )

                if voice_selection != "Default":
                    audio_file_path = self.voices_dir / (voice_selection + ".wav")
                    with open(audio_file_path, 'rb') as f:
                        audio_data = f.read()
                    st.audio(audio_data, format='audio/wav', start_time=0)

                    transcript_text = ""
                    if os.path.isfile(self.voices_dir / (voice_selection + ".txt")):
                        with open(self.voices_dir / (voice_selection + ".txt"), "r") as f:
                            transcript_text = ' '.join(f.readlines())
                    st.text_input(
                        label="Voice Transcript",
                        value=transcript_text,
                        key="voice_transcript_text",
                        on_change=self.update_voice_transcript,
                        args=[voice_selection]
                    )

                if st.button("🗑️ Clear Voices", use_container_width=True):
                    self.__clear_voices()

            with st.expander("Advanced TTS Settings", expanded=True):
                if "ollama_settings_prompts_dialog" not in st.session_state:
                    if st.button("⚙️ Ollama Settings, Prompts & Filters", use_container_width=True):
                        self.ollama_settings_prompts_dialog()
                for expander in Config.config_sliders.keys():
                    with st.expander(Config.__tts_section_to_label(expander)):
                        if expander in Config.config_sliders:
                            ConfigHelper.make_sliders(Config.config_sliders[expander])
                        if expander in Config.config_checkboxes:
                            ConfigHelper.make_checkboxes(Config.config_checkboxes[expander])
                        if expander in Config.config_selectboxes:
                            ConfigHelper.make_selectboxes(Config.config_selectboxes[expander])
                        if expander in Config.config_inputboxes:
                            ConfigHelper.make_text_inputs(Config.config_inputboxes[expander])

