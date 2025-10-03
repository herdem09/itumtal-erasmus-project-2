from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

load_dotenv()

app = Flask(__name__)

# Veritabanı bağlantısı
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'enerji_monitor'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password'),
        port=os.getenv('DB_PORT', '5432')
    )
    return conn

# Veritabanı tablolarını oluştur
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ana veri tablosu
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            zaman TIME NOT NULL,
            tarih DATE NOT NULL,
            watt REAL NOT NULL,
            kotuhava BOOLEAN NOT NULL,
            panel_acik_mi BOOLEAN NOT NULL,
            paneli_su_yap VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Saatlik ortalama tablosu
    cur.execute('''
        CREATE TABLE IF NOT EXISTS hourly_averages (
            id SERIAL PRIMARY KEY,
            tarih DATE NOT NULL,
            saat INTEGER NOT NULL,
            ortalama_watt REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tarih, saat)
        )
    ''')
    
    # Panel durumu tablosu
    cur.execute('''
        CREATE TABLE IF NOT EXISTS panel_status (
            id SERIAL PRIMARY KEY,
            panel_acik_mi BOOLEAN NOT NULL,
            kotuhava BOOLEAN NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

# Saatlik ortalama hesaplama
def calculate_hourly_average():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Son saatin verilerini al
    now = datetime.now()
    current_hour = now.hour
    current_date = now.date()
    
    cur.execute('''
        SELECT AVG(watt) as avg_watt
        FROM sensor_data 
        WHERE tarih = %s AND EXTRACT(hour FROM zaman) = %s
    ''', (current_date, current_hour))
    
    result = cur.fetchone()
    if result and result[0] is not None:
        avg_watt = result[0]
        
        # Saatlik ortalamayı kaydet
        cur.execute('''
            INSERT INTO hourly_averages (tarih, saat, ortalama_watt)
            VALUES (%s, %s, %s)
            ON CONFLICT (tarih, saat) 
            DO UPDATE SET ortalama_watt = %s
        ''', (current_date, current_hour, avg_watt, avg_watt))
        
        conn.commit()
    
    cur.close()
    conn.close()

# Scheduler'ı başlat
scheduler = BackgroundScheduler()
scheduler.add_job(func=calculate_hourly_average, trigger="cron", hour="*", minute=0)
scheduler.start()

# Uygulama kapatılırken scheduler'ı durdur
atexit.register(lambda: scheduler.shutdown())

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint - veri kaydetme
@app.route('/api/data', methods=['POST'])
def save_data():
    try:
        data = request.get_json()
        
        # Gerekli alanları kontrol et
        required_fields = ['zaman', 'tarih', 'watt', 'kotuhava', 'panel_acik_mi', 'paneli_su_yap']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} alanı gerekli'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Veriyi kaydet
        cur.execute('''
            INSERT INTO sensor_data (zaman, tarih, watt, kotuhava, panel_acik_mi, paneli_su_yap)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            data['zaman'],
            data['tarih'],
            data['watt'],
            data['kotuhava'],
            data['panel_acik_mi'],
            data['paneli_su_yap']
        ))
        
        # Panel durumunu güncelle
        cur.execute('''
            INSERT INTO panel_status (panel_acik_mi, kotuhava)
            VALUES (%s, %s)
        ''', (data['panel_acik_mi'], data['kotuhava']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Veri başarıyla kaydedildi'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint - günlük saatlik ortalamalar
@app.route('/api/daily-hourly')
def get_daily_hourly():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT saat, ortalama_watt
            FROM hourly_averages 
            WHERE tarih = CURRENT_DATE
            ORDER BY saat
        ''')
        
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in data])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint - anlık veriler (o saat)
@app.route('/api/current-hour')
def get_current_hour():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        now = datetime.now()
        current_hour = now.hour
        
        cur.execute('''
            SELECT zaman, watt, kotuhava, panel_acik_mi
            FROM sensor_data 
            WHERE tarih = CURRENT_DATE AND EXTRACT(hour FROM zaman) = %s
            ORDER BY zaman
        ''', (current_hour,))
        
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in data])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint - haftalık saatlik ortalamalar
@app.route('/api/weekly-hourly')
def get_weekly_hourly():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT tarih, saat, AVG(ortalama_watt) as ortalama_watt
            FROM hourly_averages 
            WHERE tarih >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY tarih, saat
            ORDER BY tarih, saat
        ''')
        
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in data])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint - aylık günlük ortalamalar
@app.route('/api/monthly-daily')
def get_monthly_daily():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT tarih, AVG(ortalama_watt) as ortalama_watt
            FROM hourly_averages 
            WHERE EXTRACT(year FROM tarih) = EXTRACT(year FROM CURRENT_DATE)
            AND EXTRACT(month FROM tarih) = EXTRACT(month FROM CURRENT_DATE)
            GROUP BY tarih
            ORDER BY tarih
        ''')
        
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in data])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint - yıllık aylık ortalamalar
@app.route('/api/yearly-monthly')
def get_yearly_monthly():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT EXTRACT(month FROM tarih) as ay, AVG(ortalama_watt) as ortalama_watt
            FROM hourly_averages 
            WHERE EXTRACT(year FROM tarih) = EXTRACT(year FROM CURRENT_DATE)
            GROUP BY EXTRACT(month FROM tarih)
            ORDER BY ay
        ''')
        
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in data])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint - panel durumu
@app.route('/api/panel-status')
def get_panel_status():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT panel_acik_mi, kotuhava, updated_at
            FROM panel_status 
            ORDER BY updated_at DESC 
            LIMIT 1
        ''')
        
        data = cur.fetchone()
        cur.close()
        conn.close()
        
        if data:
            return jsonify(dict(data))
        else:
            return jsonify({'panel_acik_mi': False, 'kotuhava': False})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint - panel kontrolü
@app.route('/api/panel-control', methods=['POST'])
def control_panel():
    try:
        data = request.get_json()
        action = data.get('action')  # 'ac' veya 'kapat'
        
        if action not in ['ac', 'kapat']:
            return jsonify({'error': 'Geçersiz aksiyon'}), 400
        
        panel_acik_mi = action == 'ac'
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Panel durumunu güncelle
        cur.execute('''
            INSERT INTO panel_status (panel_acik_mi, kotuhava)
            VALUES (%s, %s)
        ''', (panel_acik_mi, False))  # kotuhava varsayılan olarak False
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': f'Panel {action}ıldı', 'panel_acik_mi': panel_acik_mi})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)