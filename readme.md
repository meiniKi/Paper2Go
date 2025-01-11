# Paper2Go

![Paper2Go UI](doc/ui.png "Paper2Go")

Paper2Go converts written documents into speech. It primarily aims to convert research papers in PDF format to a summary that can be listened to on the go. All steps can be performed with self-hosted software.

Through the Web UI, the document can be uploaded. Paper2Go uses [Docling](https://github.com/DS4SD/docling) to extract the text and store it in Markdown format. Further, each section is summarized and re-formulated by an LLM (local [Ollama](https://github.com/ollama/ollama)) model to be understandable without visually seeing the document (e.g., explaining formulas and tables). Once done, the sections are individually converted to speech using [Fish-Speech](https://github.com/fishaudio/fish-speech) or [XTTSv2](https://huggingface.co/coqui/XTTS-v2) and named by the enumerated section titles. The audio files are combined in a zip file and can be downloaded via the UI.

> [!IMPORTANT]  
> :triangular_ruler: Please note that Paper2Go is work in progress.


# Quickstart

Clone the repo.

```shell
https://github.com/meiniKi/Paper2Go.git
```

Clone the models into `models`.

```shell
# install Git Large File Storage, see: https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage
git lfs install
cd models
https://github.com/fishaudio/fish-speech.git
git clone https://huggingface.co/fishaudio/fish-speech-1.5
git clone https://huggingface.co/coqui/XTTS-v2
```

Download the XTTS-v2 model. Run `xtts.py` to check your installation and download the model. You may have to access the license agreement while running the script.

```shell
cd models
python xtts.py
```

Create a virtual environment, activate it, and install the requirements.

```shell
cd <repo path>
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run redis, e.g., as a docker container.
```shell
docker compose up -d
```

Start the worker.
```shell
celery -A tasks worker --loglevel=warning
```

Start the application in another terminal.
```shell
streamlit run app.py
```

You should now be able to access the Web UI via IP and port.


# Via Docker 

🚧 Coming soon.