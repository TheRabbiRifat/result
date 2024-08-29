from flask import Flask, request, jsonify, render_template_string, session
from flask_session import Session
from pypdf import PdfReader
import io
import base64
from PIL import Image
import requests
import pdfkit
import fitz  # PyMuPDF
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['PERMANENT_SESSION_LIFETIME'] = 300  # 5 minutes
Session(app)

# The URL that will always be scraped
TARGET_URL = 'https://everify.bdris.gov.bd'

def get_image_format(image_data):
    image = Image.open(io.BytesIO(image_data))
    return image.format.lower()

@app.route('/')
def home():
    html = '''
    <html>
    <head>
        <meta http-equiv="refresh" content="5;url=https://puffin24.xyz">
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                text-align: center;
            }
            .container {
                background: #fff;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                max-width: 500px;
                width: 100%;
            }
            h1 {
                font-size: 24px;
                color: #333;
                margin-bottom: 20px;
            }
            p {
                font-size: 16px;
                color: #555;
                margin: 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Proudly Served with Pie IT.</h1>
            <p>You will be redirected shortly...</p>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/check-json')
def check_json():
    return jsonify({"status": "success", "message": "Flask app is running!"})

@app.route('/extract-images', methods=['POST'])
def extract_images():
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    pdf_file = request.files['pdf']
    reader = PdfReader(pdf_file)
    images = []

    # Extract images from each page of the PDF
    for page in reader.pages:
        for image in page.images:
            image_io = io.BytesIO()
            image_io.write(image.data)
            image_io.seek(0)
            image_format = get_image_format(image.data)
            image_base64 = base64.b64encode(image_io.getvalue()).decode('utf-8')
            images.append(f"data:image/{image_format};base64,{image_base64}")

    if len(images) < 2:
        return jsonify({"error": "The PDF does not contain enough images"}), 400

    # Prepare the images for the response
    response = {
        "photo": images[0],
        "sign": images[1]
    }
    return jsonify(response)

@app.route('/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    try:
        # Start a session to fetch the webpage content
        session.clear()
        session['requests_session'] = requests.Session()
        session['requests_session'].headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        })
        
        response = session['requests_session'].get(TARGET_URL, verify=False, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract hidden inputs
        hidden_inputs = {}
        for hidden_input in soup.find_all("input", type="hidden"):
            hidden_inputs[hidden_input.get("name")] = hidden_input.get("value", "")

        # Convert webpage to PDF
        pdf_path = '/tmp/webpage.pdf'
        pdfkit.from_url(TARGET_URL, pdf_path)

        # Extract images from PDF
        pdf_document = fitz.open(pdf_path)
        first_image_base64 = None

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            images = page.get_images(full=True)
            if images:
                xref = images[0][0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                content_type = base_image["ext"]
                first_image_base64 = f"data:image/{content_type};base64," + base64.b64encode(image_bytes).decode('utf-8')
                break  # Exit after extracting the first image

        pdf_document.close()

        if not first_image_base64:
            return jsonify({'error': 'No images found in the PDF'}), 400

        return jsonify({
            'status': 'success',
            'captcha': first_image_base64,  # Provide the first image as 'captcha'
            'hidden_inputs': hidden_inputs  # Include hidden inputs in the response
        })

    except Exception as e:
        return jsonify({'error': 'Conversion Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
