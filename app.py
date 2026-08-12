from flask import Flask, request, send_file, render_template
from PIL import Image
import fitz
import os
import uuid
import zipfile
from docx import Document


app = Flask(__name__)


# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================================================
# SAFE FILE DELETE
# =========================================================

def delete_file_safely(file_path):

    try:

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    except Exception:

        pass


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# IMAGE → PDF
# =========================================================

@app.route("/image-to-pdf", methods=["POST"])
def image_to_pdf():

    files = request.files.getlist("files")

    images = []


    for file in files:

        if not file or file.filename == "":
            continue


        extension = file.filename.lower().split(".")[-1]


        if extension not in ["jpg", "jpeg", "png"]:

            return (
                "Only JPG, JPEG and PNG files are allowed.",
                400
            )


        try:

            image = Image.open(file)


            if image.mode != "RGB":

                image = image.convert("RGB")


            images.append(image.copy())

            image.close()


        except Exception as e:

            return (
                f"Image error: {e}",
                400
            )


    if not images:

        return (
            "No valid images found.",
            400
        )


    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"{uuid.uuid4()}.pdf"
    )


    try:

        images[0].save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=images[1:]
        )


        return send_file(
            output_path,
            as_attachment=True,
            download_name="Easy-Edits.pdf"
        )


    except Exception as e:

        delete_file_safely(output_path)

        return (
            f"Image to PDF error: {e}",
            500
        )


# =========================================================
# PDF → JPG
# =========================================================

@app.route("/pdf-to-jpg", methods=["POST"])
def pdf_to_jpg():

    file = request.files.get("file")


    if not file or file.filename == "":

        return (
            "No PDF selected.",
            400
        )


    if not file.filename.lower().endswith(".pdf"):

        return (
            "Please upload a PDF file.",
            400
        )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        f"{uuid.uuid4()}.pdf"
    )


    file.save(input_path)


    image_files = []

    pdf = None


    try:

        pdf = fitz.open(input_path)


        for page_number, page in enumerate(pdf):

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False
            )


            image_path = os.path.join(
                OUTPUT_FOLDER,
                f"{uuid.uuid4()}-page-{page_number + 1}.jpg"
            )


            pix.save(image_path)

            image_files.append(image_path)


        pdf.close()

        pdf = None


        # Delete uploaded PDF
        delete_file_safely(input_path)


        # Single page PDF
        if len(image_files) == 1:

            return send_file(
                image_files[0],
                as_attachment=True,
                download_name="Easy-Edits.jpg"
            )


        # Multiple page PDF
        zip_path = os.path.join(
            OUTPUT_FOLDER,
            f"{uuid.uuid4()}.zip"
        )


        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:


            for image_path in image_files:

                zip_file.write(
                    image_path,
                    os.path.basename(image_path)
                )


        return send_file(
            zip_path,
            as_attachment=True,
            download_name="Easy-Edits-JPG.zip"
        )


    except Exception as e:

        if pdf is not None:

            try:
                pdf.close()
            except:
                pass


        delete_file_safely(input_path)


        return (
            f"PDF to JPG error: {e}",
            500
        )


# =========================================================
# MERGE PDF
# =========================================================

@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():

    files = request.files.getlist("files")


    if len(files) < 2:

        return (
            "Please select at least 2 PDF files.",
            400
        )


    merged_pdf = fitz.open()


    try:

        valid_files = 0


        for file in files:

            if not file or file.filename == "":
                continue


            if not file.filename.lower().endswith(".pdf"):

                merged_pdf.close()

                return (
                    "Only PDF files are allowed.",
                    400
                )


            temp_path = os.path.join(
                UPLOAD_FOLDER,
                f"{uuid.uuid4()}.pdf"
            )


            file.save(temp_path)


            pdf = None


            try:

                pdf = fitz.open(temp_path)

                merged_pdf.insert_pdf(pdf)

                valid_files += 1


            finally:

                if pdf is not None:

                    try:
                        pdf.close()
                    except:
                        pass


                # Delete temporary uploaded PDF
                delete_file_safely(temp_path)


        if valid_files < 2:

            merged_pdf.close()

            return (
                "Please select at least 2 PDF files.",
                400
            )


        output_path = os.path.join(
            OUTPUT_FOLDER,
            f"{uuid.uuid4()}.pdf"
        )


        merged_pdf.save(output_path)

        merged_pdf.close()


        return send_file(
            output_path,
            as_attachment=True,
            download_name="Easy-Edits-Merged.pdf"
        )


    except Exception as e:

        try:
            merged_pdf.close()
        except:
            pass


        return (
            f"Merge PDF error: {e}",
            500
        )


# =========================================================
# COMPRESS PDF
# =========================================================

@app.route("/compress-pdf", methods=["POST"])
def compress_pdf():

    file = request.files.get("file")


    if not file or file.filename == "":

        return (
            "No PDF selected.",
            400
        )


    if not file.filename.lower().endswith(".pdf"):

        return (
            "Only PDF files are allowed.",
            400
        )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        f"{uuid.uuid4()}.pdf"
    )


    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"{uuid.uuid4()}.pdf"
    )


    file.save(input_path)


    pdf = None


    try:

        pdf = fitz.open(input_path)


        pdf.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )


        pdf.close()

        pdf = None


        # Delete temporary uploaded PDF
        delete_file_safely(input_path)


        return send_file(
            output_path,
            as_attachment=True,
            download_name="Easy-Edits-Compressed.pdf"
        )


    except Exception as e:

        if pdf is not None:

            try:
                pdf.close()
            except:
                pass


        delete_file_safely(input_path)

        delete_file_safely(output_path)


        return (
            f"Compression error: {e}",
            500
        )


# =========================================================
# PDF → WORD
# =========================================================

@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():

    file = request.files.get("file")


    if not file or file.filename == "":

        return (
            "No PDF selected.",
            400
        )


    if not file.filename.lower().endswith(".pdf"):

        return (
            "Only PDF files are allowed.",
            400
        )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        f"{uuid.uuid4()}.pdf"
    )


    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"{uuid.uuid4()}.docx"
    )


    file.save(input_path)


    pdf = None


    try:

        pdf = fitz.open(input_path)


        document = Document()


        for page_number, page in enumerate(pdf):

            text = page.get_text("text")


            if text.strip():

                if page_number > 0:

                    document.add_page_break()


                for line in text.split("\n"):

                    line = line.strip()


                    if line:

                        document.add_paragraph(line)


        pdf.close()

        pdf = None


        document.save(output_path)


        # Delete temporary uploaded PDF
        delete_file_safely(input_path)


        return send_file(
            output_path,
            as_attachment=True,
            download_name="Easy-Edits-Word.docx"
        )


    except Exception as e:

        if pdf is not None:

            try:
                pdf.close()
            except:
                pass


        delete_file_safely(input_path)

        delete_file_safely(output_path)


        return (
            f"PDF to Word error: {e}",
            500
        )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )