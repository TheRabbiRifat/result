from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define the URL of the form action
FORM_URL = "https://everify.bdris.gov.bd/UBRNVerification/Search"

@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Extract form data from the request (sent as multipart/form-data)
    uburn = request.form.get('UBRN')
    birth_date = request.form.get('BirthDate')
    captcha_de_text = request.form.get('CaptchaDeText')
    captcha_input_text = request.form.get('CaptchaInputText')
    request_verification_token = request.form.get('__RequestVerificationToken')

    # Check if the request verification token is provided
    if not request_verification_token:
        return jsonify({"status": "error", "message": "__RequestVerificationToken is required"}), 400

    # Extract the cookies from the request (user sends cookies as JSON in the request body)
    cookies_list = request.json.get('cookies', [])

    # Create a dictionary for the cookies
    cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}

    # Define the form data to be submitted as multipart/form-data
    form_data = {
        "__RequestVerificationToken": request_verification_token,
        "UBRN": uburn,
        "BirthDate": birth_date,
        "CaptchaDeText": captcha_de_text,
        "CaptchaInputText": captcha_input_text
    }

    try:
        # Perform the POST request with the multipart form data and cookies
        response = requests.post(FORM_URL, data=form_data, cookies=cookies, verify=False)

        # Return the response from the form submission
        return jsonify({"status": "success", "response": response.text}), response.status_code
    except Exception as e:
        # Handle errors
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
