import os
import subprocess
from flask import Flask, request, send_file, jsonify, after_this_request
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from werkzeug.utils import secure_filename
import glob

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
FONT_PATH = os.path.join('fonts', 'majalla.ttf')  # Path to the custom font
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Helper to apply font and styling 
def set_font_style(run, font_name='Sakkal Majalla', font_size=Pt(11)):
    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError(f"Font file not found: {FONT_PATH}")
    
    # Set font name and size
    run.font.name = font_name
    run.font.size = font_size

    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    rPr.append(rFonts)

@app.route('/convert', methods=['POST'])
def convert_docx_to_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.docx'):
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(filepath)

        # Apply font styling to the DOCX file
        document = Document(filepath)
        for paragraph in document.paragraphs:
            for run in paragraph.runs:
                set_font_style(run, font_name='Sakkal Majalla')

        styled_docx_path = os.path.join(UPLOAD_FOLDER, 'styled_' + file.filename)
        document.save(styled_docx_path)

        # Convert DOCX to PDF using LibreOffice
        try:
            subprocess.run([
                'libreoffice',
                '--headless',
                '--convert-to',
                'pdf',
                '--outdir',
                CONVERTED_FOLDER,
                styled_docx_path
            ], check=True)

            # Dynamically locate the output PDF
            base_filename = os.path.splitext(os.path.basename(styled_docx_path))[0]
            pdf_files = glob.glob(os.path.join(CONVERTED_FOLDER, f"{base_filename}*.pdf"))

            if not pdf_files:
                raise FileNotFoundError(f"No PDF file found for {base_filename} in {CONVERTED_FOLDER}")

            output_pdf_path = pdf_files[0]  # Assume the first match is correct

            # Schedule deletion of the files after download
            @after_this_request
            def cleanup_files(response):
                try:
                    os.remove(filepath)
                    os.remove(styled_docx_path)
                    os.remove(output_pdf_path)
                except Exception as e:
                    app.logger.error(f"Error cleaning up files: {e}")
                return response

        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'LibreOffice failed: {e.stderr.decode()}'}), 500
        except FileNotFoundError as e:
            return jsonify({'error': str(e)}), 500

        return send_file(output_pdf_path, as_attachment=True)

    return jsonify({'error': 'Invalid file format. Only DOCX is supported.'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
