# Railway 部署指南

## 步驟 1：註冊 Railway 帳號
1. 訪問 https://railway.app
2. 使用 GitHub 帳號登入

## 步驟 2：創建新項目
1. 點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 選擇您的 GitHub 倉庫：`sky770825/bniserver`

## 步驟 3：配置環境變數
在 Railway 項目設置中添加以下環境變數：
- `FLASK_ENV`: `production`
- `PORT`: `5000`

## 步驟 4：部署
Railway 會自動檢測到 Python 項目並開始部署。

## 步驟 5：獲取域名
部署完成後，Railway 會提供一個域名，例如：
`https://your-app-name.railway.app`

## 優點
- ✅ 更適合 Flask 應用
- ✅ 免費額度充足
- ✅ 自動 HTTPS
- ✅ 簡單的部署流程
- ✅ 更好的錯誤日誌

## 故障排除
如果遇到問題：
1. 檢查 Railway 部署日誌
2. 確保所有依賴都在 `requirements.txt` 中
3. 確保 `railway.json` 配置正確 