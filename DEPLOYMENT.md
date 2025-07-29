# 🚀 簽到網站部署指南

## 📋 部署前準備

### 1. 確保文件完整
- ✅ `app.py` - 主應用程式
- ✅ `requirements.txt` - Python 依賴
- ✅ `Procfile` - 部署配置
- ✅ `runtime.txt` - Python 版本
- ✅ `.gitignore` - Git 忽略文件

### 2. 代碼上傳到 GitHub
```bash
# 初始化 Git 倉庫
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit"

# 在 GitHub 創建新倉庫，然後推送
git remote add origin https://github.com/你的用戶名/簽到網站.git
git branch -M main
git push -u origin main
```

## 🌐 部署選項

### 選項 1: Vercel（推薦新手）

1. **註冊 Vercel**
   - 訪問 [vercel.com](https://vercel.com)
   - 使用 GitHub 帳號註冊

2. **導入項目**
   - 點擊 "New Project"
   - 選擇你的 GitHub 倉庫
   - 點擊 "Import"

3. **配置部署**
   - Framework Preset: 選擇 "Other"
   - Build Command: 留空
   - Output Directory: 留空
   - Install Command: `pip install -r requirements.txt`

4. **環境變量**
   - 添加 `FLASK_ENV=production`

5. **部署**
   - 點擊 "Deploy"
   - 等待部署完成

### 選項 2: Railway

1. **註冊 Railway**
   - 訪問 [railway.app](https://railway.app)
   - 使用 GitHub 帳號註冊

2. **創建項目**
   - 點擊 "New Project"
   - 選擇 "Deploy from GitHub repo"
   - 選擇你的倉庫

3. **自動部署**
   - Railway 會自動檢測 Python 項目
   - 自動安裝依賴並部署

### 選項 3: Render

1. **註冊 Render**
   - 訪問 [render.com](https://render.com)
   - 使用 GitHub 帳號註冊

2. **創建 Web Service**
   - 點擊 "New +"
   - 選擇 "Web Service"
   - 連接你的 GitHub 倉庫

3. **配置**
   - Name: 你的項目名稱
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

## 🔧 部署後配置

### 1. 設置管理員帳號
- 訪問你的網站
- 使用預設帳號登入：
  - 用戶名：`admin`
  - 密碼：`admin123`
- 立即修改管理員密碼

### 2. 配置域名（可選）
- 在部署平台添加自定義域名
- 配置 SSL 證書（通常自動提供）

### 3. 數據庫備份
- 定期備份數據庫文件
- 考慮使用外部數據庫服務

## 🛠️ 故障排除

### 常見問題

1. **部署失敗**
   - 檢查 `requirements.txt` 是否完整
   - 確認 Python 版本兼容性

2. **應用無法啟動**
   - 檢查 `Procfile` 格式
   - 確認端口配置

3. **靜態文件無法訪問**
   - 確認 `static` 目錄結構正確
   - 檢查文件權限

### 本地測試
```bash
# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
export FLASK_ENV=production

# 運行應用
python app.py
```

## 📞 支持

如果遇到問題，請檢查：
1. 部署平台的錯誤日誌
2. 應用程式的錯誤信息
3. 網絡連接和防火牆設置

---

**注意**：部署到生產環境前，請確保：
- 修改預設管理員密碼
- 配置適當的安全設置
- 定期備份數據
- 監控應用性能 