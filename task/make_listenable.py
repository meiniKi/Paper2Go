# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import re
from tqdm import tqdm
import configparser
import torch
from ollama import chat, Client
from ollama import ChatResponse

def do_make_listenable(markdown, config_dict, ofile=None):
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
        if any(word in s.lower() for word in config_dict["LISTENABLE"]["filters"].split(",")):
            to_skip += 1
            continue
        if not s.startswith("#"):
            texts[-1] += s
            continue
        
        print(s)
        processed_titles.append(s)
        texts.append(s)

    processed_texts = []

    client = Client(host=config_dict["LISTENABLE"]["host"])

    for i in tqdm(range(len(texts))):
        if len(processed_texts) == 0:
            context = ""
        elif len(processed_texts) == 1:
            context = processed_texts[0]
        else:
            context = processed_texts[0] + processed_texts[-1]

        response = client.generate(
            model=config_dict["LISTENABLE"]["model"],
            system=config_dict["LISTENABLE"]["system_prompt"],
            prompt=config_dict["LISTENABLE"]["user_prompt_template"].format(text=texts[i], context=context)
        )
        processed_texts.append(response.response.strip().strip("```").strip().strip('"'))
    

    if ofile is not None:
        with open(ofile, "w") as f:
            f.write(' '.join(processed_texts))
    
    return {"status": "complete", "titles": processed_titles, "script": processed_texts}