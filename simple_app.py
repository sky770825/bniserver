from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>簽到系統</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 600px; margin: 0 auto; }
            .btn { padding: 10px 20px; margin: 5px; text-decoration: none; color: white; background: #007bff; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 簽到系統部署成功！</h1>
            <p>您的網站已經成功部署到 Render。</p>
            <p>環境變數：</p>
            <ul>
                <li>FLASK_ENV: {{ env.get("FLASK_ENV", "未設置") }}</li>
                <li>PORT: {{ env.get("PORT", "未設置") }}</li>
            </ul>
            <div>
                <a href="/health" class="btn">健康檢查</a>
                <a href="/login" class="btn">登入頁面</a>
            </div>
        </div>
    </body>
    </html>
    ''', env=os.environ)

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': '網站正常運行',
        'environment': os.environ.get('FLASK_ENV', 'development')
    })

@app.route('/login')
def login():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>登入 - 簽到系統</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 400px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            input { width: 100%; padding: 10px; margin-top: 5px; }
            .btn { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>登入</h1>
            <form method="POST">
                <div class="form-group">
                    <label>用戶名：</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>密碼：</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn">登入</button>
            </form>
            <p><a href="/">返回首頁</a></p>
        </div>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 