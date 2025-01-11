# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

import os
import zipfile

def do_archive(idir, ofile):
    with zipfile.ZipFile(ofile, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(idir):
            rel_root = os.path.relpath(root, idir)
            
            for file in files:
                full_file_path = os.path.join(root, file)
                arcname = os.path.join(rel_root, file)
                zipf.write(full_file_path, arcname=arcname)
