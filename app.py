import base64
import requests
import pdfkit
import fitz  # PyMuPDF
from flask import Flask, jsonify, request
from flask_session import Session
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['PERMANENT_SESSION_LIFETIME'] = 300  # 5 minutes
Session(app)

# The URL that will always be scraped
TARGET_URL = 'https://everify.bdris.gov.bd'
FORM_URL = 'https://everify.bdris.gov.bd/UBRNVerification/Search'

@app.route('/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    try:
        # Start a session to fetch the webpage content
        requests_session = requests.Session()
        requests_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        })
        
        response = requests_session.get(TARGET_URL, verify=False, timeout=10)
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

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        # Receive form data from the client
        ubrn = request.json.get('UBRN')
        birth_date = request.json.get('BirthDate')
        captcha = request.json.get('CaptchaInputText')
        captcha_hidden = request.json.get('CaptchaDeText')

        if not all([ubrn, birth_date, captcha, captcha_hidden]):
            return jsonify({'error': 'Missing form fields'}), 400

        # Start a session to fetch the initial page and extract hidden inputs
        requests_session = requests.Session()
        requests_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        })

        response = requests_session.get(TARGET_URL, verify=False, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract and include any hidden inputs required by the form
        hidden_inputs = {}
        for hidden_input in soup.find_all("input", type="hidden"):
            hidden_inputs[hidden_input.get("name")] = hidden_input.get("value", "")

        # Prepare form data
        form_data = {
            '__RequestVerificationToken': hidden_inputs.get('__RequestVerificationToken', ''),
            'UBRN': ubrn,
            'BirthDate': birth_date,
            'CaptchaInputText': captcha,
            'CaptchaDeText': captcha_hidden,
        }

        # Submit the form
        submit_response = requests_session.post(FORM_URL, data=form_data, verify=False, timeout=10)
        submit_response.raise_for_status()

        # Parse the response to extract the result table
        result_soup = BeautifulSoup(submit_response.text, 'html.parser')
        result_table = result_soup.find('table')  # Assuming the result is in a table

        if result_table:
            # Convert the result table to HTML or text and return
            result_html = str(result_table)
            return jsonify({'status': 'success', 'result': result_html})
        else:
            return jsonify({'status': 'failed', 'message': 'No result table found'}), 400

    except Exception as e:
        return jsonify({'error': 'Form Submission Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
