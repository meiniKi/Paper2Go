# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import streamlit as st
from datetime import datetime
from pathlib import Path
from celery import Celery
from celery.result import AsyncResult
from config import Config
from tasks import archive
import time

class App():
    def __init__(self):
        self.config = Config(voices_dir=Path("voices").absolute())
        self.celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

    def __wait_with_spinner(self, task, file:int, of_files:int, step_name:str, step:int, of_steps:int):
        with st.spinner(f"Processing File ({file}/{of_files}) Step {step_name} ({step}/{of_steps})"):
            while True:
                task_result = AsyncResult(task.id, app=self.celery_app)
                if task_result.state == "SUCCESS":
                    return task_result.result
                elif task_result.state in ["FAILURE", "REVOKED"]:
                    st.error(f"Task failed with status: {task_result.state}")
                    return None
                time.sleep(1)

    def run(self):
        st.set_page_config(page_title="Paper2Go")
        st.title("Paper2Go")

        tab_pdf, tab_text = st.tabs(["From PDF", "From Text"])

        with tab_pdf:
            source_files = st.file_uploader("Select a pdf to convert.", accept_multiple_files=True, type=["pdf"])
            if st.button("Convert PDFs" if len(source_files) > 1 else "Convert PDF"):
                working_dir = Path("data").absolute() / self.unique_dir()
                st.write("This may take a few minutes, please be patient...")
                os.makedirs(working_dir, exist_ok=True)
                for i, file in enumerate(source_files):
                    file_bytes = bytes(file.getbuffer())
                    task_step_1 = self.__from_pdf_step_1(file_bytes, str(working_dir / "01_extracted.md"))
                    if (result := self.__wait_with_spinner(task_step_1, i, len(source_files), "PDF to Text Conversion", 1, 3)) is None:
                        break

                    task_step_2 = self.__from_pdf_step_2(result["markdown"], str(working_dir / "02_script.md"), self.config.as_dict())
                    if (result := self.__wait_with_spinner(task_step_2, i, len(source_files), "Reformulation", 2, 3)) is None:
                        break

                    os.makedirs(working_dir / "audio" / f"{i}")
                    task_step_3 = self.__from_text_pipeline(result["titles"], result["script"], str(working_dir / "audio" / f"{i}"), self.config.as_dict())
                    if (result := self.__wait_with_spinner(task_step_3, i, len(source_files), "Text-to-Speech", 3, 3)) is None:
                        break

                st.spinner("Preparing Download...")
                r = archive(str(working_dir / "audio"), str(working_dir / "audio.zip"))
                with open(working_dir / "audio.zip", "rb") as file:
                    st.download_button(
                        label="Download Files",
                        data=file,
                        file_name=str(working_dir / "audio.zip"),
                        mime="application/zip"
                    )

        with tab_text:
            summarize = st.toggle("Enhance text for TTS before converting", value=False)
            source_text = st.chat_input("Type your script here")
            if source_text:
                working_dir = Path("data").absolute() / self.unique_dir()
                os.makedirs(working_dir, exist_ok=True)
                if summarize:
                    task = self. __from_pdf_step_2("## Title" + source_text, str(working_dir), self.config.as_dict())
                    with st.spinner(f"Processing..."):
                        while True:
                            task_result = AsyncResult(task.id, app=self.celery_app)
                            if task_result.state == "SUCCESS":
                                st.write(task_result.get()["script"])
                                break
                            elif task_result.state in ["FAILURE", "REVOKED"]:
                                st.error(f"Task failed with status: {task_result.state}")
                                break
                            time.sleep(1)

                task = self.__from_text_pipeline(["tts"], task_result.get()["script"] if summarize else [source_text], str(working_dir), self.config.as_dict())
                with st.spinner(f"Processing..."):
                    while True:
                        task_result = AsyncResult(task.id, app=self.celery_app)
                        if task_result.state == "SUCCESS":
                            result = task_result.result
                            st.success(f"Done 💬✅")
                            break
                        elif task_result.state in ["FAILURE", "REVOKED"]:
                            st.error(f"Task failed with status: {task_result.state}")
                            break
                        time.sleep(1)

                st.audio(working_dir/"0-tts.mp3", format="audio/mpeg", loop=False)

        self.config.config_ui()
        
        st.sidebar.title("About")
        st.sidebar.write("Paper2Go converts a PDF to Markdown, re-formulates it, synthesizes it into speech, and converts it to MP3 audio.")        
        self.footer()

    def __from_text_pipeline(self, titles, texts, working_dir, config):
        return self.celery_app.send_task('tasks.make_tts', args=[titles, texts, working_dir, config])

    def __from_pdf_step_1(self, file_bytes, working_dir):
        return self.celery_app.send_task('tasks.convert_to_markdown', args=[file_bytes, working_dir])

    def __from_pdf_step_2(self, script, working_dir, config):
        return self.celery_app.send_task('tasks.make_listenable', args=[script, config, None])

    def unique_dir(self):
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]


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
    app.run()

