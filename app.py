from flask import Flask, request, jsonify
import requests

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
        url = "https://everify.bdris.gov.bd/"

        # Prepare the form data
        form_data = {
            '__RequestVerificationToken': request_verification_token,
            'UBRN': ubrn,
            'BirthDate': birth_date,
            'CaptchaDeText': captcha_de_text,
            'CaptchaInputText': captcha_input,
        }

        # Custom headers including User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Submit the form with SSL verification disabled, custom User-Agent, and a timeout
        response = requests.post(url, data=form_data, headers=headers, timeout=10, verify=False)

        # Check if submission was successful
        if response.ok:
            return jsonify({"message": "Form submitted successfully!", "response": response.text}), 200
        else:
            return jsonify({"error": "Failed to submit the form.", "status_code": response.status_code}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
