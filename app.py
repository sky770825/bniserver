from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checkin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 新增：發起人ID
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    max_participants = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 新增：與User的關聯
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
    today = datetime.now().date()
    
    # 獲取今日簽到記錄
    today_checkin = CheckIn.query.filter(
        CheckIn.user_id == session['user_id'],
        db.func.date(CheckIn.check_in_time) == today
    ).first()
    
    # 獲取最近的活動
    upcoming_events = Event.query.filter(
        Event.start_time >= datetime.now()
    ).order_by(Event.start_time).limit(5).all()
    
    # 獲取用戶註冊的活動
    user_events = EventRegistration.query.filter(
        EventRegistration.user_id == session['user_id']
    ).all()
    
    # 計算統計數據
    current_month = datetime.now().month
    checkin_count = CheckIn.query.filter(
        CheckIn.user_id == session['user_id'],
        db.func.extract('month', CheckIn.check_in_time) == current_month
    ).count()
    
    event_count = EventRegistration.query.filter(
        EventRegistration.user_id == session['user_id']
    ).count()
    
    # 計算出勤率（簡化計算）
    total_days = 30  # 假設一個月30天
    attendance_rate = min(100, int((checkin_count / total_days) * 100)) if total_days > 0 else 0
    
    return render_template('index.html', 
                         user=user, 
                         today_checkin=today_checkin,
                         upcoming_events=upcoming_events,
                         user_events=user_events,
                         checkin_count=checkin_count,
                         event_count=event_count,
                         attendance_rate=attendance_rate)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
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
        line_id = request.form.get('line_id', '')  # 新增：LINE ID
        
        if not username or not password or not name:
            flash('請填寫所有必填欄位', 'error')
            return render_template('register.html')
        
        # 檢查用戶名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用戶名已存在', 'error')
            return render_template('register.html')
        
        # 創建新用戶
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            name=name,
            email=email,
            phone=phone,
            line_id=line_id,  # 新增：LINE ID
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
    
    return render_template('profile.html', user=user, checkins=checkins)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    if request.method == 'POST':
        try:
            user.name = request.form.get('name', user.name)
            user.email = request.form.get('email', user.email)
            user.phone = request.form.get('phone', user.phone)
            user.line_id = request.form.get('line_id', user.line_id)  # 新增：LINE ID
            
            # 如果提供了新密碼，則更新密碼
            new_password = request.form.get('new_password')
            if new_password:
                user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            flash('個人資料更新成功！', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗：{str(e)}', 'error')
    
    return render_template('edit_profile.html', user=user)

@app.route('/events')
def events():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    events = Event.query.order_by(Event.created_at.desc()).all()
    all_users = User.query.all()  # 新增：獲取所有用戶列表
    return render_template('events.html', events=events, all_users=all_users)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    event = db.session.get(Event, event_id)
    if not event:
        flash('活動不存在！', 'error')
        return redirect(url_for('events'))
    
    # 檢查用戶是否已在此活動簽到
    user_checkin = CheckIn.query.filter(
        CheckIn.user_id == session['user_id'],
        CheckIn.event_id == event_id
    ).first()
    
    # 獲取活動參與者（包含用戶信息）
    participants = db.session.query(CheckIn, User).join(
        User, CheckIn.user_id == User.id
    ).filter(
        CheckIn.event_id == event_id
    ).all()
    
    # 獲取所有用戶列表（供簽到選擇）
    all_users = User.query.all()
    
    return render_template('event_detail.html', 
                         event=event, 
                         user_checkin=user_checkin,
                         participants=participants,
                         all_users=all_users)

@app.route('/event/<int:event_id>/checkin', methods=['POST'])
def event_checkin(event_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'})
    
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'success': False, 'message': '活動不存在！'})
    
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
    
    return render_template('admin.html', users=users, checkins=checkins, events=events, attendance_rate=attendance_rate)

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
def admin_add_event():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
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
        
        # 創建新活動
        event = Event(
            title=title,
            description=description,
            location=location,
            organizer_id=organizer_id,  # 新增：設置發起人
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            max_participants=int(max_participants) if max_participants else None
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '活動新增成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'新增活動失敗：{str(e)}'})

@app.route('/admin/events/edit/<int:event_id>', methods=['POST'])
def admin_edit_event(event_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
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
        
        # 更新活動
        event.title = title
        event.description = description
        event.location = location
        event.organizer_id = organizer_id  # 新增：更新發起人
        event.start_time = datetime.fromisoformat(start_time)
        event.end_time = datetime.fromisoformat(end_time)
        event.max_participants = int(max_participants) if max_participants else None
        
        db.session.commit()
        return jsonify({'success': True, 'message': '活動更新成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新活動失敗：{str(e)}'})

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
def admin_delete_event(event_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify({'success': False, 'message': '活動不存在'})
        
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
def admin_add_user():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        line_id = request.form.get('line_id', '')  # 新增：LINE ID
        
        if not username or not password or not name:
            return jsonify({'success': False, 'message': '請填寫所有必填欄位'})
        
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
            line_id=line_id,  # 新增：LINE ID
            is_admin=False
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '成員新增成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'新增成員失敗：{str(e)}'})

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
def admin_edit_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': '權限不足'})
    
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'message': '用戶不存在'})
        
        user.name = request.form.get('name', user.name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.line_id = request.form.get('line_id', user.line_id)  # 新增：LINE ID
        
        # 如果提供了新密碼，則更新密碼
        new_password = request.form.get('new_password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '成員資料更新成功！'})
        
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

if __name__ == '__main__':
    with app.app_context():
        # 刪除所有表並重新創建
        db.drop_all()
        db.create_all()
        
        # 創建管理員帳號（如果不存在）
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                name='管理員',
                email='admin@example.com',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 