# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import configparser
import streamlit as st


class ConfigIO:
    config_path = "paper2go.ini"
    config_defaults_path = "paper2go_default.ini"

    @classmethod
    def load_config(cls, defaults=False):
        parser = configparser.ConfigParser()
        parser.read(cls.config_path if not defaults else cls.config_defaults_path)
        st.session_state["config"] = {section: dict(parser.items(section)) for section in parser.sections()}
        if defaults:
            cls.store_config()

    @classmethod
    def store_config(cls):
        parser = configparser.ConfigParser()
        for section in st.session_state["config"].keys():
            parser.add_section(section)

        for section in st.session_state["config"].keys():
            section_dict = st.session_state["config"][section]
            fields = section_dict.keys()
            for field in fields:
                value = section_dict[field]
                parser.set(section, field, str(value))

        if cls.config_path is not None:
            with open(cls.config_path, 'w') as f:
                parser.write(f)