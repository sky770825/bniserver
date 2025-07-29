# 簽到系統

一個功能完整的簽到管理系統，類似於 https://bni-youlate.weddingwishlove.com/ 的簽到網站。

## 功能特色

### 🎯 核心功能
- **用戶註冊/登入**：支持用戶註冊和登入系統
- **簽到/簽退**：每日簽到和簽退功能
- **活動管理**：創建和管理活動
- **個人資料**：查看個人簽到記錄和資料
- **管理後台**：管理員可以查看所有用戶和簽到記錄

### 🎨 界面設計
- **現代化UI**：使用Bootstrap 5和漸變色彩
- **響應式設計**：支持手機、平板和桌面設備
- **動畫效果**：卡片浮動動畫和過渡效果
- **直觀操作**：簡潔明了的用戶界面

### 🔧 技術架構
- **後端**：Flask + SQLAlchemy
- **前端**：Bootstrap 5 + jQuery
- **數據庫**：SQLite（可擴展到MySQL/PostgreSQL）
- **圖標**：Font Awesome 6

## 安裝和運行

### 1. 克隆項目
```bash
git clone https://github.com/sky770825/bniserver.git
cd bniserver
```

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 運行應用
```bash
python app.py
```

### 4. 訪問網站
打開瀏覽器訪問：http://localhost:5000

## 默認帳號

### 管理員帳號
- **用戶名**：admin
- **密碼**：admin123

## 功能說明

### 用戶功能
1. **註冊**：填寫用戶名、姓名、郵箱等資訊
2. **登入**：使用用戶名和密碼登入
3. **簽到**：每日簽到，可選擇地點和備註
4. **簽退**：每日簽退
5. **個人資料**：查看簽到記錄和個人資訊
6. **活動查看**：瀏覽所有活動

### 管理員功能
1. **用戶管理**：查看所有用戶資訊
2. **簽到記錄**：查看所有簽到記錄
3. **活動管理**：新增、編輯、刪除活動
4. **統計數據**：查看用戶數、簽到數等統計

## 數據庫結構

### 用戶表 (User)
- id：主鍵
- username：用戶名（唯一）
- password_hash：密碼哈希
- name：姓名
- email：郵箱
- phone：電話
- is_admin：是否為管理員
- created_at：創建時間

### 簽到記錄表 (CheckIn)
- id：主鍵
- user_id：用戶ID
- check_in_time：簽到時間
- check_out_time：簽退時間
- location：簽到地點
- notes：備註
- status：狀態（checked_in/checked_out）

### 活動表 (Event)
- id：主鍵
- title：活動標題
- description：活動描述
- start_time：開始時間
- end_time：結束時間
- location：活動地點
- max_participants：最大參與人數
- created_at：創建時間

### 活動註冊表 (EventRegistration)
- id：主鍵
- event_id：活動ID
- user_id：用戶ID
- registered_at：註冊時間
- status：狀態（registered/attended/cancelled）

## 自定義配置

### 修改數據庫
在 `app.py` 中修改：
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
```

### 修改密鑰
在 `app.py` 中修改：
```python
app.config['SECRET_KEY'] = 'your-secret-key-here'
```

## 部署建議

### 生產環境
1. 使用 Gunicorn 或 uWSGI 作為 WSGI 服務器
2. 使用 Nginx 作為反向代理
3. 使用 PostgreSQL 或 MySQL 作為數據庫
4. 配置 SSL 證書

### 示例部署命令
```bash
# 安裝生產依賴
pip install gunicorn

# 運行生產服務器
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 開發計劃

### 即將推出的功能
- [ ] 簽到統計報表
- [ ] 活動報名功能
- [ ] 郵件通知
- [ ] 手機APP
- [ ] 地理位置簽到
- [ ] 二維碼簽到

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

MIT License
