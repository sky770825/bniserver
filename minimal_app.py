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
        <title>簽到系統 - 測試版</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                min-height: 100vh;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                text-align: center; 
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            .btn { 
                padding: 15px 30px; 
                margin: 10px; 
                text-decoration: none; 
                color: white; 
                background: rgba(255,255,255,0.2); 
                border-radius: 10px; 
                display: inline-block;
                transition: all 0.3s ease;
            }
            .btn:hover { 
                background: rgba(255,255,255,0.3); 
                transform: translateY(-2px);
            }
            .status { 
                background: rgba(0,255,0,0.2); 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 簽到系統部署成功！</h1>
            <div class="status">
                <h2>✅ 網站狀態：正常運行</h2>
                <p>您的 Flask 應用已經成功部署到 Render</p>
            </div>
            <p><strong>環境變數：</strong></p>
            <ul style="text-align: left; display: inline-block;">
                <li>FLASK_ENV: {{ env.get("FLASK_ENV", "未設置") }}</li>
                <li>PORT: {{ env.get("PORT", "未設置") }}</li>
                <li>部署平台: Render</li>
            </ul>
            <div>
                <a href="/test" class="btn">🧪 測試 API</a>
                <a href="/health" class="btn">❤️ 健康檢查</a>
                <a href="/info" class="btn">ℹ️ 系統信息</a>
            </div>
            <p style="margin-top: 40px; opacity: 0.8;">
                這是一個簡化版本，用於測試部署是否成功
            </p>
        </div>
    </body>
    </html>
    ''', env=os.environ)

@app.route('/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Flask 應用正常運行',
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'port': os.environ.get('PORT', '5000'),
        'timestamp': '2025-01-29 13:00:00'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'bniserver',
        'version': '1.0.0',
        'environment': os.environ.get('FLASK_ENV', 'development')
    })

@app.route('/info')
def info():
    return jsonify({
        'app_name': '簽到系統',
        'framework': 'Flask',
        'deployment': 'Render',
        'database': 'SQLite',
        'features': [
            '用戶註冊/登入',
            '簽到/簽退',
            '活動管理',
            '個人資料',
            '管理員後台'
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 