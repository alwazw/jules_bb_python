import os
import fitz  # PyMuPDF

def watermark_pdf(file_path, output_dir):
    """
    Adds a 'VOIDED' watermark to a PDF file and saves it to a new directory.
    It also renames the file to indicate it has been voided.
    """
    if not os.path.exists(file_path):
        print(f"ERROR: PDF file not found at {file_path}. Cannot watermark.")
        return

    try:
        doc = fitz.open(file_path)
        for page in doc:
            # Add a diagonal "VOIDED" watermark
            rect = page.rect
            p1 = fitz.Point(rect.width / 10, rect.height / 10)
            p2 = fitz.Point(rect.width * 9 / 10, rect.height * 9 / 10)

            # The text will be inserted in a box that is drawn from bottom-left to top-right
            # We need to calculate the rectangle for the text
            text_rect = fitz.Rect(p1, p2)

            # Add the text
            page.insert_textbox(text_rect, "VOIDED",
                                fontsize=50,
                                fontname="helv-bold",
                                color=(1, 0, 0),  # Red
                                align=fitz.TEXT_ALIGN_CENTER,
                                rotate=45,
                                opacity=0.5)

        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        voided_filename = f"{name}_voided{ext}"
        output_path = os.path.join(output_dir, voided_filename)

        doc.save(output_path)
        doc.close()

        print(f"SUCCESS: Watermarked and saved voided label to {output_path}")

        # Optionally, remove the original file after watermarking
        os.remove(file_path)
        print(f"INFO: Removed original label: {file_path}")

    except Exception as e:
        print(f"ERROR: Failed to watermark PDF {file_path}. Reason: {e}")
