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

class Config:

    slider_config_setup = namedtuple("SliderConfigSetup", "section key label type min max")
    checkbox_config_setup = namedtuple("CheckboxConfigSetup", "section key label")

    config_sliders = { "Fish-Speech" : [slider_config_setup("TTS_FISH", "num_samples", "Num. Samples", int, 1, 10),
                                        slider_config_setup("TTS_FISH", "top_p", "Top P", float, 0.0, 1.0),
                                        slider_config_setup("TTS_FISH", "repetition_penalty", "Repetition Penalty", float, 0.0, 5.0),
                                        slider_config_setup("TTS_FISH", "temperature", "Temperature", float, 0.0, 1.0),
                                        slider_config_setup("TTS_FISH", "seed", "Seed", int, 1, 1000),
                                        slider_config_setup("TTS_FISH", "chunk_length", "Chunk Length", int, 1, 1000)],
                        "XTTSv2" : [slider_config_setup("TTS_XTTSv2", "speed", "Speed", float, 0.1, 4.0)]}

    config_checkboxes = {   "Fish-Speech" : [checkbox_config_setup("TTS_FISH", "compile", "Compile")],
                            "XTTSv2" : [checkbox_config_setup("TTS_XTTSv2", "split_sentences", "Split Sentence")]}


    def __init__(self, voices_dir:Path, config_path="paper2go.ini", config_defaults_path="paper2go_defaults.ini"):
        self.config_path = config_path
        self.config_defaults_path = config_defaults_path
        self.voices_dir = voices_dir
        self.load_config()

    def as_dict(self):
        return st.session_state["config"]
        
    def load_config(self):
        parser = configparser.ConfigParser()
        parser.read(self.config_path)
        st.session_state["config"] = {section: dict(parser.items(section)) for section in parser.sections()}

    def store_config(self, stream=False):
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

        if stream:
            output = StringIO()
            parser.write(output)
            return output.getvalue()

    def update_config(self, key, value):
        if self.config and (key in self.config):
            self.config[key] = value

    @st.dialog("Upload your INI File")
    def config_upload_ini_dialog(self):
        uploaded_ini = st.file_uploader(
            label="Upload INI",
            type=["ini"],
            label_visibility="hidden")
        if uploaded_ini is not None:
            with open('paper2go.ini', "wb") as f:
                f.write(uploaded_ini.getbuffer())


    def __tts_translate(self, label_txt):
        lut = {"Fish-Speech": "TTS_FISH", "XTTSv2": "TTS_XTTSv2"}
        return lut[label_txt]
    
    def __clear_voices(self):
        for filename in os.listdir(self.voices_dir):
            file_path = self.voices_dir / filename
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)

    def config_ui(self):
        with st.sidebar:
            st.title("Settings")

            if st.button("✅ Save", use_container_width=True):
                for s in sum(Config.config_sliders.values(), []):
                    st.session_state["config"][s.section][s.key] = str(st.session_state.get(f"{s.section}_{s.key}"))
                for c in sum(Config.config_checkboxes.values(), []):
                    st.session_state["config"][c.section][c.key] = str(st.session_state.get(f"{c.section}_{c.key}"))
                print(st.session_state["config"])
                self.store_config()

            with st.expander("Store / Restore"):
                if st.button("⚙️ Restore Defaults"):
                    st.session_state["config"] = self.load_config(self.config_defaults_path)

                st.download_button(
                    label="💾 Download Config",
                    data=self.store_config(stream=True),
                    file_name='config.ini',
                    mime='text/plain'
                )

                if "config_upload_ini_dialog" not in st.session_state:
                    if st.button("📁 Upload Config INI"):
                        self.config_upload_ini_dialog()

            with st.expander("Basic Settings", expanded=True):
                st.session_state["config"]["TTS"]["tts_method"] = self.__tts_translate(st.radio("Select method for TTS 👇", ["Fish-Speech", "XTTSv2"], index=0))

                tts_voice_upload = st.file_uploader(
                                label="Voice sample",
                                type=["mp3", "wav"])
            
                if tts_voice_upload is not None:
                    with open(self.voices_dir/tts_voice_upload.name, "wb") as f:
                        f.write(tts_voice_upload.getbuffer())
                        if tts_voice_upload.type != "wav":
                            f = Path(self.voices_dir/tts_voice_upload).absolute()
                            AudioSegment.from_wav(f).export(f.with_suffix('.wav'), format="wav")

                if st.button("Clear Uploaded"):
                    self.__clear_voices()

                st.session_state["config"]["TTS"]["voice"] = self.voices_dir / st.selectbox("Select Voice to use",
                    ["Default"] + [str(file.name) for file in Path(self.voices_dir).rglob('*') if file.is_file()]
                )

            with st.expander("Advanced Settings", expanded=True):
                for expander in Config.config_sliders.keys():
                    with st.expander(expander): 
                        if expander in Config.config_sliders:
                            for s in Config.config_sliders[expander]:
                                st.slider(
                                    label=s.label,
                                    min_value=s.min,
                                    max_value=s.max,
                                    value=s.type(st.session_state["config"][s.section][s.key]),
                                    key=f"{s.section}_{s.key}"
                                )

                        if expander in Config.config_checkboxes:
                            for c in Config.config_checkboxes[expander]:
                                st.checkbox(
                                    label=c.label,
                                    value=bool(st.session_state["config"][c.section][c.key]),
                                    key=f"{c.section}_{c.key}"
                                )

        # TODO: update dict and UI