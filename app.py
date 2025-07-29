from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# 職級選項
POSITION_OPTIONS = [
    '區董顧',
    '執行董顧', 
    '董顧',
    '主席',
    '副主席',
    '教育組長',
    '資訊長'
]

# 權限檢查輔助函數
def has_permission(permission):
    """檢查當前用戶是否有指定權限"""
    if 'user_id' not in session:
        return False
    
    user = db.session.get(User, session['user_id'])
    if not user:
        return False
    
    # 管理員擁有所有權限
    if user.is_admin:
        return True
    
    # 檢查特定權限
    if permission == 'add_events':
        return user.can_add_events
    elif permission == 'edit_events':
        return user.can_edit_events
    elif permission == 'delete_events':
        return user.can_delete_events
    elif permission == 'manage_users':
        return user.can_manage_users
    
    return False

# 創建 Flask 應用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 根據環境設置數據庫路徑
if os.environ.get('FLASK_ENV') == 'production':
    # 生產環境使用絕對路徑
    db_path = os.path.join(os.getcwd(), 'checkin.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
else:
    # 開發環境使用相對路徑
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checkin.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 檔案上傳配置
app.config['UPLOAD_FOLDER'] = 'static/uploads/avatars'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 確保上傳資料夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 簡單的測試路由 - 不依賴數據庫
@app.route('/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Flask 應用正常運行',
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'port': os.environ.get('PORT', '5000')
    })

