from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# 创建应用实例
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 创建数据库实例
db = SQLAlchemy(app)

# 导入路由（在db创建后导入，避免循环导入）
from task_manager import routes
