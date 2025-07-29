from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# 創建 Flask 應用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checkin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 檔案上傳配置
app.config['UPLOAD_FOLDER'] = 'static/uploads/avatars'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 確保上傳資料夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

# 路由
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # 獲取今日簽到記錄
    today = datetime.now().date()
    today_checkin = CheckIn.query.filter(
        CheckIn.user_id == session['user_id'],
        db.func.date(CheckIn.check_in_time) == today
    ).first()
    
    # 獲取本月統計
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    checkin_count = CheckIn.query.filter(
        CheckIn.user_id == session['user_id'],
        CheckIn.check_in_time >= start_of_month
    ).count()
    
    # 獲取活動統計
    event_count = Event.query.filter(Event.start_time >= start_of_month).count()
    
    # 計算出勤率
    total_days = (datetime.now() - start_of_month).days + 1
    attendance_rate = round((checkin_count / total_days) * 100, 1) if total_days > 0 else 0
    
    # 獲取即將到來的活動
    upcoming_events = Event.query.filter(
        Event.start_time >= datetime.now()
    ).order_by(Event.start_time).limit(3).all()
    
    return render_template('index.html', 
                         user=user, 
                         today_checkin=today_checkin,
                         checkin_count=checkin_count,
                         event_count=event_count,
                         attendance_rate=attendance_rate,
                         upcoming_events=upcoming_events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session['name'] = user.name
            flash('登入成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用戶名或密碼錯誤', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('已登出', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        line_id = request.form.get('line_id', '')
        position = request.form.get('position', '')
        
        # 檢查用戶名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用戶名已存在', 'error')
            return render_template('register.html', position_options=POSITION_OPTIONS)
        
        # 創建新用戶
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            name=name,
            email=email,
            phone=phone,
            line_id=line_id,
            position=position
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('註冊成功！請登入', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', position_options=POSITION_OPTIONS)

@app.route('/checkin', methods=['POST'])
def checkin():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    # 檢查今日是否已簽到
    today = datetime.now().date()
    existing_checkin = CheckIn.query.filter(
        CheckIn.user_id == session['user_id'],
        db.func.date(CheckIn.check_in_time) == today
    ).first()
    
    if existing_checkin:
        return jsonify({'success': False, 'message': '今日已簽到'})
    
    # 創建簽到記錄
    location = request.form.get('location', '')
    notes = request.form.get('notes', '')
    
    checkin = CheckIn(
        user_id=session['user_id'],
        location=location,
        notes=notes
    )
    
    db.session.add(checkin)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '簽到成功！'})

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    # 獲取今日簽到記錄
    today = datetime.now().date()
    checkin = CheckIn.query.filter(
        CheckIn.user_id == session['user_id'],
        db.func.date(CheckIn.check_in_time) == today
    ).first()
    
    if not checkin:
        return jsonify({'success': False, 'message': '今日尚未簽到'})
    
    if checkin.check_out_time:
        return jsonify({'success': False, 'message': '今日已簽退'})
    
    # 更新簽退時間
    checkin.check_out_time = datetime.now()
    checkin.status = 'checked_out'
    db.session.commit()
    
    return jsonify({'success': True, 'message': '簽退成功！'})

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('請先登入', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('用戶不存在', 'error')
        return redirect(url_for('login'))
    
    # 獲取簽到統計
    checkin_count = CheckIn.query.filter_by(user_id=session['user_id']).count()
    organized_events = Event.query.filter_by(organizer_id=session['user_id']).count()
    
    # 獲取最近的簽到記錄
    recent_checkins = CheckIn.query.filter_by(user_id=session['user_id']).order_by(CheckIn.check_in_time.desc()).limit(10).all()
    
    return render_template('profile.html', 
                         user=user, 
                         checkin_count=checkin_count,
                         organized_events=organized_events,
                         recent_checkins=recent_checkins)

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
    
    checkin_count = CheckIn.query.filter_by(user_id=user_id).count()
    organized_events = Event.query.filter_by(organizer_id=user_id).order_by(Event.created_at.desc()).limit(5).all()
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
        flash('請先登入', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('用戶不存在', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form.get('email', '')
        user.phone = request.form.get('phone', '')
        user.line_id = request.form.get('line_id', '')
        user.position = request.form.get('position', '')
        user.bio = request.form.get('bio', '')
        
        db.session.commit()
        flash('個人資料更新成功！', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user, position_options=POSITION_OPTIONS)

@app.route('/events')
def events():
    if 'user_id' not in session:
        flash('請先登入', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    events = Event.query.order_by(Event.start_time.desc()).all()
    users = User.query.all()
    
    return render_template('events.html', events=events, users=users, has_permission=has_permission)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    if 'user_id' not in session:
        flash('請先登入', 'error')
        return redirect(url_for('login'))
    
    event = db.session.get(Event, event_id)
    if not event:
        flash('活動不存在', 'error')
        return redirect(url_for('events'))
    
    # 檢查用戶是否已簽到
    user_checkin = CheckIn.query.filter_by(
        user_id=session['user_id'],
        event_id=event_id
    ).first()
    
    return render_template('event_detail.html', 
                         event=event, 
                         user_checkin=user_checkin,
                         has_permission=has_permission)

@app.route('/event/<int:event_id>/checkin', methods=['POST'])
def event_checkin(event_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'success': False, 'message': '活動不存在'})
    
    # 檢查是否已簽到
    existing_checkin = CheckIn.query.filter_by(
        user_id=session['user_id'],
        event_id=event_id
    ).first()
    
    if existing_checkin:
        return jsonify({'success': False, 'message': '您已簽到過此活動'})
    
    # 創建簽到記錄
    location = request.form.get('location', '')
    notes = request.form.get('notes', '')
    
    checkin = CheckIn(
        user_id=session['user_id'],
        event_id=event_id,
        location=location,
        notes=notes
    )
    
    db.session.add(checkin)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '活動簽到成功！'})

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('權限不足', 'error')
        return redirect(url_for('index'))
    
    # 獲取統計數據
    total_users = User.query.count()
    total_events = Event.query.count()
    total_checkins = CheckIn.query.count()
    
    # 獲取最近的活動
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    
    # 獲取最近的簽到記錄
    recent_checkins = CheckIn.query.order_by(CheckIn.check_in_time.desc()).limit(10).all()
    
    return render_template('admin.html', 
                         total_users=total_users,
                         total_events=total_events,
                         total_checkins=total_checkins,
                         recent_events=recent_events,
                         recent_checkins=recent_checkins)

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/<int:user_id>')
def get_user_detail(user_id):
    """獲取用戶詳細信息（用於 AJAX）"""
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
            'bio': user.bio,
            'can_add_events': user.can_add_events,
            'can_edit_events': user.can_edit_events,
            'can_delete_events': user.can_delete_events,
            'can_manage_users': user.can_manage_users,
            'is_admin': user.is_admin
        }
    })

