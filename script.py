import os
import shutil
import re
import argparse
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

import datetime

def remove_white_background(image):
    image = image.convert("RGBA")
    data = image.getdata()

    new_data = []
    for item in data:
        # Set transparency (alpha) to 0 for white background pixels
        if item[:3] == (255, 255, 255):
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    image.putdata(new_data)
    return image

def replace_colors(image, color_replacements):
    image = image.convert("RGBA")
    data = image.getdata()

    new_data = []
    for item in data:
        # Check if the current pixel color is in the replacements dictionary
        if item[:3] in color_replacements:
            new_color = color_replacements[item[:3]]
            new_data.append(new_color + (255,))
        else:
            new_data.append(item)

    image.putdata(new_data)
    return image


def process_pdf_files(file1, file2, output_dir):
    # Convert PDFs to images with increased DPI
    images1 = convert_from_path(file1, dpi=150)
    images2 = convert_from_path(file2, dpi=150)

    color_replacements1 = {(0, 0, 0): (255, 0, 0)}
    color_replacements1_black = {(26, 26, 26): (255, 0, 0)}
    color_replacements1_grey = {(152, 152, 152): (255, 0, 0)}
    color_replacements1_grey1 = {(153, 153, 153): (255, 0, 0)}
    color_replacements1_grey2 = {(166, 166, 166):(255, 0, 0)}
    color_replacements1_lnl = {(237,237,237):(255, 0, 0)}

    color_replacements2 = {(0, 0, 0): (0, 255, 0)}
    color_replacements2_grey = {(152, 152, 152): (0, 255, 0)}
    color_replacements2_black = {(26, 26, 26): (0, 255, 0)}
    color_replacements2_grey1 = {(153, 153, 153): (0, 255, 0)}
    color_replacements2_grey2 = {(166, 166, 166):(0, 255, 0)}
    color_replacements2_lnl = {(237,237,237):(0, 255, 0)}

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Process each page of the PDFs
    for i, (image1, image2) in enumerate(zip(images1, images2)):
        # Remove white background
        image1 = remove_white_background(image1)
        image2 = remove_white_background(image2)
        # image1_copy = image1.copy()
        image2_copy = image2.copy()

        image1 = replace_colors(image1, color_replacements1)
        image2 = replace_colors(image2, color_replacements2)
        image1 = replace_colors(image1, color_replacements1_grey)
        image2 = replace_colors(image2, color_replacements2_grey)
        image1 = replace_colors(image1, color_replacements1_black)
        image2 = replace_colors(image2, color_replacements2_black)
        image1 = replace_colors(image1, color_replacements1_grey1)
        image2 = replace_colors(image2, color_replacements2_grey1)        
        image1 = replace_colors(image1, color_replacements1_grey2)
        image2 = replace_colors(image2, color_replacements2_grey2) 
        image1 = replace_colors(image1, color_replacements1_lnl)
        image2 = replace_colors(image2, color_replacements2_lnl) 

        # Replace colors in image1 where red overlaps with green
        for x in range(image1.width):
            for y in range(image1.height):
                pixel1 = image1.getpixel((x, y))
                pixel2 = image2.getpixel((x, y))

                # Check if the pixel in image1 is red and the pixel in image2 is green
                if pixel1 == (255, 0, 0, 255) and pixel2 == (0, 255, 0, 255):
                    original_pixel2 = image2_copy.getpixel((x, y))
                    image2.putpixel((x, y), original_pixel2)

        # Overlay images
        combined_image = Image.alpha_composite(image1, image2)

        # Convert the image to RGB before saving as PDF
        combined_image = combined_image.convert("RGB")

        # Save the result as a PDF file
        output_file = os.path.join(output_dir, f"comparison_page{i+1:02}.pdf")
        combined_image.save(output_file, "PDF", resolution=150.0)

    print("Comparison completed successfully.")

def check_pdf_for_pattern(pdf_path, second_pdf, output_dir, pattern):
    reader1 = PdfReader(pdf_path)
    reader2 = PdfReader(second_pdf)
    page_numbers = []
    writer1 = PdfWriter()
    writer2 = PdfWriter()
    allmatches2 = []
    for page_number2, page2 in enumerate(reader2.pages):
        text2 = page2.extract_text()
        matches2 = re.findall(pattern, text2)
        allmatches2.append(matches2)


    for page_number, page in enumerate(reader1.pages):

        text = page.extract_text()
        matches = re.findall(pattern, text)
        print("IN PROCESS....")
        if matches:
            for page_number2, page2 in enumerate(reader2.pages):
                if matches not in allmatches2:
                    break
                else:
                    text2 = page2.extract_text()
                    matches2 = re.findall(pattern, text2)

                    if matches2 and matches == matches2:
                        page_numbers.append(page_number)  # Add page number into a list

                        print("Found a match! Codes found on page: ", matches)
                        writer1.add_page(page)
                        writer2.add_page(page2)
                        output_file1 = "temp/output_file1.pdf"  # First PDF output file path
                        output_file2 = "temp/output_file2.pdf"  # Second PDF output file path

                        with open(output_file1, "wb") as f1:
                            writer1.write(f1)

                        with open(output_file2, "wb") as f2:
                            writer2.write(f2)

                        process_pdf_files(output_file1, output_file2, output_dir)

                        # Deleting temp files
                        os.remove(output_file1)
                        os.remove(output_file2)
                        break


    return page_numbers

def get_page_count(pdf_file):
    with open(pdf_file, 'rb') as f:
        pdf_reader = PdfReader(f)
        page_count = pdf_reader.getNumPages()
    return page_count

def replace_pages_in_pdf(original_pdf, replacement_pdf, page_numbers, output_dir):
    print("Replacing pages...")
    original_reader = PdfReader(original_pdf)
    writer = PdfWriter()
    length = len(original_reader.pages)
    j = 0
    for i in range(length):
        page = original_reader.pages[i]
        print("Completed pages: ", i, "/", length)
        if i in page_numbers:
            replacement_reader = PdfReader(output_dir+"\\"+replacement_pdf[j])
            replacement_page = replacement_reader.pages[0]
            writer.add_page(replacement_page)
            j += 1
        else:
            writer.add_page(page)
        
    output_file = original_pdf +"_comparison.pdf"
    with open(output_file, "wb") as f:
        writer.write(f)

    print("Pages replaced successfully in the original PDF.")

def main():
    parser = argparse.ArgumentParser(description="PDF Comparison Script")
    parser.add_argument("file1", help="First input PDF file")
    parser.add_argument("file2", help="Second input PDF file")
    parser.add_argument("-o", "--output-dir", default="output", help="Output directory (default: output)")

    args = parser.parse_args()
    file1 = args.file1
    file2 = args.file2
    output_dir = args.output_dir

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        print("Cleaning directories....")
    else:
        os.mkdir(output_dir)
        print("Temp output directory created.")

    if os.path.exists("temp"):
        shutil.rmtree("temp")
        os.mkdir("temp")
    else:
        os.mkdir("temp")


    print("Getting codes....")
    pages = check_pdf_for_pattern(file1, file2, output_dir, "[A-Z]{1,2}-\\d{3}[A-E]?")
    file_list = os.listdir(output_dir)
    replace_pages_in_pdf(file1, file_list, pages, output_dir)
    shutil.rmtree(output_dir)
    os.mkdir(output_dir)

if __name__ == "__main__":
    main()