from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
    <head><title>測試頁面</title></head>
    <body>
        <h1>✅ 網站正常運行</h1>
        <p>Flask 應用已成功部署</p>
        <p>環境：{}</p>
        <p>端口：{}</p>
    </body>
    </html>
    '''.format(
        os.environ.get('FLASK_ENV', 'development'),
        os.environ.get('PORT', '5000')
    )

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok', 'message': 'pong'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 