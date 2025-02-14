# SPDX-FileCopyrightText: 2025 Meinhard Kissich
# SPDX-License-Identifier: MIT

from tempfile import NamedTemporaryFile
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

def do_convert_to_markdown(file_bytes, ofile=None):
    artifacts_path = StandardPdfPipeline.download_models_hf()
    pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path, do_table_structure=True)
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    with NamedTemporaryFile(delete=True, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name
        markdown = doc_converter.convert(temp_file_path).document.export_to_markdown()

    if ofile is not None:
        with open(ofile, "w") as f:
            f.write(markdown)

    return {"status": "complete", "markdown": markdown}