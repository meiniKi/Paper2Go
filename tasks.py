# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

from task.convert_to_markdown import do_convert_to_markdown
from task.make_listenable import do_make_listenable
from task.make_tts import do_make_tts
from task.archive import do_archive

from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True)
def convert_to_markdown(self, ifile, ofile=None):
    return do_convert_to_markdown(ifile, ofile=None)

@app.task(bind=True)
def make_listenable(self, markdown, ofile=None):
    return do_make_listenable(markdown, ofile)

@app.task(bind=True)
def make_tts(self, titles, script, odir, config_dict):
    return do_make_tts(titles, script, odir, config_dict)

@app.task(bind=True)
def archive(self, idir, ofile):
    return do_archive(idir, ofile)