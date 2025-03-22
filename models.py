# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 创建数据库实例，但不初始化
db = SQLAlchemy()

# 项目成员关联表
project_members = db.Table('project_members',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    created_tasks = db.relationship('Task', backref='creator', lazy=True, foreign_keys='Task.creator_id')
    assigned_tasks = db.relationship('Task', backref='assignee', lazy=True, foreign_keys='Task.assignee_id')
    owned_projects = db.relationship('Project', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    def __repr__(self):
        return f'<Task {self.title}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 关系
    tasks = db.relationship('Task', backref='project', lazy=True)
    members = db.relationship('User', secondary=project_members, lazy='subquery',
                              backref=db.backref('projects', lazy=True))

    def __repr__(self):
        return f'<Project {self.name}>'
