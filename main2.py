import fitz
import numpy as np

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

# Usage example
invert_pdf_pages("input.pdf", "output.pdf", "1-12,14-20,22-32,56,66-78,82-97")