@app.route('/')
def index_simple():
    """簡化的首頁，不依賴數據庫"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>簽到系統</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 600px; margin: 0 auto; text-align: center; }
            .btn { padding: 15px 30px; margin: 10px; text-decoration: none; color: white; background: rgba(255,255,255,0.2); border-radius: 10px; display: inline-block; }
            .btn:hover { background: rgba(255,255,255,0.3); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 簽到系統</h1>
            <p>您的網站已經成功部署到 Render！</p>
            <p>環境：{{ env.get("FLASK_ENV", "development") }}</p>
            <div>
                <a href="/test" class="btn">測試 API</a>
                <a href="/health" class="btn">健康檢查</a>
            </div>
        </div>
    </body>
    </html>
    ''', env=os.environ)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_avatar(file, user_id):
    if file and allowed_file(file.filename):
        # 生成安全的檔案名
        filename = secure_filename(f"avatar_{user_id}_{int(datetime.now().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f"uploads/avatars/{filename}"
    return None

db = SQLAlchemy(app)

# 數據模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    line_id = db.Column(db.String(50))  # 新增：LINE ID欄位
    avatar = db.Column(db.String(200))  # 新增：頭像檔案路徑
    position = db.Column(db.String(50))  # 新增：職級欄位
    bio = db.Column(db.Text)  # 新增：自介欄位
    can_add_events = db.Column(db.Boolean, default=False)  # 新增：可以新增活動
    can_edit_events = db.Column(db.Boolean, default=False)  # 新增：可以編輯活動
    can_delete_events = db.Column(db.Boolean, default=False)  # 新增：可以刪除活動
    can_manage_users = db.Column(db.Boolean, default=False)  # 新增：可以管理用戶
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='checked_in')  # checked_in, checked_out
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))  # 新增：關聯活動

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(50), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    max_participants = db.Column(db.Integer, default=0)  # 0表示無限制
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organizer = db.relationship('User', backref='organized_events')

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='registered')  # registered, attended, cancelled

# 健康檢查路由
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': '網站正常運行',
        'environment': os.environ.get('FLASK_ENV', 'development')
    })

# 路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['name'] = user.name
            session['is_admin'] = user.is_admin
            flash('登入成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用戶名或密碼錯誤！', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('已登出！', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        line_id = request.form.get('line_id', '')
        
        if not username or not password or not name:
            flash('請填寫所有必填欄位', 'error')
            return render_template('register.html')
        
        # 檢查用戶名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用戶名已存在', 'error')
            return render_template('register.html')
        
        # 檢查姓名格式
        if '/' not in name:
            flash('姓名格式錯誤，請使用「編號/姓名/專業別」格式', 'error')
            return render_template('register.html')
        
        # 創建新用戶
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            name=name,
            email=email,
            phone=phone,
            line_id=line_id,
            is_admin=False
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('註冊成功！請登入', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'註冊失敗：{str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/checkin', methods=['POST'])
def checkin():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    user_id = session['user_id']
    today = datetime.now().date()
    
    # 檢查是否已經簽到
    existing_checkin = CheckIn.query.filter(
        CheckIn.user_id == user_id,
        db.func.date(CheckIn.check_in_time) == today,
        CheckIn.status == 'checked_in'
    ).first()
    
    if existing_checkin:
        return jsonify({'success': False, 'message': '今日已簽到！'})
    
    # 創建新的簽到記錄
    checkin = CheckIn(
        user_id=user_id,
        location=request.form.get('location', ''),
        notes=request.form.get('notes', '')
    )
    
    db.session.add(checkin)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '簽到成功！'})

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    user_id = session['user_id']
    today = datetime.now().date()
    
    # 查找今日的簽到記錄
    checkin = CheckIn.query.filter(
        CheckIn.user_id == user_id,
        db.func.date(CheckIn.check_in_time) == today,
        CheckIn.status == 'checked_in'
    ).first()
    
    if not checkin:
        return jsonify({'success': False, 'message': '今日尚未簽到！'})
    
    if checkin.check_out_time:
        return jsonify({'success': False, 'message': '今日已簽退！'})
    
    # 更新簽退時間
    checkin.check_out_time = datetime.now()
    checkin.status = 'checked_out'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '簽退成功！'})

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    checkins = CheckIn.query.filter_by(user_id=session['user_id']).order_by(CheckIn.check_in_time.desc()).limit(10).all()
    
    # 計算出席統計
    total_events = Event.query.count()
    attended_events = db.session.query(CheckIn.event_id).filter_by(user_id=session['user_id']).distinct().count()
    missed_events = total_events - attended_events if total_events > 0 else 0
    
    # 計算出席率
    attendance_rate = (attended_events / total_events * 100) if total_events > 0 else 0
    
    return render_template('profile.html', 
                         user=user, 
                         checkins=checkins,
                         total_events=total_events,
                         attended_events=attended_events,
                         missed_events=missed_events,
                         attendance_rate=attendance_rate)

@app.route('/user/<int:user_id>')
def view_user_profile(user_id):
    """查看其他用戶的個人檔案"""
    if 'user_id' not in session:
        flash('請先登入', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, user_id)
    if not user:
        flash('用戶不存在', 'error')
        return redirect(url_for('events'))
    
    # 獲取用戶的簽到統計
    checkin_count = CheckIn.query.filter_by(user_id=user_id).count()
    
    # 獲取用戶發起的活動
    organized_events = Event.query.filter_by(organizer_id=user_id).order_by(Event.created_at.desc()).limit(5).all()
    
    # 計算缺席數和參與率
    total_events = Event.query.count()
    if total_events > 0:
        attendance_rate = round((checkin_count / total_events) * 100, 1)
        absent_count = total_events - checkin_count
    else:
        attendance_rate = 0
        absent_count = 0
    
    return render_template('user_profile.html', 
                         user=user, 
                         checkin_count=checkin_count,
                         organized_events=organized_events,
                         absent_count=absent_count,
                         attendance_rate=attendance_rate)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        user.line_id = request.form['line_id']
        user.bio = request.form.get('bio', '')  # 新增：處理自介欄位
        
        # 只有管理員才能修改職級
        if session.get('is_admin'):
            user.position = request.form['position']
        
        # 檢查姓名格式
        if '/' not in user.name:
            flash('姓名格式錯誤，請使用「編號/姓名/專業別」格式', 'error')
            return render_template('edit_profile.html', user=user)
        
        # 處理新密碼
        new_password = request.form.get('new_password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        # 處理頭像上傳
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename != '':
                if file and allowed_file(file.filename):
                    filename = save_avatar(file, user.id)
                    if filename:
                        # 刪除舊頭像
                        if user.avatar:
                            old_avatar_path = os.path.join(app.static_folder, 'avatars', user.avatar)
                            if os.path.exists(old_avatar_path):
                                os.remove(old_avatar_path)
                        user.avatar = filename
        
        db.session.commit()
        flash('個人資料更新成功！', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/events')
def events():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    events = Event.query.order_by(Event.created_at.desc()).all()
    all_users = User.query.all()  # 新增：獲取所有用戶列表
    now = datetime.now()  # 新增：當前時間
    return render_template('events.html', events=events, all_users=all_users, now=now, has_permission=has_permission)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    event = db.session.get(Event, event_id)
    if not event:
        flash('活動不存在', 'error')
        return redirect(url_for('events'))
    
    # 獲取當前用戶
    current_user = db.session.get(User, session['user_id'])
    
    # 檢查當前用戶是否已簽到
    user_checkin = CheckIn.query.filter_by(
        user_id=session['user_id'], 
        event_id=event_id
    ).first()
    
    # 獲取所有成員
    all_users = User.query.all()
    
    # 獲取已簽到的成員
    checked_in_users = db.session.query(CheckIn, User).join(
        User, CheckIn.user_id == User.id
    ).filter(CheckIn.event_id == event_id).all()
    
    # 創建出席狀況列表
    attendance_list = []
    checked_in_user_ids = [checkin.user_id for checkin, _ in checked_in_users]
    
    for user in all_users:
        is_checked_in = user.id in checked_in_user_ids
        checkin_record = None
        if is_checked_in:
            checkin_record = CheckIn.query.filter_by(
                user_id=user.id, 
                event_id=event_id
            ).first()
        
        attendance_list.append({
            'user': user,
            'is_checked_in': is_checked_in,
            'checkin_record': checkin_record
        })
    
    return render_template('event_detail.html', 
                         event=event, 
                         user_checkin=user_checkin,
                         all_users=all_users,
                         attendance_list=attendance_list,
                         now=datetime.now(),
                         has_permission=has_permission)  # 新增：當前時間

@app.route('/event/<int:event_id>/checkin', methods=['POST'])
def event_checkin(event_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'success': False, 'message': '活動不存在！'})
    
    # 檢查活動時間
    now = datetime.now()
    if event.end_time < now:
        return jsonify({'success': False, 'message': '活動已結束，無法簽到！'})
    
    if event.start_time > now:
        return jsonify({'success': False, 'message': '活動尚未開始，無法簽到！'})
    
    # 獲取選擇的用戶ID
    selected_user_id = request.form.get('checkin_user')
    if not selected_user_id:
        return jsonify({'success': False, 'message': '請選擇簽到人員！'})
    
    selected_user_id = int(selected_user_id)
    
    # 檢查是否已經在此活動簽到
    existing_checkin = CheckIn.query.filter(
        CheckIn.user_id == selected_user_id,
        CheckIn.event_id == event_id
    ).first()
    
    if existing_checkin:
        return jsonify({'success': False, 'message': '該人員已經在此活動簽到過了！'})
    
    # 創建活動簽到記錄
    checkin = CheckIn(
        user_id=selected_user_id,
        event_id=event_id,
        location=request.form.get('location', event.location),
        notes=request.form.get('notes', '')
    )
    
    db.session.add(checkin)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '活動簽到成功！'})

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('權限不足！', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()
    checkins = CheckIn.query.order_by(CheckIn.check_in_time.desc()).limit(20).all()
    events = Event.query.all()
    
    # 計算統計數據
    attendance_rate = 0
    if users:
        total_checkins = CheckIn.query.count()
        total_users = len(users)
        attendance_rate = min(100, int((total_checkins / (total_users * 30)) * 100)) if total_users > 0 else 0
    
    return render_template('admin.html', users=users, checkins=checkins, events=events, attendance_rate=attendance_rate, has_permission=has_permission)

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    users = User.query.all()
    user_list = []
    
    for user in users:
        user_list.append({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'is_admin': user.is_admin,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'success': True, 'users': user_list})

@app.route('/admin/users/<int:user_id>')
def get_user_detail(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': '用戶不存在'})
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'line_id': user.line_id,
            'position': user.position,
            'is_admin': user.is_admin,
            'can_add_events': user.can_add_events,
            'can_edit_events': user.can_edit_events,
            'can_delete_events': user.can_delete_events,
            'can_manage_users': user.can_manage_users,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@app.route('/admin/checkins')
def admin_checkins():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    checkins = CheckIn.query.order_by(CheckIn.check_in_time.desc()).all()
    checkin_list = []
    
    for checkin in checkins:
        user = db.session.get(User, checkin.user_id)
        checkin_list.append({
            'id': checkin.id,
            'user_name': user.name if user else 'Unknown',
            'check_in_time': checkin.check_in_time.strftime('%Y-%m-%d %H:%M:%S'),
            'check_out_time': checkin.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if checkin.check_out_time else None,
            'location': checkin.location,
            'status': checkin.status
        })
    
    return jsonify({'success': True, 'checkins': checkin_list})

@app.route('/admin/events/add', methods=['POST'])
def add_event():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    # 檢查權限
    if not has_permission('add_events'):
        return jsonify({'success': False, 'message': '權限不足，無法新增活動'})
    
    try:
        title = request.form['title']
        description = request.form['description']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        location = request.form['location']
        organizer_id = request.form.get('organizer_id')
        max_participants = request.form.get('max_participants')
        
        if not title or not start_time or not end_time or not location or not organizer_id:
            return jsonify({'success': False, 'message': '請填寫所有必填欄位'})
        
        # 檢查發起人是否存在
        organizer = db.session.get(User, organizer_id)
        if not organizer:
            return jsonify({'success': False, 'message': '發起人不存在'})
        
        event = Event(
            title=title,
            description=description,
            location=location,
            organizer_id=organizer_id,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            max_participants=int(max_participants) if max_participants else 0
        )
        
        db.session.add(event)
        db.session.commit()
        return jsonify({'success': True, 'message': '活動新增成功！'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'新增失敗：{str(e)}'})

@app.route('/admin/events/fix_organizers', methods=['POST'])
def fix_event_organizers():
    """修復現有活動的發起人設置"""
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        # 獲取所有沒有發起人的活動
        events_without_organizer = Event.query.filter_by(organizer_id=None).all()
        
        # 獲取第一個管理員作為默認發起人
        default_organizer = User.query.filter_by(is_admin=True).first()
        
        if not default_organizer:
            return jsonify({'success': False, 'message': '沒有找到管理員用戶'})
        
        # 修復所有沒有發起人的活動
        for event in events_without_organizer:
            event.organizer_id = default_organizer.id
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'已修復 {len(events_without_organizer)} 個活動的發起人設置'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'修復失敗：{str(e)}'})

@app.route('/admin/events/edit/<int:event_id>', methods=['POST'])
def admin_edit_event(event_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    # 檢查權限
    if not has_permission('edit_events'):
        return jsonify({'success': False, 'message': '權限不足，無法編輯活動'})
    
    try:
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify({'success': False, 'message': '活動不存在'})
        
        title = request.form.get('title')
        description = request.form.get('description', '')
        location = request.form.get('location')
        organizer_id = request.form.get('organizer_id')  # 新增：發起人ID
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        max_participants = request.form.get('max_participants')
        
        if not title or not location or not organizer_id or not start_time or not end_time:
            return jsonify({'success': False, 'message': '請填寫所有必填欄位'})
        
        # 檢查發起人是否存在
        organizer = db.session.get(User, organizer_id)
        if not organizer:
            return jsonify({'success': False, 'message': '發起人不存在'})
        
        # 如果不是管理員，只能編輯自己發起的活動
        if not session.get('is_admin') and event.organizer_id != session['user_id']:
            return jsonify({'success': False, 'message': '只能編輯自己發起的活動'})
        
        # 如果不是管理員，發起人必須是自己
        if not session.get('is_admin') and organizer_id != str(session['user_id']):
            return jsonify({'success': False, 'message': '只能將自己設為發起人'})
        
        # 更新活動
        event.title = title
        event.description = description
        event.location = location
        event.organizer_id = organizer_id  # 新增：更新發起人
        event.start_time = datetime.fromisoformat(start_time)
        event.end_time = datetime.fromisoformat(end_time)
        event.max_participants = int(max_participants) if max_participants else 0 # 新增：更新參與人數限制
        
        db.session.commit()
        return jsonify({'success': True, 'message': '活動更新成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新活動失敗：{str(e)}'})

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
def admin_delete_event(event_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    # 檢查權限
    if not has_permission('delete_events'):
        return jsonify({'success': False, 'message': '權限不足，無法刪除活動'})
    
    try:
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify({'success': False, 'message': '活動不存在'})
        
        # 如果不是管理員，只能刪除自己發起的活動
        if not session.get('is_admin') and event.organizer_id != session['user_id']:
            return jsonify({'success': False, 'message': '只能刪除自己發起的活動'})
        
        # 刪除相關的簽到記錄
        CheckIn.query.filter_by(event_id=event_id).delete()
        
        # 刪除活動
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '活動刪除成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'刪除活動失敗：{str(e)}'})

@app.route('/admin/users/add', methods=['POST'])
def add_user():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        line_id = request.form['line_id']
        position = request.form['position']
        
        # 檢查用戶名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用戶名已存在'})
        
        # 檢查姓名格式
        if '/' not in name:
            return jsonify({'success': False, 'message': '姓名格式錯誤，請使用「編號/姓名/專業別」格式'})
        
        # 創建新用戶
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            name=name,
            email=email,
            phone=phone,
            line_id=line_id,
            position=position,
            can_add_events='can_add_events' in request.form,
            can_edit_events='can_edit_events' in request.form,
            can_delete_events='can_delete_events' in request.form,
            can_manage_users='can_manage_users' in request.form,
            is_admin=False
        )
        
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': '用戶新增成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'新增失敗：{str(e)}'})

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': '用戶不存在'})
    
    try:
        # 用戶名不應該被修改，所以不從表單獲取
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        user.line_id = request.form['line_id']
        user.position = request.form['position']
        
        # 處理權限設定
        user.can_add_events = 'can_add_events' in request.form
        user.can_edit_events = 'can_edit_events' in request.form
        user.can_delete_events = 'can_delete_events' in request.form
        user.can_manage_users = 'can_manage_users' in request.form
        
        # 檢查姓名格式
        if '/' not in user.name:
            return jsonify({'success': False, 'message': '姓名格式錯誤，請使用「編號/姓名/專業別」格式'})
        
        # 如果提供了新密碼，則更新密碼
        new_password = request.form.get('new_password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '用戶更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失敗：{str(e)}'})

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'message': '用戶不存在'})
        
        # 不能刪除自己
        if user.id == session['user_id']:
            return jsonify({'success': False, 'message': '不能刪除自己的帳號'})
        
        # 刪除相關的簽到記錄
        CheckIn.query.filter_by(user_id=user_id).delete()
        
        # 刪除用戶
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '成員刪除成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'刪除成員失敗：{str(e)}'})

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': '沒有選擇檔案'})
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'message': '沒有選擇檔案'})
    
    if file and allowed_file(file.filename):
        try:
            # 生成安全的檔案名
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session['user_id']}_{timestamp}_{filename}"
            
            # 確保 avatars 目錄存在
            avatar_dir = os.path.join(app.static_folder, 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # 保存檔案
            file_path = os.path.join(avatar_dir, filename)
            file.save(file_path)
            
            # 更新用戶資料庫
            user = db.session.get(User, session['user_id'])
            if user:
                # 刪除舊頭像檔案
                if user.avatar:
                    old_avatar_path = os.path.join(avatar_dir, user.avatar)
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)
                
                user.avatar = filename
                db.session.commit()
                
                return jsonify({'success': True, 'message': '頭像上傳成功！'})
            else:
                return jsonify({'success': False, 'message': '用戶不存在'})
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'上傳失敗：{str(e)}'})
    else:
        return jsonify({'success': False, 'message': '不支援的檔案格式'})

@app.route('/api/user/<int:user_id>/avatar')
def get_user_avatar(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': '用戶不存在'})
    
    return jsonify({
        'success': True,
        'avatar': user.avatar,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'line_id': user.line_id,
        'position': user.position  # 新增：職級
    })

# 初始化數據庫和管理員帳號
with app.app_context():
    try:
        db.create_all()
        
        # 創建管理員帳號（如果不存在）
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                name='001/管理員/系統管理員',
                email='admin@example.com',
                is_admin=True,
                can_add_events=True,
                can_edit_events=True,
                can_delete_events=True,
                can_manage_users=True
            )
            db.session.add(admin)
            db.session.commit()
            print("管理員帳號已創建")
    except Exception as e:
        print(f"數據庫初始化錯誤：{e}")
        # 在生產環境中，如果數據庫初始化失敗，我們仍然要讓應用運行
        pass

if __name__ == '__main__':
    # 開發環境使用 debug 模式，生產環境不使用
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 