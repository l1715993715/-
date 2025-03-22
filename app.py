# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# 创建应用实例
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 导入数据库和模型
from models import db, User, Task, Project, project_members

# 初始化数据库
db.init_app(app)

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误！', 'danger')
    
    return render_template('auth/login.html')

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户名或邮箱是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册！', 'danger')
            return render_template('auth/register.html')
        
        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

# 登出路由
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('您已成功登出！', 'success')
    return redirect(url_for('index'))

# 仪表盘路由
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # 获取用户的任务
    tasks = Task.query.filter_by(assignee_id=user.id).order_by(Task.due_date).all()
    
    # 获取用户的项目
    user_projects = db.session.query(Project).join(project_members).filter(
        project_members.c.user_id == user.id
    ).all()
    
    # 统计数据
    stats = {
        'total_tasks': len(tasks),
        'completed_tasks': len([t for t in tasks if t.status == 'completed']),
        'pending_tasks': len([t for t in tasks if t.status == 'pending']),
        'total_projects': len(user_projects)
    }
    
    return render_template('dashboard/dashboard.html', user=user, tasks=tasks, 
                           projects=user_projects, stats=stats)

# 任务相关路由
@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # 处理任务创建
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        due_date_str = request.form.get('due_date')
        project_id = request.form.get('project_id')
        
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        
        # 创建新任务
        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            project_id=project_id if project_id else None,
            creator_id=user.id,
            assignee_id=user.id,
            status='pending'
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash('任务创建成功！', 'success')
        return redirect(url_for('tasks'))
    
    # 获取任务列表
    tasks = Task.query.filter_by(assignee_id=user.id).order_by(Task.due_date).all()
    projects = Project.query.join(project_members).filter(project_members.c.user_id == user.id).all()
    
    return render_template('dashboard/tasks.html', tasks=tasks, projects=projects)

# 编辑任务
@app.route('/tasks/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    # 确保只有任务创建者或负责人可以编辑
    if task.creator_id != session['user_id'] and task.assignee_id != session['user_id']:
        flash('您无权编辑此任务！', 'danger')
        return redirect(url_for('tasks'))
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.priority = request.form.get('priority')
        task.status = request.form.get('status')
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        else:
            task.due_date = None
            
        project_id = request.form.get('project_id')
        task.project_id = project_id if project_id else None
        
        db.session.commit()
        flash('任务更新成功！', 'success')
        return redirect(url_for('tasks'))
    
    projects = Project.query.join(project_members).filter(
        project_members.c.user_id == session['user_id']
    ).all()
    
    return render_template('dashboard/tasks.html', task=task, projects=projects, edit_mode=True)

# 删除任务
@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    # 确保只有任务创建者可以删除
    if task.creator_id != session['user_id']:
        flash('您无权删除此任务！', 'danger')
        return redirect(url_for('tasks'))
    
    db.session.delete(task)
    db.session.commit()
    flash('任务已删除！', 'success')
    return redirect(url_for('tasks'))

# 项目相关路由
@app.route('/projects', methods=['GET', 'POST'])
def projects():
    if 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # 处理项目创建
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # 创建新项目
        new_project = Project(
            name=name,
            description=description,
            owner_id=user.id
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        # 添加创建者为项目成员
        new_project.members.append(user)
        
        # 添加其他成员
        member_ids = request.form.getlist('members')
        for member_id in member_ids:
            member = User.query.get(member_id)
            if member:
                new_project.members.append(member)
        
        db.session.commit()
        flash('项目创建成功！', 'success')
        return redirect(url_for('projects'))
    
    # 获取项目列表
    user_projects = Project.query.join(project_members).filter(
        project_members.c.user_id == user.id
    ).all()
    
    # 获取可添加的用户
    all_users = User.query.filter(User.id != user.id).all()
    
    return render_template('dashboard/projects.html', projects=user_projects, users=all_users)

# 编辑项目
@app.route('/projects/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    # 确保只有项目创建者可以编辑
    if project.owner_id != session['user_id']:
        flash('您无权编辑此项目！', 'danger')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        
        # 更新项目成员
        current_members = set([member.id for member in project.members])
        new_members = set([int(id) for id in request.form.getlist('members')])
        
        # 添加新成员
        for member_id in new_members - current_members:
            member = User.query.get(member_id)
            if member:
                project.members.append(member)
        
        # 移除旧成员
        for member_id in current_members - new_members - {project.owner_id}:
            member = User.query.get(member_id)
            if member:
                project.members.remove(member)
        
        db.session.commit()
        flash('项目更新成功！', 'success')
        return redirect(url_for('projects'))
    
    all_users = User.query.filter(User.id != session['user_id']).all()
    
    return render_template('dashboard/projects.html', project=project, users=all_users, edit_mode=True)

# 删除项目
@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    if project.owner_id != session['user_id']:
        flash('您无权删除此项目！', 'danger')
        return redirect(url_for('projects'))
    
    Task.query.filter_by(project_id=project.id).delete()
    
    db.session.delete(project)
    db.session.commit()
    flash('项目已删除！', 'success')
    return redirect(url_for('projects'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
