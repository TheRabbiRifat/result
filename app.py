from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define the URL of the form action
FORM_URL = "https://everify.bdris.gov.bd/UBRNVerification/Search"

@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Extract form data from the request (multipart/form-data)
    uburn = request.form.get('UBRN')
    birth_date = request.form.get('BirthDate')
    captcha_de_text = request.form.get('CaptchaDeText')
    captcha_input_text = request.form.get('CaptchaInputText')
    request_verification_token = request.form.get('__RequestVerificationToken')

    # Extract cookies from the request (application/json)
    cookies_json = request.get_json()
    cookies = cookies_json.get('cookies', []) if cookies_json else []

    # Prepare cookies dictionary for the requests session
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}

    # Define the headers, including the User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Define the form data to be submitted
    form_data = {
        "__RequestVerificationToken": request_verification_token,
        "UBRN": uburn,
        "BirthDate": birth_date,
        "CaptchaDeText": captcha_de_text,
        "CaptchaInputText": captcha_input_text
    }

    try:
        # Perform the POST request with the form data and cookies
        response = requests.post(FORM_URL, headers=headers, data=form_data, cookies=cookies_dict, verify=False)

        # Return the response from the form submission
        return jsonify({"status": "success", "response": response.text}), response.status_code
    except Exception as e:
        # Handle errors
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
