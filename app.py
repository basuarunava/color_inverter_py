import gradio as gr
import fitz
import numpy as np
import tempfile
import os
from loguru import logger

def parse_page_selection(selection, num_pages=None):
    selection = selection.strip().lower()
    if selection == "all" and num_pages is not None:
        return list(range(num_pages))
    pages = set()
    for part in selection.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.update(range(start - 1, end))  # Convert to 0-based index
        else:
            pages.add(int(part) - 1)  # Convert to 0-based index
    return sorted(pages)

def invert_colors(pix):
    img = np.frombuffer(pix.samples, dtype=np.uint8)
    img = 255 - img  # Invert colors
    return fitz.Pixmap(pix.colorspace, pix.width, pix.height, img.tobytes(), pix.alpha)

def invert_pdf_pages(input_pdf, output_pdf, page_selection):
    doc = fitz.open(input_pdf)
    pages_to_invert = parse_page_selection(page_selection, len(doc))
    for page_num in pages_to_invert:
        if 0 <= page_num < len(doc):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=100)  # Lower DPI for smaller images
            inverted_pix = invert_colors(pix)
            img_rect = page.rect
            page.clean_contents()
            page.insert_image(img_rect, stream=inverted_pix.tobytes(), keep_proportion=True)
    doc.save(output_pdf, deflate=True, garbage=4)
    doc.close()
def remove_pdf_pages(input_pdf, output_pdf, page_selection):
    pages_to_remove = parse_page_selection(page_selection)
    doc = fitz.open(input_pdf)
    for page_num in sorted(pages_to_remove, reverse=True):
        if 0 <= page_num < len(doc):
            doc.delete_page(page_num)
    doc.save(output_pdf)
    doc.close()

def invert_pdf_document(input_file, page_selection, output_name, remove_pages):
    logger.info(f"Starting PDF inversion for {input_file} on pages: {page_selection}")
    if hasattr(input_file, "read"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
            tmp_in.write(input_file.read())
            tmp_in_path = tmp_in.name
        cleanup = True
        logger.info(f"Created temporary input file: {tmp_in_path}")
    else:
        tmp_in_path = input_file
        cleanup = False

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
        tmp_out_path = tmp_out.name
    logger.info(f"Created temporary output file: {tmp_out_path}")

    if remove_pages:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_removed:
            tmp_removed_path = tmp_removed.name
        remove_pdf_pages(tmp_in_path, tmp_removed_path, remove_pages)
        tmp_in_path = tmp_removed_path
        logger.info(f"Removed pages: {remove_pages}")

    invert_pdf_pages(tmp_in_path, tmp_out_path, page_selection)
    logger.info(f"Successfully inverted pages: {page_selection}")

    if cleanup:
        os.remove(tmp_in_path)

    final_output_path = os.path.join(os.path.dirname(tmp_out_path), output_name)
    os.rename(tmp_out_path, final_output_path)
    logger.info(f"Output saved as: {final_output_path}")
    return final_output_path

iface = gr.Interface(
    fn=invert_pdf_document,
    inputs=[
        gr.File(label="Input PDF"),
        gr.Textbox(label="Page Selection", value="1-12,14-20,22-32,56,66-78,82-97"),
        gr.Textbox(label="Output Name", value="inverted_output.pdf"),
        gr.Textbox(label="Pages to Remove", value="")
    ],
    outputs=gr.File(label="Output PDF"),
    title="PDF Color Inverter",
    description="Upload a PDF, specify the pages to invert (or type 'all'), pages to remove, and a custom output name. by @arunavabasucom"
)

if __name__ == "__main__":
    iface.launch(share=True, server_name="0.0.0.0")