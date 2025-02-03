import cv2
import re
import os
import glob
import sys
from fpdf import FPDF
from pdf2image import convert_from_path
from PIL import Image as PILImage

class Converter:
    def __init__(self):
        self.a4_w_mm = 210
        self.a4_h_mm = 297
        self.dpi = 200.0

    def invert_image(self, i_input, i_output):
        """Inverts a given image."""
        image = cv2.imread(i_input)
        print("Inverting image: {}".format(i_input))
        if image is None:
            print("Error reading image: {}".format(i_input))
            return
        image = ~image
        cv2.imwrite(i_output, image)

    def pdf_to_img_all(self, file_path, o_dir):
        """Converts all PDF pages to JPEG images."""
        if not os.path.exists(o_dir):
            os.makedirs(o_dir)
        pages = convert_from_path(file_path, dpi=self.dpi)
        for i, image in enumerate(pages):
            output_path = os.path.join(o_dir, f"{i+1}.jpeg")
            image.save(output_path, 'JPEG', quality=95)
            print("Saved image: {}".format(output_path))

    def get_scaled_dimensions(self, width_pixels, height_pixels):
        """Calculate scaled dimensions maintaining aspect ratio."""
        width_ratio = width_pixels / height_pixels
        
        if width_ratio > 1:  # Landscape
            w = self.a4_h_mm
            h = self.a4_h_mm / width_ratio
            return 'L', w, h
        else:  # Portrait
            h = self.a4_h_mm
            w = self.a4_h_mm * width_ratio
            return 'P', w, h

    def img_to_pdf(self, i_dir, o_dir, filename, invert_pages):
        """Combines images into PDF, inverting specified pages."""
        pdf = FPDF(unit="mm", format='A4')
        pdf.set_auto_page_break(auto=False, margin=0)
        pdf.set_margins(0, 0, 0)

        # Collect and sort image files
        filepaths = []
        for filepath in glob.iglob(os.path.join(i_dir, '*.jpeg')):
            filepaths.append(filepath)

        pages = []
        for path in filepaths:
            base = os.path.basename(path)
            match = re.search(r'(\d+)\.jpeg', base)
            if match:
                pages.append((int(match.group(1)), path))
        pages.sort(key=lambda x: x[0])

        # Process each page
        for page_num, img_path in pages:
            if page_num in invert_pages:
                self.invert_image(img_path, img_path)
            else:
                print("Keeping original image: {}".format(img_path))
            
            with PILImage.open(img_path) as img:
                width_pixels, height_pixels = img.size

            # Get scaled dimensions and orientation
            orientation, w, h = self.get_scaled_dimensions(width_pixels, height_pixels)
            
            # Add page with proper orientation
            pdf.add_page(orientation=orientation)
            
            # Center image on page
            x = (self.a4_w_mm if orientation == 'P' else self.a4_h_mm - w) / 2
            y = (self.a4_h_mm if orientation == 'P' else self.a4_w_mm - h) / 2
            
            # Place image
            pdf.image(img_path, x=x, y=y, w=w, h=h)
            print(f"Added {img_path} to PDF ({orientation})")

        # Save output
        if not os.path.exists(o_dir):
            os.makedirs(o_dir)
        output_pdf = os.path.join(o_dir, filename)
        pdf.output(output_pdf, "F")
        print("Generated PDF: {}".format(output_pdf))


def parse_page_ranges(range_str):
    """Converts range string to list of page numbers."""
    pages = set()
    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


if __name__ == "__main__":
    converter = Converter()
    pdf_file = 'input.pdf'
    img_dir = 'images'
    output_dir = 'output'
    output_pdf_name = 'result.pdf'

    page_range_str = "1-12,14-20,22-32,56,66-78,82-97"
    pages_to_invert = parse_page_ranges(page_range_str)

    converter.pdf_to_img_all(pdf_file, img_dir)
    converter.img_to_pdf(img_dir, output_dir, output_pdf_name, pages_to_invert)