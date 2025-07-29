from flask import Flask, render_template_string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>測試頁面</title>
    </head>
    <body>
        <h1>網站正常運行！</h1>
        <p>環境變數：</p>
        <ul>
            <li>FLASK_ENV: {{ env.get("FLASK_ENV", "未設置") }}</li>
            <li>PORT: {{ env.get("PORT", "未設置") }}</li>
        </ul>
    </body>
    </html>
    ''', env=os.environ)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 