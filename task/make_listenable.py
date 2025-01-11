# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import re
from tqdm import tqdm
import configparser
import torch
from ollama import chat, Client
from ollama import ChatResponse

def do_make_listenable(markdown, ofile=None):
    config = configparser.ConfigParser()
    config.read('paper2go.ini')
    MODEL = config.get('LISTENABLE','MODEL')
    HOST = config.get('LISTENABLE','HOST')
    FILTERS = config.get('LISTENABLE','FILTERS').split(",")
    SYSTEM_PROMPT = config.get('LISTENABLE','SYSTEM_PROMPT')

    prompt_template = """
        Take into account the context delimited by triple backquotes.

        ```{context}```

        Take the text delimited by triple backquotes and rewrite it for text to speech. Thus, describe all formulas and tables verbally. Only respond with the rewrite. Do not add any other text.

        ```{text}```
    """

    markdown_sections = re.split("(^#.*$)", markdown, flags=re.MULTILINE)

    to_skip = 0
    texts = []
    title = None

    processed_titles = []

    for s in filter(lambda x: x.strip() != "", markdown_sections):
        if title is None:
            title = s.strip().strip("#")
        if to_skip > 0:
            to_skip -= 1
            continue
        s = s.strip()
        if any(word in s.lower() for word in FILTERS):
            to_skip += 1
            continue
        if not s.startswith("#"):
            texts[-1] += s
            continue
        
        print(s)
        processed_titles.append(s)
        texts.append(s)

    processed_texts = []

    client = Client(host=HOST)

    for i in tqdm(range(len(texts))):
        if len(processed_texts) == 0:
            context = ""
        elif len(processed_texts) == 1:
            context = processed_texts[0]
        else:
            context = processed_texts[0] + processed_texts[-1]

        response = client.generate(
            model=MODEL,
            system=SYSTEM_PROMPT,
            prompt=prompt_template.format(text=texts[i], context=context)
        )
        processed_texts.append(response.response.strip().strip("```").strip().strip('"'))
    

    if ofile is not None:
        with open(ofile, "w") as f:
            f.write(' '.join(processed_texts))
    
    return {"status": "complete", "titles": processed_titles, "script": processed_texts}