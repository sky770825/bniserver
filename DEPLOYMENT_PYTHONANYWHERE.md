# PythonAnywhere 部署指南

## 步驟 1：註冊 PythonAnywhere 帳號
1. 訪問 https://www.pythonanywhere.com
2. 點擊 "Create a Beginner account" (免費帳號)
3. 填寫註冊信息

## 步驟 2：登入並創建 Web 應用
1. 登入後，點擊 "Web" 標籤
2. 點擊 "Add a new web app"
3. 選擇 "Flask"
4. 選擇 Python 3.11
5. 設置路徑：`/home/yourusername/mysite/flask_app.py`

## 步驟 3：上傳文件
1. 點擊 "Files" 標籤
2. 進入 `/home/yourusername/mysite/` 目錄
3. 上傳以下文件：
   - `app.py` (重命名 pythonanywhere_config.py)
   - `requirements.txt`
   - `templates/` 目錄
   - `static/` 目錄

## 步驟 4：安裝依賴
1. 點擊 "Consoles" 標籤
2. 打開 Bash console
3. 執行：
   ```bash
   cd mysite
   pip install -r requirements.txt
   ```

## 步驟 5：配置 Web 應用
1. 回到 "Web" 標籤
2. 在 "Code" 部分：
   - Source code: `/home/yourusername/mysite`
   - Working directory: `/home/yourusername/mysite`
3. 在 "WSGI configuration file" 中設置：
   ```python
   import sys
   path = '/home/yourusername/mysite'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```

## 步驟 6：重啟應用
1. 點擊 "Reload" 按鈕
2. 等待重啟完成

## 步驟 7：訪問您的網站
您的網站地址將是：
`https://yourusername.pythonanywhere.com`

## 優點
- ✅ 專門為 Python 設計
- ✅ 非常穩定可靠
- ✅ 免費額度充足
- ✅ 簡單易用
- ✅ 自動 HTTPS

## 故障排除
如果遇到問題：
1. 檢查 Console 中的錯誤日誌
2. 確保所有文件路徑正確
3. 確保依賴已正確安裝 