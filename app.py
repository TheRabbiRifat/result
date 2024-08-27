from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Render!"

@app.route('/submit_form', methods=['POST'])
def submit_form():
    uburn = request.form.get('UBRN')
    birth_date = request.form.get('BirthDate')
    captcha_input_text = request.form.get('CaptchaInputText')
    request_verification_token = request.form.get('__RequestVerificationToken')
    captcha_de_text = request.form.get('CaptchaDeText')

    url = 'https://everify.bdris.gov.bd/UBRNVerification/Search'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    data = {
        '__RequestVerificationToken': request_verification_token,
        'UBRN': uburn,
        'BirthDate': birth_date,
        'CaptchaInputText': captcha_input_text,
        'CaptchaDeText': captcha_de_text
    }
    
    response = requests.post(url, headers=headers, data=data, verify=False)
    
    return jsonify({
        'status_code': response.status_code,
        'response_text': response.text
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
