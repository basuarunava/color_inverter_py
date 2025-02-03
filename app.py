import gradio as gr
import fitz
import numpy as np
import tempfile
import os

def parse_page_selection(selection):
    pages = set()
    for part in selection.split(','):
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
    pages_to_invert = parse_page_selection(page_selection)
    doc = fitz.open(input_pdf)
    
    for page_num in pages_to_invert:
        if 0 <= page_num < len(doc):
            page = doc[page_num]
            pix = page.get_pixmap()
            inverted_pix = invert_colors(pix)
            img_rect = page.rect
            page.clean_contents()
            page.insert_image(img_rect, stream=inverted_pix.tobytes())

    doc.save(output_pdf)
    doc.close()

def invert_pdf_document(input_file, page_selection):
    # If input_file is a file-like object, write its content to a temp file.
    # Otherwise, assume it's a file path.
    if hasattr(input_file, "read"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
            tmp_in.write(input_file.read())
            tmp_in_path = tmp_in.name
        cleanup = True
    else:
        tmp_in_path = input_file
        cleanup = False

    # Create a temporary file to save the inverted PDF.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
        tmp_out_path = tmp_out.name

    invert_pdf_pages(tmp_in_path, tmp_out_path, page_selection)

    # Clean up temporary input file if it was created.
    if cleanup:
        os.remove(tmp_in_path)
    return tmp_out_path

iface = gr.Interface(
    fn=invert_pdf_document,
    inputs=[
        gr.File(label="Input PDF"),
        gr.Textbox(label="Page Selection", value="1-12,14-20,22-32,56,66-78,82-97")
    ],
    outputs=gr.File(label="Output PDF"),
    title="PDF Color Inverter",
    description="Upload a PDF and specify the pages to invert colors."
)

if __name__ == "__main__":
    iface.launch(share=True)