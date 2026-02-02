from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """사용자 모델"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계 설정
    records = db.relationship('PushupRecord', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'


class PushupRecord(db.Model):
    """푸시업 기록 모델"""
    __tablename__ = 'pushup_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 같은 유저가 같은 날짜에 중복 기록 방지
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_user_date'),
    )

    def __repr__(self):
        return f'<PushupRecord {self.user_id} - {self.date}>'
