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


class StockHolding(db.Model):
    """주식 보유 모델"""
    __tablename__ = 'stock_holdings'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    avg_price = db.Column(db.Float, nullable=False, default=0)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StockHolding {self.symbol} x{self.shares}>'


class CashAsset(db.Model):
    """현금 자산 모델 (단일 행)"""
    __tablename__ = 'cash_assets'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False, default=0)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CashAsset ₩{self.amount}>'


class SiteConfig(db.Model):
    """사이트 설정 (key-value)"""
    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Event(db.Model):
    """D-Day 이벤트 모델"""
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    participants = db.relationship('EventParticipant', backref='event', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Event {self.title}>'


class EventParticipant(db.Model):
    """이벤트 참석자 모델"""
    __tablename__ = 'event_participants'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', name='unique_event_user'),
    )
