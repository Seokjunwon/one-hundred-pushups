import os
import time
from datetime import datetime, date, timedelta
from calendar import monthrange
from flask import Flask, render_template, request, jsonify, send_from_directory
from models import db, User, PushupRecord, StockHolding, CashAsset, SiteConfig
from whitenoise import WhiteNoise
import holidays
import requests as http_requests

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

# 관리자 목록
ADMIN_USERS = ["원석준", "김병석"]

# Finnhub API 설정 (환경변수는 폴백용)
FINNHUB_API_KEY_ENV = os.environ.get('FINNHUB_API_KEY', '')


def get_finnhub_api_key():
    """DB에서 API 키 조회, 없으면 환경변수 폴백"""
    try:
        config = SiteConfig.query.filter_by(key='FINNHUB_API_KEY').first()
        if config and config.value:
            return config.value
    except Exception:
        pass
    return FINNHUB_API_KEY_ENV

# 주가 캐시 (60초 TTL)
_price_cache = {}
PRICE_CACHE_TTL = 60


def get_stock_price(symbol):
    """Finnhub에서 주가 조회 (캐시 포함)"""
    now = time.time()
    if symbol in _price_cache:
        cached_time, cached_data = _price_cache[symbol]
        if now - cached_time < PRICE_CACHE_TTL:
            return cached_data

    api_key = get_finnhub_api_key()
    if not api_key:
        return None

    try:
        resp = http_requests.get(
            f'https://finnhub.io/api/v1/quote',
            params={'symbol': symbol, 'token': api_key},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            result = {
                'c': data.get('c', 0),    # 현재가
                'dp': data.get('dp', 0),   # 변동률%
                'd': data.get('d', 0),     # 변동액
                'pc': data.get('pc', 0),   # 전일 종가
            }
            _price_cache[symbol] = (now, result)
            return result
    except Exception:
        pass

    return _price_cache.get(symbol, (0, None))[1]


# 환율 캐시 (5분 TTL)
_exchange_rate_cache = {'time': 0, 'rate': 0}
EXCHANGE_RATE_CACHE_TTL = 300


def get_usd_krw_rate():
    """USD/KRW 환율 조회 (캐시 포함)"""
    now = time.time()
    if _exchange_rate_cache['rate'] and now - _exchange_rate_cache['time'] < EXCHANGE_RATE_CACHE_TTL:
        return _exchange_rate_cache['rate']

    try:
        resp = http_requests.get(
            'https://open.er-api.com/v6/latest/USD',
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            rate = data.get('rates', {}).get('KRW', 0)
            if rate > 0:
                _exchange_rate_cache['time'] = now
                _exchange_rate_cache['rate'] = rate
                return rate
    except Exception:
        pass

    if _exchange_rate_cache['rate']:
        return _exchange_rate_cache['rate']
    return 1350  # 폴백 기본값


def is_admin(user_name):
    """관리자 여부 확인"""
    return user_name in ADMIN_USERS


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


@app.route('/manifest.json')
def manifest():
    """PWA manifest 파일"""
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')


@app.route('/service-worker.js')
def service_worker():
    """서비스 워커 파일 (루트에서 제공해야 스코프가 전체 사이트)"""
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')


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
        'name': user.name,
        'is_admin': is_admin(user.name)
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

    # 미래 날짜는 체크 불가
    if target_date > date.today():
        return jsonify({'error': '미래 날짜는 체크할 수 없습니다'}), 400

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


@app.route('/api/assets')
def get_assets():
    """전체 자산 조회 (실시간 주가 + 환율 포함)"""
    stocks = StockHolding.query.all()
    stock_list = []
    total_stock_value_usd = 0

    usd_krw = get_usd_krw_rate()
    now_str = datetime.utcnow().strftime('%Y.%m.%d %H:%M')

    for s in stocks:
        price_data = get_stock_price(s.symbol)
        current_price = price_data['c'] if price_data else 0
        change_percent = price_data['dp'] if price_data else 0
        value_usd = current_price * s.shares
        value_krw = round(value_usd * usd_krw)
        total_stock_value_usd += value_usd

        stock_list.append({
            'id': s.id,
            'symbol': s.symbol,
            'shares': s.shares,
            'current_price': current_price,
            'change_percent': round(change_percent, 2),
            'value_usd': round(value_usd, 2),
            'value_krw': value_krw,
        })

    cash = CashAsset.query.first()
    cash_krw = cash.amount if cash else 0
    total_stock_krw = round(total_stock_value_usd * usd_krw)
    total_assets_krw = total_stock_krw + cash_krw

    return jsonify({
        'stocks': stock_list,
        'cash_krw': cash_krw,
        'total_stock_usd': round(total_stock_value_usd, 2),
        'total_stock_krw': total_stock_krw,
        'total_assets_krw': total_assets_krw,
        'usd_krw': round(usd_krw, 2),
        'updated_at': now_str,
    })


@app.route('/api/stock-price/<symbol>')
def get_stock_price_api(symbol):
    """주가 프록시"""
    price_data = get_stock_price(symbol.upper())
    if price_data is None:
        return jsonify({'error': '주가 조회 실패'}), 500
    return jsonify(price_data)


@app.route('/api/admin/stock', methods=['POST'])
def add_stock():
    """주식 종목 추가 (관리자 전용)"""
    data = request.get_json()
    user_id = data.get('user_id')
    user = db.session.get(User, user_id)
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    symbol = data.get('symbol', '').strip().upper()
    shares = data.get('shares', 0)

    if not symbol or shares <= 0:
        return jsonify({'error': '종목코드와 수량을 올바르게 입력해주세요'}), 400

    stock = StockHolding(symbol=symbol, shares=shares, added_by=user_id)
    db.session.add(stock)
    db.session.commit()

    return jsonify({'id': stock.id, 'symbol': stock.symbol, 'shares': stock.shares})


@app.route('/api/admin/stock/<int:stock_id>', methods=['PUT'])
def update_stock(stock_id):
    """주식 수량 수정 (관리자 전용)"""
    data = request.get_json()
    user_id = data.get('user_id')
    user = db.session.get(User, user_id)
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    stock = db.session.get(StockHolding, stock_id)
    if not stock:
        return jsonify({'error': '종목을 찾을 수 없습니다'}), 404

    shares = data.get('shares', 0)
    if shares <= 0:
        return jsonify({'error': '수량을 올바르게 입력해주세요'}), 400

    stock.shares = shares
    db.session.commit()

    return jsonify({'id': stock.id, 'symbol': stock.symbol, 'shares': stock.shares})


@app.route('/api/admin/stock/<int:stock_id>', methods=['DELETE'])
def delete_stock(stock_id):
    """주식 종목 삭제 (관리자 전용)"""
    data = request.get_json()
    user_id = data.get('user_id')
    user = db.session.get(User, user_id)
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    stock = db.session.get(StockHolding, stock_id)
    if not stock:
        return jsonify({'error': '종목을 찾을 수 없습니다'}), 404

    db.session.delete(stock)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/admin/cash', methods=['PUT'])
def update_cash():
    """현금 자산 수정 (관리자 전용)"""
    data = request.get_json()
    user_id = data.get('user_id')
    user = db.session.get(User, user_id)
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    amount = data.get('amount', 0)
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return jsonify({'error': '금액을 올바르게 입력해주세요'}), 400
    if amount < 0:
        return jsonify({'error': '금액을 올바르게 입력해주세요'}), 400

    cash = CashAsset.query.first()
    if cash:
        cash.amount = amount
        cash.updated_by = user_id
    else:
        cash = CashAsset(amount=amount, updated_by=user_id)
        db.session.add(cash)

    db.session.commit()

    return jsonify({'amount': cash.amount})


@app.route('/api/admin/finnhub-key', methods=['GET'])
def get_finnhub_key():
    """Finnhub API 키 상태 조회 (관리자 전용)"""
    user_id = request.args.get('user_id', type=int)
    user = db.session.get(User, user_id) if user_id else None
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    api_key = get_finnhub_api_key()
    if api_key:
        masked = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
        return jsonify({'has_key': True, 'masked_key': masked})
    return jsonify({'has_key': False, 'masked_key': ''})


@app.route('/api/admin/finnhub-key', methods=['PUT'])
def save_finnhub_key():
    """Finnhub API 키 저장 (관리자 전용)"""
    data = request.get_json()
    user_id = data.get('user_id')
    user = db.session.get(User, user_id) if user_id else None
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    api_key = data.get('api_key', '').strip()
    if not api_key:
        return jsonify({'error': 'API 키를 입력해주세요'}), 400

    config = SiteConfig.query.filter_by(key='FINNHUB_API_KEY').first()
    if config:
        config.value = api_key
        config.updated_by = user_id
    else:
        config = SiteConfig(key='FINNHUB_API_KEY', value=api_key, updated_by=user_id)
        db.session.add(config)

    db.session.commit()

    # 캐시 초기화
    _price_cache.clear()

    return jsonify({'success': True})


@app.route('/api/admin/finnhub-test', methods=['POST'])
def test_finnhub_key():
    """Finnhub API 키 연결 테스트 (관리자 전용)"""
    data = request.get_json()
    user_id = data.get('user_id')
    user = db.session.get(User, user_id) if user_id else None
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    api_key = data.get('api_key', '').strip()
    if not api_key:
        api_key = get_finnhub_api_key()
    if not api_key:
        return jsonify({'success': False, 'message': 'API 키가 없습니다'}), 400

    try:
        resp = http_requests.get(
            'https://finnhub.io/api/v1/quote',
            params={'symbol': 'AAPL', 'token': api_key},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('c', 0) > 0:
                return jsonify({'success': True, 'message': '연결 성공!'})
            else:
                return jsonify({'success': False, 'message': '잘못된 API 키입니다'})
        elif resp.status_code == 401:
            return jsonify({'success': False, 'message': '잘못된 API 키입니다'})
        else:
            return jsonify({'success': False, 'message': f'API 오류 (HTTP {resp.status_code})'})
    except Exception as e:
        return jsonify({'success': False, 'message': '연결 실패: 네트워크 오류'})


@app.route('/api/admin/save-all', methods=['POST'])
def save_all_settings():
    """관리자 설정 일괄 저장"""
    data = request.get_json()
    user_id = data.get('user_id')
    user = db.session.get(User, user_id) if user_id else None
    if not user or not is_admin(user.name):
        return jsonify({'error': '권한이 없습니다'}), 403

    saved = []

    # API 키 저장
    api_key = data.get('api_key', '').strip()
    if api_key:
        config = SiteConfig.query.filter_by(key='FINNHUB_API_KEY').first()
        if config:
            config.value = api_key
            config.updated_by = user_id
        else:
            config = SiteConfig(key='FINNHUB_API_KEY', value=api_key, updated_by=user_id)
            db.session.add(config)
        _price_cache.clear()
        saved.append('API 키')

    # 현금 저장
    cash_amount = data.get('cash_amount')
    if cash_amount is not None:
        try:
            cash_amount = int(cash_amount)
        except (ValueError, TypeError):
            cash_amount = 0
        if cash_amount >= 0:
            cash = CashAsset.query.first()
            if cash:
                cash.amount = cash_amount
                cash.updated_by = user_id
            else:
                cash = CashAsset(amount=cash_amount, updated_by=user_id)
                db.session.add(cash)
            saved.append('현금 자산')

    db.session.commit()

    if saved:
        return jsonify({'success': True, 'message': ', '.join(saved) + ' 저장 완료'})
    return jsonify({'success': True, 'message': '변경 사항 없음'})


# DB 테이블 생성
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
