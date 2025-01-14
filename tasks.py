# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

from task.convert_to_markdown import do_convert_to_markdown
from task.make_listenable import do_make_listenable
from task.make_tts import do_make_tts
from task.archive import do_archive
from task.encode_reference import do_encode_reference

from celery import Celery

app = Celery(
    'tasks', 
    broker='redis://localhost:6379/0', 
    backend='redis://localhost:6379/0'
)

@app.task
def convert_to_markdown(file_bytes, ofile=None):
    return do_convert_to_markdown(file_bytes, ofile=None)

@app.task
def make_listenable(markdown, config_dict, ofile=None):
    return do_make_listenable(markdown, config_dict, ofile)

@app.task
def make_tts(titles, script, odir, config_dict):
    return do_make_tts(titles, script, odir, config_dict)

@app.task
def archive(idir, ofile):
    return do_archive(idir, ofile)

@app.task
def encode_reference(ifile, ofile, config_dict):
    return do_encode_reference(ifile, ofile, config_dict)
