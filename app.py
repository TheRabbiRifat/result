import requests
from flask import Flask, jsonify, request
from bs4 import BeautifulSoup

app = Flask(__name__)

# The URL that will always be scraped
TARGET_URL = 'https://everify.bdris.gov.bd'

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        # Receive form data from the client
        user_data = {
            'UBRN': request.json.get('UBRN'),
            'BirthDate': request.json.get('BirthDate'),
            'CaptchaInputText': request.json.get('CaptchaInputText'),
            'CaptchaDeText': request.json.get('CaptchaDeText'),
            '__RequestVerificationToken': request.json.get('__RequestVerificationToken'),
        }

        if not all(user_data.values()):
            return jsonify({'error': 'Missing form fields'}), 400

        # Start a session to persist cookies and hidden inputs
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        })

        # Step 1: Visit the initial page to extract hidden fields and cookies
        response = session.get(TARGET_URL, verify=False, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Step 2: Extract hidden inputs from the initial form
        hidden_inputs = {}
        for hidden_input in soup.find_all("input", type="hidden"):
            hidden_inputs[hidden_input.get("name")] = hidden_input.get("value", "")

        # Step 3: Replace hidden inputs with user-provided values
        hidden_inputs.update(user_data)

        # Step 4: Prepare the form data for submission
        form_data = {
            '__RequestVerificationToken': hidden_inputs.get('__RequestVerificationToken'),
            'UBRN': hidden_inputs.get('UBRN'),
            'BirthDate': hidden_inputs.get('BirthDate'),
            'CaptchaInputText': hidden_inputs.get('CaptchaInputText'),
            'CaptchaDeText': hidden_inputs.get('CaptchaDeText'),
        }

        # Step 5: Submit the form
        submit_response = session.post(TARGET_URL, data=form_data, verify=False, timeout=10)
        submit_response.raise_for_status()

        # Step 6: Parse the response to extract the specific div content
        result_soup = BeautifulSoup(submit_response.text, 'html.parser')
        target_div = result_soup.find('div', class_='container body-content')

        if target_div:
            # Convert the div to HTML and return it in the response
            target_div_html = str(target_div)
            return jsonify({'status': 'success', 'content': target_div_html})
        else:
            return jsonify({'status': 'failed', 'message': 'Target div not found'}), 400

    except Exception as e:
        return jsonify({'error': 'Form Submission Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
