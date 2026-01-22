from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.teo.v20220901 import teo_client, models

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Flask-Login配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据库路径
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'edgeone.db')

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 数据库初始化
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL)''')
    
    # 配置表
    c.execute('''CREATE TABLE IF NOT EXISTS configs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  secret_id TEXT NOT NULL,
                  secret_key TEXT NOT NULL,
                  zone_id TEXT NOT NULL,
                  region TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 创建默认管理员用户（如果不存在）
    default_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    password_hash = generate_password_hash(default_password)
    c.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                  ('admin', password_hash))
    
    conn.commit()
    conn.close()

# 用户类
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1])
    return None

# EdgeOne API调用
def call_edgeone_api(secret_id, secret_key, zone_id, region, purge_type, targets=None, method='delete'):
    """调用EdgeOne缓存清除API
    
    Args:
        secret_id: 腾讯云SecretId
        secret_key: 腾讯云SecretKey
        zone_id: 站点ID
        region: 区域 (cn/intl)
        purge_type: 清除类型 (purge_all/purge_url/purge_prefix/purge_host/purge_cache_tag)
        targets: 目标列表（可选）
        method: 清除方法 (invalidate=标记过期, delete=直接删除)
    """
    try:
        # 实例化认证对象
        cred = credential.Credential(secret_id, secret_key)
        
        # 实例化http选项
        httpProfile = HttpProfile()
        httpProfile.endpoint = "teo.tencentcloudapi.com"
        
        # 根据区域选择端点
        if region == 'intl':
            # 国际版可能需要不同的端点，根据实际情况调整
            httpProfile.endpoint = "teo.tencentcloudapi.com"
        
        # 实例化client选项
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        # 实例化要请求产品的client对象
        client = teo_client.TeoClient(cred, "", clientProfile)
        
        # 实例化请求对象
        req = models.CreatePurgeTaskRequest()
        req.ZoneId = zone_id
        req.Type = purge_type
        
        # 设置清除方法（Method参数对目录、主机名和全部清除有效）
        # URL和缓存标签类型默认为直接删除，但也可以设置Method
        if method and method in ['invalidate', 'delete']:
            req.Method = method
        
        # 设置目标
        if targets and isinstance(targets, list) and len(targets) > 0:
            req.Targets = targets
        elif targets and isinstance(targets, str):
            req.Targets = [targets]
        
        # 调用接口
        resp = client.CreatePurgeTask(req)
        
        # 返回结果
        return {
            'Response': {
                'JobId': resp.JobId if hasattr(resp, 'JobId') else None,
                'TaskId': resp.TaskId if hasattr(resp, 'TaskId') else None
            }
        }
    except Exception as e:
        error_msg = str(e)
        # 尝试提取错误代码和消息
        if hasattr(e, 'code'):
            error_code = e.code
        else:
            error_code = 'RequestError'
        
        return {'Error': {'Code': error_code, 'Message': error_msg}}

# 路由
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1])
            login_user(user)
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/configs', methods=['GET'])
@login_required
def get_configs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, secret_id, secret_key, zone_id, region, created_at, updated_at FROM configs ORDER BY updated_at DESC')
    configs = []
    for row in c.fetchall():
        configs.append({
            'id': row[0],
            'name': row[1],
            'secret_id': row[2][:8] + '***' if len(row[2]) > 8 else '***',  # 部分隐藏
            'secret_key': '***',
            'zone_id': row[4],
            'region': row[5],
            'created_at': row[6],
            'updated_at': row[7]
        })
    conn.close()
    return jsonify(configs)

@app.route('/api/configs', methods=['POST'])
@login_required
def create_config():
    data = request.json
    name = data.get('name', '未命名配置')
    secret_id = data.get('secret_id')
    secret_key = data.get('secret_key')
    zone_id = data.get('zone_id')
    region = data.get('region', 'cn')
    
    if not all([secret_id, secret_key, zone_id]):
        return jsonify({'success': False, 'message': '请填写所有必填字段'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO configs (name, secret_id, secret_key, zone_id, region)
                 VALUES (?, ?, ?, ?, ?)''',
              (name, secret_id, secret_key, zone_id, region))
    conn.commit()
    config_id = c.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': config_id})

@app.route('/api/configs/<int:config_id>', methods=['GET'])
@login_required
def get_config(config_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, secret_id, secret_key, zone_id, region FROM configs WHERE id = ?', (config_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'success': False, 'message': '配置不存在'}), 404
    
    return jsonify({
        'id': row[0],
        'name': row[1],
        'secret_id': row[2],
        'secret_key': row[3],
        'zone_id': row[4],
        'region': row[5]
    })

@app.route('/api/configs/<int:config_id>', methods=['PUT'])
@login_required
def update_config(config_id):
    data = request.json
    name = data.get('name')
    secret_id = data.get('secret_id')
    secret_key = data.get('secret_key')
    zone_id = data.get('zone_id')
    region = data.get('region')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 检查配置是否存在
    c.execute('SELECT id FROM configs WHERE id = ?', (config_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '配置不存在'}), 404
    
    # 更新配置
    updates = []
    values = []
    if name:
        updates.append('name = ?')
        values.append(name)
    if secret_id:
        updates.append('secret_id = ?')
        values.append(secret_id)
    if secret_key:
        updates.append('secret_key = ?')
        values.append(secret_key)
    if zone_id:
        updates.append('zone_id = ?')
        values.append(zone_id)
    if region:
        updates.append('region = ?')
        values.append(region)
    
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        values.append(config_id)
        c.execute(f'UPDATE configs SET {", ".join(updates)} WHERE id = ?', values)
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

@app.route('/api/configs/<int:config_id>', methods=['DELETE'])
@login_required
def delete_config(config_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM configs WHERE id = ?', (config_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    
    if not deleted:
        return jsonify({'success': False, 'message': '配置不存在'}), 404
    
    return jsonify({'success': True})

@app.route('/api/purge', methods=['POST'])
@login_required
def purge_cache():
    data = request.json
    config_id = data.get('config_id')
    purge_type = data.get('type', 'purge_all')
    targets = data.get('targets', [])
    method = data.get('method', 'delete')  # 默认为直接删除
    
    if not config_id:
        return jsonify({'success': False, 'message': '请选择配置'}), 400
    
    # 获取配置
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT secret_id, secret_key, zone_id, region FROM configs WHERE id = ?', (config_id,))
    config = c.fetchone()
    conn.close()
    
    if not config:
        return jsonify({'success': False, 'message': '配置不存在'}), 404
    
    secret_id, secret_key, zone_id, region = config
    
    # 调用API
    result = call_edgeone_api(secret_id, secret_key, zone_id, region, purge_type, targets if targets else None, method)
    
    if 'Error' in result:
        return jsonify({
            'success': False,
            'message': result['Error'].get('Message', 'API调用失败'),
            'code': result['Error'].get('Code', 'Unknown')
        }), 400
    
    method_text = '标记过期' if method == 'invalidate' else '直接删除'
    return jsonify({
        'success': True,
        'data': result.get('Response', {}),
        'message': f'缓存清除任务已提交（{method_text}）'
    })

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