@app.route('/admin/checkins')
def admin_checkins():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    checkins = CheckIn.query.order_by(CheckIn.check_in_time.desc()).all()
    return render_template('admin_checkins.html', checkins=checkins)

@app.route('/admin/events/add', methods=['POST'])
def add_event():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    try:
        title = request.form['title']
        description = request.form['description']
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        location = request.form['location']
        max_participants = int(request.form.get('max_participants', 0))
        organizer_id = int(request.form['organizer_id'])
        
        # 驗證發起人是否存在
        organizer = db.session.get(User, organizer_id)
        if not organizer:
            return jsonify({'success': False, 'message': '發起人不存在'})
        
        event = Event(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            organizer_id=organizer_id,
            max_participants=max_participants
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '活動新增成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'新增活動失敗：{str(e)}'})

@app.route('/admin/events/fix_organizers', methods=['POST'])
def fix_event_organizers():
    """修復現有活動的發起人設置"""
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        events_without_organizer = Event.query.filter_by(organizer_id=None).all()
        default_organizer = User.query.filter_by(is_admin=True).first()
        
        if not default_organizer:
            return jsonify({'success': False, 'message': '沒有找到管理員用戶'})
        
        for event in events_without_organizer:
            event.organizer_id = default_organizer.id
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'已修復 {len(events_without_organizer)} 個活動的發起人設置'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'修復失敗：{str(e)}'})

@app.route('/admin/events/edit/<int:event_id>', methods=['POST'])
def admin_edit_event(event_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    try:
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify({'success': False, 'message': '活動不存在'})
        
        # 權限檢查
        current_user = db.session.get(User, session['user_id'])
        if not current_user.is_admin and event.organizer_id != session['user_id']:
            return jsonify({'success': False, 'message': '權限不足'})
        
        title = request.form['title']
        description = request.form['description']
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        location = request.form['location']
        max_participants = int(request.form.get('max_participants', 0))
        organizer_id = int(request.form['organizer_id'])
        
        # 驗證發起人是否存在
        organizer = db.session.get(User, organizer_id)
        if not organizer:
            return jsonify({'success': False, 'message': '發起人不存在'})
        
        event.title = title
        event.description = description
        event.start_time = start_time
        event.end_time = end_time
        event.location = location
        event.organizer_id = organizer_id
        event.max_participants = max_participants
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '活動更新成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新活動失敗：{str(e)}'})

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
def admin_delete_event(event_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    try:
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify({'success': False, 'message': '活動不存在'})
        
        # 權限檢查
        current_user = db.session.get(User, session['user_id'])
        if not current_user.is_admin and event.organizer_id != session['user_id']:
            return jsonify({'success': False, 'message': '權限不足'})
        
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
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        line_id = request.form.get('line_id', '')
        position = request.form.get('position', '')
        
        # 檢查用戶名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用戶名已存在'})
        
        # 創建新用戶
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            name=name,
            email=email,
            phone=phone,
            line_id=line_id,
            position=position,
            can_add_events=request.form.get('can_add_events') == 'on',
            can_edit_events=request.form.get('can_edit_events') == 'on',
            can_delete_events=request.form.get('can_delete_events') == 'on',
            can_manage_users=request.form.get('can_manage_users') == 'on',
            is_admin=request.form.get('is_admin') == 'on'
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '成員新增成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'新增成員失敗：{str(e)}'})

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'message': '用戶不存在'})
        
        user.name = request.form['name']
        user.email = request.form.get('email', '')
        user.phone = request.form.get('phone', '')
        user.line_id = request.form.get('line_id', '')
        user.position = request.form.get('position', '')
        user.bio = request.form.get('bio', '')
        user.can_add_events = request.form.get('can_add_events') == 'on'
        user.can_edit_events = request.form.get('can_edit_events') == 'on'
        user.can_delete_events = request.form.get('can_delete_events') == 'on'
        user.can_manage_users = request.form.get('can_manage_users') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'
        
        # 如果提供了新密碼，則更新密碼
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '成員更新成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新成員失敗：{str(e)}'})

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

# 導出 Flask 應用給 Vercel
handler = app 