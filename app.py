from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configure Flask-Session if needed
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Extract form data from the request
    uburn = request.form.get('UBRN')
    birth_date = request.form.get('BirthDate')
    captcha_input_text = request.form.get('CaptchaInputText')
    request_verification_token = request.form.get('__RequestVerificationToken')
    captcha_de_text = request.form.get('CaptchaDeText')

    # Define the URL for form submission
    url = 'https://everify.bdris.gov.bd/UBRNVerification/Search'
    
    # Define headers including the User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Create the data payload to send in the POST request
    data = {
        '__RequestVerificationToken': request_verification_token,
        'UBRN': uburn,
        'BirthDate': birth_date,
        'CaptchaInputText': captcha_input_text,
        'CaptchaDeText': captcha_de_text
    }
    
    # Send the POST request with multipart/form-data encoding
    response = requests.post(url, headers=headers, data=data, verify=False)
    
    # Return the response from the form submission
    return jsonify({
        'status_code': response.status_code,
        'response_text': response.text
    })

if __name__ == '__main__':
    app.run(debug=True)
  
