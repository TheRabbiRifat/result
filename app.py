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
FORM_URL = 'https://everify.bdris.gov.bd'

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

        # Extract hidden inputs including __RequestVerificationToken
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
        form_data = request.json

        ubrn = form_data.get('UBRN')
        birth_date = form_data.get('BirthDate')
        captcha_input_text = form_data.get('CaptchaInputText')
        captcha_de_text = form_data.get('CaptchaDeText')
        verification_token = form_data.get('__RequestVerificationToken')

        if not all([ubrn, birth_date, captcha_input_text, captcha_de_text, verification_token]):
            return jsonify({'error': 'Missing form fields'}), 400

        # Start a session to fetch the initial page and extract hidden inputs
        with requests.Session() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
            })

            # Fetch the form page
            response = session.get(TARGET_URL, verify=False, timeout=10)
            response.raise_for_status()

            # Parse the page to extract hidden inputs
            soup = BeautifulSoup(response.text, 'html.parser')
            hidden_inputs = {input_tag.get('name'): input_tag.get('value', '') for input_tag in soup.find_all('input', type='hidden')}
            
            # Add the provided values to hidden inputs
            hidden_inputs.update({
                '__RequestVerificationToken': verification_token,
                'UBRN': ubrn,
                'BirthDate': birth_date,
                'CaptchaInputText': captcha_input_text,
                'CaptchaDeText': captcha_de_text,
            })

            # Prepare the form data
            multipart_form_data = {key: (None, value) for key, value in hidden_inputs.items()}

            # Submit the form with multipart/form-data
            submit_response = session.post(FORM_URL, files=multipart_form_data, verify=False, timeout=10)
            submit_response.raise_for_status()

            # Parse the response to extract the specific div content
            result_soup = BeautifulSoup(submit_response.text, 'html.parser')
            target_div = result_soup.find('div', class_='container body-content')

            if target_div:
                target_div_html = str(target_div)
                return jsonify({'status': 'success', 'content': target_div_html})
            else:
                return jsonify({'status': 'failed', 'message': 'Target div not found'}), 400

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Form Submission Error', 'details': e.response.text}), 500

    except Exception as e:
        return jsonify({'error': 'Form Submission Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
