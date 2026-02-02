import os
from datetime import datetime, date, timedelta
from calendar import monthrange
from flask import Flask, render_template, request, jsonify
from models import db, User, PushupRecord
from whitenoise import WhiteNoise
import holidays

app = Flask(__name__)

# 정적 파일 서빙 (배포 환경)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

# 설정
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# DATABASE_URL 처리 (Render/Supabase 호환성)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///pushups.db')
# Render는 postgres://를 사용하지만 SQLAlchemy + psycopg3는 postgresql+psycopg://를 요구
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# DB 초기화
db.init_app(app)

# 한국 공휴일
kr_holidays = holidays.KR()


def is_workday(check_date):
    """평일인지 확인 (주말과 공휴일 제외)"""
    # 주말 체크 (토요일=5, 일요일=6)
    if check_date.weekday() >= 5:
        return False
    # 공휴일 체크
    if check_date in kr_holidays:
        return False
    return True


def get_month_workdays(year, month):
    """해당 월의 모든 평일 목록 반환"""
    workdays = []
    _, last_day = monthrange(year, month)

    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        # 미래 날짜는 제외
        if current_date > date.today():
            break
        if is_workday(current_date):
            workdays.append(current_date)

    return workdays


def calculate_penalty(user_id, year, month):
    """벌금 계산 (미체크 평일 * 10000원)"""
    workdays = get_month_workdays(year, month)

    # 해당 월의 완료된 기록 조회
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    completed_dates = db.session.query(PushupRecord.date).filter(
        PushupRecord.user_id == user_id,
        PushupRecord.date >= start_date,
        PushupRecord.date <= end_date,
        PushupRecord.completed == True
    ).all()
    completed_dates = [r[0] for r in completed_dates]

    # 미완료 평일 수 계산
    missed_days = [d for d in workdays if d not in completed_dates]
    penalty = len(missed_days) * 10000

    return penalty, len(missed_days), len(workdays)


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/login', methods=['POST'])
def login():
    """로그인 (이름으로)"""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': '이름을 입력해주세요'}), 400

    # 기존 유저 찾기 또는 새로 생성
    user = User.query.filter_by(name=name).first()
    if not user:
        user = User(name=name)
        db.session.add(user)
        db.session.commit()

    return jsonify({
        'id': user.id,
        'name': user.name
    })


@app.route('/api/calendar/<int:year>/<int:month>')
def get_calendar(year, month):
    """캘린더 데이터 조회"""
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': '로그인이 필요합니다'}), 401

    # 해당 월의 기록 조회
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    records = PushupRecord.query.filter(
        PushupRecord.user_id == user_id,
        PushupRecord.date >= start_date,
        PushupRecord.date <= end_date
    ).all()

    completed_dates = [r.date.isoformat() for r in records if r.completed]

    # 공휴일 정보
    holiday_dates = []
    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        if current_date in kr_holidays:
            holiday_dates.append({
                'date': current_date.isoformat(),
                'name': kr_holidays.get(current_date)
            })

    # 벌금 계산
    penalty, missed_days, total_workdays = calculate_penalty(user_id, year, month)

    return jsonify({
        'year': year,
        'month': month,
        'completed_dates': completed_dates,
        'holidays': holiday_dates,
        'penalty': penalty,
        'missed_days': missed_days,
        'total_workdays': total_workdays,
        'first_day_weekday': date(year, month, 1).weekday(),
        'last_day': last_day
    })


@app.route('/api/toggle', methods=['POST'])
def toggle_completion():
    """완료 상태 토글"""
    data = request.get_json()
    user_id = data.get('user_id')
    date_str = data.get('date')

    if not user_id or not date_str:
        return jsonify({'error': '필수 정보가 누락되었습니다'}), 400

    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # 오늘 날짜만 토글 가능
    if target_date != date.today():
        return jsonify({'error': '오늘 날짜만 체크할 수 있습니다'}), 400

    # 기존 기록 확인
    record = PushupRecord.query.filter_by(
        user_id=user_id,
        date=target_date
    ).first()

    if record:
        # 기존 기록이 있으면 삭제 (토글 off)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'completed': False})
    else:
        # 새 기록 생성 (토글 on)
        record = PushupRecord(user_id=user_id, date=target_date, completed=True)
        db.session.add(record)
        db.session.commit()
        return jsonify({'completed': True})


@app.route('/api/ranking')
def get_ranking():
    """벌금 랭킹 (명예의 전당)"""
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', date.today().month, type=int)

    # 해당 월 범위
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    users = User.query.all()
    rankings = []

    for user in users:
        penalty, missed_days, total_workdays = calculate_penalty(user.id, year, month)
        completed_days = total_workdays - missed_days

        # 해당 월의 첫 체크 시간 조회 (먼저 체크한 사람 우선)
        first_record = PushupRecord.query.filter(
            PushupRecord.user_id == user.id,
            PushupRecord.date >= start_date,
            PushupRecord.date <= end_date
        ).order_by(PushupRecord.created_at.asc()).first()

        first_check_time = first_record.created_at if first_record else datetime.max

        rankings.append({
            'id': user.id,
            'name': user.name,
            'penalty': penalty,
            'completed_days': completed_days,
            'total_workdays': total_workdays,
            'completion_rate': round(completed_days / total_workdays * 100, 1) if total_workdays > 0 else 0,
            'first_check_time': first_check_time
        })

    # 정렬: 벌금 적은 순 → 먼저 체크한 순
    rankings.sort(key=lambda x: (x['penalty'], x['first_check_time']))

    # 순위 부여 (1, 2, 3등 순차적으로)
    for i, r in enumerate(rankings):
        r['rank'] = i + 1
        # first_check_time은 JSON 직렬화에서 제외
        del r['first_check_time']

    return jsonify(rankings)


@app.route('/api/available-months')
def get_available_months():
    """조회 가능한 월 목록"""
    today = date.today()
    months = []

    # 최근 12개월
    for i in range(12):
        year = today.year
        month = today.month - i

        while month <= 0:
            month += 12
            year -= 1

        months.append({
            'year': year,
            'month': month,
            'label': f'{year}년 {month}월'
        })

    return jsonify(months)


# DB 테이블 생성
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
