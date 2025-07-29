# PythonAnywhere 配置文件
# 將此文件重命名為 app.py 並上傳到 PythonAnywhere

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# 創建 Flask 應用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# PythonAnywhere 數據庫配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checkin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 檔案上傳配置
app.config['UPLOAD_FOLDER'] = 'static/uploads/avatars'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 確保上傳資料夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 簡單的測試路由
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>簽到系統 - PythonAnywhere</title>
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 簽到系統</h1>
            <h2>✅ 部署到 PythonAnywhere 成功！</h2>
            <p>您的 Flask 應用已經成功部署到 PythonAnywhere</p>
            <div>
                <a href="/test" class="btn">🧪 測試 API</a>
                <a href="/health" class="btn">❤️ 健康檢查</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Flask 應用正常運行',
        'platform': 'PythonAnywhere',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'bniserver',
        'platform': 'PythonAnywhere',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(debug=True) 