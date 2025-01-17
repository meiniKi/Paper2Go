# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import streamlit as st
from config_io import ConfigIO

class ConfigHelper:

    @classmethod
    def update_config(cls, key, func = lambda x: x):
        s, k = key.split("/")[0], key.split("/")[1]
        st.session_state["config"][s][k] = str(func(st.session_state[key]))
        ConfigIO.store_config()

    @staticmethod
    def make_sliders(ctx_lists):
        for s in ctx_lists:
            st.slider(
                label=s.label,
                min_value=s.min,
                max_value=s.max,
                value=s.type(st.session_state["config"][s.section][s.key]),
                key=f"{s.section}/{s.key}",
                on_change=ConfigHelper.update_config,
                args=[f"{s.section}/{s.key}"]
            )

    @staticmethod
    def make_checkboxes(ctx_list):
        for s in ctx_list:
            st.toggle(
                label=s.label,
                value=bool(st.session_state["config"][s.section][s.key]),
                key=f"{s.section}/{s.key}",
                on_change=ConfigHelper.update_config,
                args=[f"{s.section}/{s.key}"]
            )

    @staticmethod
    def make_selectboxes(ctx_lists):
        for s in ctx_lists:
            st.selectbox(
                label=s.label,
                index=s.options.index(st.session_state["config"][s.section][s.key]),
                key=f"{s.section}/{s.key}",
                options=s.options,
                on_change=ConfigHelper.update_config,
                args=[f"{s.section}/{s.key}"]
            )

    @staticmethod
    def make_text_inputs(ctx_list):
        for s in ctx_list:
            st.text_input(
                label=s.label,
                value=st.session_state["config"][s.section][s.key],
                key=f"{s.section}/{s.key}",
                on_change=ConfigHelper.update_config,
                args=[f"{s.section}/{s.key}"]
            )

    @staticmethod
    def make_text_ares(ctx_list):
        for s in ctx_list:
            st.text_area(
                label=s.label,
                value=st.session_state["config"][s.section][s.key],
                key=f"{s.section}/{s.key}",
                on_change=ConfigHelper.update_config,
                args=[f"{s.section}/{s.key}"]
            )
