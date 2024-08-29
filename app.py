from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        # Extract form data from the POST request
        ubrn = request.json.get('UBRN')
        birth_date = request.json.get('BirthDate')
        captcha_input = request.json.get('CaptchaInputText')
        captcha_de_text = request.json.get('CaptchaDeText')
        request_verification_token = request.json.get('__RequestVerificationToken')

        # Validate required fields
        if not all([ubrn, birth_date, captcha_input, captcha_de_text, request_verification_token]):
            return jsonify({"error": "Missing required fields"}), 400

        # URL of the page containing the form
        form_page_url = "https://everify.bdris.gov.bd/"

        # Fetch the page containing the form
        response = requests.get(form_page_url)
        if not response.ok:
            return jsonify({"error": "Failed to fetch the form page.", "status_code": response.status_code}), 500

        # Parse the form page
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        
        if form is None:
            return jsonify({"error": "Form not found on the page."}), 500

        # Extract hidden fields
        hidden_inputs = form.find_all('input', type='hidden')
        form_data = {input.get('name'): input.get('value') for input in hidden_inputs}

        # Add or update form data with user input
        form_data.update({
            '__RequestVerificationToken': request_verification_token,
            'UBRN': ubrn,
            'BirthDate': birth_date,
            'CaptchaDeText': captcha_de_text,
            'CaptchaInputText': captcha_input,
        })

        # Submit the form
        action_url = form.get('action')
        if not action_url.startswith('http'):
            action_url = form_page_url.rsplit('/', 1)[0] + '/' + action_url

        submit_response = requests.post(action_url, data=form_data, verify=False)  # disable SSL verification

        # Check if submission was successful
        if submit_response.ok:
            return jsonify({"message": "Form submitted successfully!", "response": submit_response.text}), 200
        else:
            return jsonify({"error": "Failed to submit the form.", "status_code": submit_response.status_code}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
