# Render 部署指南

## 步驟 1：註冊 Render 帳號
1. 訪問 https://render.com
2. 使用 GitHub 帳號登入

## 步驟 2：創建新服務
1. 點擊 "New +"
2. 選擇 "Web Service"
3. 連接您的 GitHub 帳號
4. 選擇倉庫：`sky770825/bniserver`

## 步驟 3：配置服務
- **Name**: `bniserver` (或您喜歡的名稱)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

## 步驟 4：環境變數
在 "Environment" 標籤中添加：
- `FLASK_ENV`: `production`
- `PORT`: `5000`

## 步驟 5：部署
1. 點擊 "Create Web Service"
2. Render 會自動開始部署
3. 等待部署完成

## 步驟 6：獲取域名
部署完成後，您會得到一個域名，例如：
`https://bniserver.onrender.com`

## 優點
- ✅ 免費額度充足
- ✅ 對 Flask 支持很好
- ✅ 自動 HTTPS
- ✅ 簡單的部署流程
- ✅ 良好的錯誤日誌

## 故障排除
如果遇到問題：
1. 檢查 Render 部署日誌
2. 確保所有依賴都在 `requirements.txt` 中
3. 確保 `render.yaml` 配置正確 