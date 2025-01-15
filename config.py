# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import configparser
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

class Config:

    slider_config_setup = namedtuple("SliderConfigSetup", "section key label type min max")
    checkbox_config_setup = namedtuple("CheckboxConfigSetup", "section key label")
    selectbox_config_setup = namedtuple("SelectboxConfigSetup", "section key label type options")
    input_config_setup = namedtuple("InputConfigSetup", "section key label")

    config_sliders = { "Fish-Speech" : [slider_config_setup("TTS_FISH", "num_samples", "Num. Samples", int, 1, 10),
                                        slider_config_setup("TTS_FISH", "top_p", "Top P", float, 0.0, 1.0),
                                        slider_config_setup("TTS_FISH", "repetition_penalty", "Repetition Penalty", float, 1.0, 1.9),
                                        slider_config_setup("TTS_FISH", "temperature", "Temperature", float, 0.0, 1.0),
                                        slider_config_setup("TTS_FISH", "seed", "Seed", int, 1, 1000),
                                        slider_config_setup("TTS_FISH", "chunk_length", "Chunk Length", int, 1, 1000)],
                        "XTTSv2" : [slider_config_setup("TTS_XTTSv2", "speed", "Speed", float, 0.1, 4.0)]}

    config_checkboxes = {   "Fish-Speech" : [checkbox_config_setup("TTS_FISH", "compile", "Compile")],
                            "XTTSv2" : [checkbox_config_setup("TTS_XTTSv2", "split_sentences", "Split Sentence")]}
    
    config_selectboxes = {  "XTTSv2" : [selectbox_config_setup("TTS_XTTSv2", "lang", "Language", List[str], ["de", "en"])] }

    config_inputboxes = {  "XTTSv2" : [input_config_setup("TTS_XTTSv2", "emotion", "Emotion")] }


    def __init__(self, voices_dir:Path, config_path="paper2go.ini", config_defaults_path="paper2go_default.ini"):
        self.config_path = config_path
        self.config_defaults_path = config_defaults_path
        self.voices_dir = voices_dir
        self.celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
        self.load_config()

    def as_dict(self):
        return st.session_state["config"]
        
    def load_config(self, defaults=False):
        parser = configparser.ConfigParser()
        parser.read(self.config_path if not defaults else self.config_defaults_path)
        st.session_state["config"] = {section: dict(parser.items(section)) for section in parser.sections()}

    def store_config(self):
        self.__update_to_config_dict()
        parser = configparser.ConfigParser()
        for section in st.session_state["config"].keys():
            parser.add_section(section)

        for section in st.session_state["config"].keys():
            section_dict = st.session_state["config"][section]
            fields = section_dict.keys()
            for field in fields:
                value = section_dict[field]
                parser.set(section, field, str(value))

        if self.config_path is not None:
            with open(self.config_path, 'w') as f:
                parser.write(f)

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
            self.load_config()
            st.rerun()

    @st.dialog("Update your Ollama Settings and Prompts")
    def ollama_settings_prompts_dialog(self):
        st.caption("🚧 No test yet. Make sure the model is available.")
        model = st.text_input(
            "Ollama Model",
            value=st.session_state["config"]["LISTENABLE"]["model"]
        )
        host = st.text_input(
            "Ollama Host",
            value=st.session_state["config"]["LISTENABLE"]["host"]
        )
        filters = st.text_input(
            "Sections to filter",
            value=st.session_state["config"]["LISTENABLE"]["filters"]
        )
        sys_prompt = st.text_area(
            "System Prompt",
            value=st.session_state["config"]["LISTENABLE"]["system_prompt"]
        )
        user_prompt = st.text_area(
            "System Prompt",
            value=st.session_state["config"]["LISTENABLE"]["user_prompt_template"]
        )
        if st.button("✅ Apply"):
            st.session_state["config"]["LISTENABLE"]["model"] = model
            st.session_state["config"]["LISTENABLE"]["host"] = host
            st.session_state["config"]["LISTENABLE"]["filters"] = filters
            st.session_state["config"]["LISTENABLE"]["system_prompt"] = sys_prompt
            st.session_state["config"]["LISTENABLE"]["user_prompt_template"] = user_prompt
            self.store_config()
            st.rerun()

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

    def __tts_translate(self, label_txt):
        lut = {"Fish-Speech": "TTS_FISH", "XTTSv2": "TTS_XTTSv2"}
        return lut[label_txt]
    
    def __clear_voices(self):
        for filename in os.listdir(self.voices_dir):
            file_path = self.voices_dir / filename
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
        st.rerun()

    def __update_to_config_dict(self):
        st.session_state["config"]["TTS"]["tts_method"] = str(st.session_state.get(f"tts_method"))
        st.session_state["config"]["TTS"]["voice"] = str(self.voices_dir / st.session_state.get(f"voice_selection"))
        for s in sum(Config.config_sliders.values(), []):
            st.session_state["config"][s.section][s.key] = str(st.session_state.get(f"{s.section}_{s.key}"))
        for s in sum(Config.config_checkboxes.values(), []):
            st.session_state["config"][s.section][s.key] = str(st.session_state.get(f"{s.section}_{s.key}"))
        for s in sum(Config.config_selectboxes.values(), []):
            st.session_state["config"][s.section][s.key] = str(st.session_state.get(f"{s.section}_{s.key}"))
        for s in sum(Config.config_inputboxes.values(), []):
            st.session_state["config"][s.section][s.key] = st.session_state.get(f"{s.section}_{s.key}")

    def __encode_reference(self, ifile, ofile, config_dict):
        return self.celery_app.send_task('tasks.encode_reference', args=[ifile, ofile, config_dict])

    def config_ui(self):
        with st.sidebar:
            st.title("Settings")

            if st.button("✅ Don't forget to Save", use_container_width=True):
                self.store_config()

            with st.expander("💾 Store / Restore"):
                if st.button("⚙️ Restore Defaults"):
                    self.load_config(defaults=True)
                    print(st.session_state["config"])

                with open(self.config_path, "rb") as file:
                    st.download_button(
                        label="💾 Download Config",
                        data=file,
                        #on_click=self.store_config(), TODO: check why this is initially executed
                        file_name='config.ini',
                        mime='text/plain'
                    )

                if "config_upload_ini_dialog" not in st.session_state:
                    if st.button("📁 Upload Config INI"):
                        self.config_upload_ini_dialog()

            with st.expander("Basic Settings", expanded=True):
                tts_method = self.__tts_translate(st.radio("Select method for TTS 👇", ["Fish-Speech", "XTTSv2"], index=0))
                st.session_state["tts_method"] = tts_method

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
                    "Select Voice to use",
                    ["Default"] + list({str(file.stem) for file in Path(self.voices_dir).rglob('*.wav') if file.is_file()}),
                )
                st.session_state["voice_selection"] = voice_selection
                

                if voice_selection != "Default":
                    audio_file_path = self.voices_dir / (voice_selection + ".wav")
                    with open(audio_file_path, 'rb') as f:
                        audio_data = f.read()
                    st.audio(audio_data, format='audio/wav', start_time=0)

                    col_script, col_apply = st.columns([6, 1])
                    with col_script:
                        transcript_text = ""
                        if os.path.isfile(self.voices_dir / (voice_selection + ".txt")):
                            with open(self.voices_dir / (voice_selection + ".txt"), "r") as f:
                                transcript_text = ' '.join(f.readlines())
                        st.text_input("Voice Transcript", value=transcript_text, key="voice_transcript_text")
                    with col_apply:
                        st.write('<div style="height: 26px;"></div>', unsafe_allow_html=True)
                        if st.button("✅"):
                            with open(self.voices_dir / (voice_selection + ".txt"), "w") as f:
                                f.write(st.session_state["voice_transcript_text"])
                            st.success("ok")
                            time.sleep(0.5)
                            st.rerun()

                if st.button("🗑️ Clear Uploaded", use_container_width=True):
                    self.__clear_voices()


            with st.expander("Advanced Settings", expanded=True):
                if "ollama_settings_prompts_dialog" not in st.session_state:
                    if st.button("⚙️ Ollama Settings, Prompts & Filters", use_container_width=True):
                        self.ollama_settings_prompts_dialog()
                for expander in Config.config_sliders.keys():
                    with st.expander(expander): 
                        if expander in Config.config_sliders:
                            for s in Config.config_sliders[expander]:
                                st.slider(
                                    label=s.label,
                                    min_value=s.min,
                                    max_value=s.max,
                                    value=s.type(st.session_state["config"][s.section][s.key]),
                                    key=f"{s.section}_{s.key}",
                                    on_change=self.store_config()
                                )
                        if expander in Config.config_checkboxes:
                            for s in Config.config_checkboxes[expander]:
                                st.toggle(
                                    label=s.label,
                                    value=bool(st.session_state["config"][s.section][s.key]),
                                    key=f"{s.section}_{s.key}",
                                    on_change=self.store_config()
                                )
                        if expander in Config.config_selectboxes:
                            for s in Config.config_selectboxes[expander]:
                                st.selectbox(
                                    label=s.label,
                                    index=s.options.index(st.session_state["config"][s.section][s.key]),
                                    key=f"{s.section}_{s.key}",
                                    options=s.options,
                                    on_change=self.store_config()
                                )
                        if expander in Config.config_inputboxes:
                            for s in Config.config_inputboxes[expander]:
                                st.text_input(
                                    label=s.label,
                                    value=st.session_state["config"][s.section][s.key],
                                    key=f"{s.section}_{s.key}",
                                    on_change=self.store_config()
                                )

        # TODO: update dict and UI