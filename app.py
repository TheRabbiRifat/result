import base64
import io
from flask import Flask, jsonify, request
from flask_session import Session
from pyppeteer import launch
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

async def fetch_page_content(url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
    content = await page.content()
    await browser.close()
    return content

async def convert_to_pdf(url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
    pdf_data = await page.pdf()
    await browser.close()
    return pdf_data

@app.route('/convert-to-pdf', methods=['POST'])
async def convert_to_pdf_endpoint():
    try:
        # Fetch the webpage content
        page_content = await fetch_page_content(TARGET_URL)

        # Parse hidden inputs
        soup = BeautifulSoup(page_content, 'html.parser')
        hidden_inputs = {input_tag.get("name"): input_tag.get("value", "") for input_tag in soup.find_all("input", type="hidden")}

        # Convert webpage to PDF
        pdf_data = await convert_to_pdf(TARGET_URL)

        # Save the PDF to a temporary file
        pdf_path = '/tmp/webpage.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_data)

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
async def submit_form():
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

        # Launch browser and navigate to the target URL
        browser = await launch()
        page = await browser.newPage()
        await page.goto(TARGET_URL, {'waitUntil': 'networkidle2'})

        # Fill in the form fields
        await page.type('input[name="UBRN"]', ubrn)
        await page.type('input[name="BirthDate"]', birth_date)
        await page.type('input[name="CaptchaInputText"]', captcha_input_text)
        await page.type('input[name="CaptchaDeText"]', captcha_de_text)
        await page.evaluate(f'document.querySelector('input[name="__RequestVerificationToken"]').value = "{verification_token}";')

        # Click the submit button
        await page.click('button[type="submit"]')  # Adjust the selector if needed

        # Wait for navigation or response after submission
        await page.waitForNavigation({'waitUntil': 'networkidle2'})

        # Get the response content
        response_content = await page.content()

        # Parse the response to extract the specific div content
        result_soup = BeautifulSoup(response_content, 'html.parser')
        target_div = result_soup.find('div', class_='container body-content')

        await browser.close()

        if target_div:
            target_div_html = str(target_div)
            return jsonify({'status': 'success', 'content': target_div_html})
        else:
            return jsonify({'status': 'failed', 'message': 'Target div not found'}), 400

    except Exception as e:
        return jsonify({'error': 'Form Submission Error', 'details': str(e)}), 500

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run(host='0.0.0.0', port=8080))
