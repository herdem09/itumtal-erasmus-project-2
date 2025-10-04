from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///panel_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Veritabanı modeli
class PanelData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zaman = db.Column(db.String(10), nullable=False)
    tarih = db.Column(db.String(10), nullable=False)
    watt = db.Column(db.Float, nullable=False)
    kotu_hava = db.Column(db.Boolean, nullable=False)
    panel_acik_mi = db.Column(db.Boolean, nullable=False)
    yon = db.Column(db.Integer, nullable=False)
    paneli_su_yap = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'zaman': self.zaman,
            'tarih': self.tarih,
            'watt': self.watt,
            'kotu_hava': self.kotu_hava,
            'panel_acik_mi': self.panel_acik_mi,
            'yon': self.yon,
            'paneli_su_yap': self.paneli_su_yap,
            'timestamp': self.timestamp.isoformat()
        }

# CSV dosyası işlemleri
CSV_FILE = 'panel_status.csv'

def update_csv(kotu_hava, panel_acik_mi, yon, paneli_su_yap):
    """CSV dosyasını günceller - sadece en son durumu tutar"""
    data = {
        'kotu_hava': kotu_hava,
        'panel_acik_mi': panel_acik_mi,
        'yon': yon,
        'paneli_su_yap': paneli_su_yap,
        'timestamp': datetime.now().isoformat()
    }
    df = pd.DataFrame([data])
    df.to_csv(CSV_FILE, index=False)

def get_csv_data():
    """CSV dosyasından veri okur"""
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        return df.iloc[-1].to_dict() if not df.empty else {}
    return {}

# API endpointleri
@app.route('/api/panel_control', methods=['POST'])
def panel_control():
    """Panel kontrol komutunu alır (sadece paneli_su_yap)"""
    try:
        data = request.get_json()
        
        # Veri doğrulama
        if 'paneli_su_yap' not in data:
            return jsonify({'error': 'Eksik alan: paneli_su_yap'}), 400
        
        # Veri tipini kontrol et
        paneli_su_yap = bool(data['paneli_su_yap'])
        
        # Mevcut CSV verilerini oku
        csv_data = get_csv_data()
        
        # CSV dosyasını güncelle (diğer değerler aynı kalır)
        kotu_hava = csv_data.get('kotu_hava', False)
        panel_acik_mi = csv_data.get('panel_acik_mi', False)
        yon = csv_data.get('yon', 0)
        
        update_csv(kotu_hava, panel_acik_mi, yon, paneli_su_yap)
        
        return jsonify({'message': 'Panel kontrol komutu alındı', 'paneli_su_yap': paneli_su_yap}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Mevcut durumu döndürür"""
    csv_data = get_csv_data()
    latest_data = PanelData.query.order_by(PanelData.timestamp.desc()).first()
    
    return jsonify({
        'csv_status': csv_data,
        'latest_data': latest_data.to_dict() if latest_data else None
    })

# Web arayüzü route'ları
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/daily')
def daily():
    return render_template('daily.html')

@app.route('/yearly')
def yearly():
    return render_template('yearly.html')

@app.route('/weekly')
def weekly():
    return render_template('weekly.html')

@app.route('/monthly')
def monthly():
    return render_template('monthly.html')

@app.route('/monthly_averages')
def monthly_averages():
    return render_template('monthly_averages.html')

# API endpointleri - grafik verileri için
@app.route('/api/daily_data/<date>')
def get_daily_data(date):
    """Belirli bir günün saatlik verilerini döndürür"""
    try:
        data = PanelData.query.filter_by(tarih=date).all()
        hourly_data = {}
        
        for record in data:
            hour = record.zaman.split(':')[0]  # Saat kısmını al
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(record.watt)
        
        # Saatlik ortalamaları hesapla
        hourly_averages = {}
        for hour in range(24):
            hour_str = f"{hour:02d}"
            if hour_str in hourly_data:
                hourly_averages[hour_str] = sum(hourly_data[hour_str]) / len(hourly_data[hour_str])
            else:
                hourly_averages[hour_str] = 0
        
        return jsonify(hourly_averages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/yearly_data')
def get_yearly_data():
    """Yıl boyunca günlük ortalamaları döndürür"""
    try:
        data = PanelData.query.all()
        daily_data = {}
        
        for record in data:
            date = record.tarih
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(record.watt)
        
        # Günlük ortalamaları hesapla
        daily_averages = {}
        for date, watts in daily_data.items():
            daily_averages[date] = sum(watts) / len(watts)
        
        return jsonify(daily_averages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weekly_data/<start_date>')
def get_weekly_data(start_date):
    """Belirli bir haftanın günlük verilerini döndürür"""
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        weekly_data = {}
        
        for i in range(7):
            current_date = start_dt + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            data = PanelData.query.filter_by(tarih=date_str).all()
            if data:
                watts = [record.watt for record in data]
                weekly_data[date_str] = sum(watts) / len(watts)
            else:
                weekly_data[date_str] = 0
        
        return jsonify(weekly_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly_data/<year>/<month>')
def get_monthly_data(year, month):
    """Belirli bir ayın günlük verilerini döndürür"""
    try:
        data = PanelData.query.filter(
            PanelData.tarih.like(f'{year}-{month:02d}-%')
        ).all()
        
        daily_data = {}
        for record in data:
            date = record.tarih
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(record.watt)
        
        # Günlük ortalamaları hesapla
        daily_averages = {}
        for date, watts in daily_data.items():
            daily_averages[date] = sum(watts) / len(watts)
        
        return jsonify(daily_averages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly_averages/<year>')
def get_monthly_averages(year):
    """Belirli bir yılın aylık ortalamalarını döndürür"""
    try:
        data = PanelData.query.filter(
            PanelData.tarih.like(f'{year}-%')
        ).all()
        
        monthly_data = {}
        for record in data:
            month = record.tarih[:7]  # YYYY-MM formatında
            if month not in monthly_data:
                monthly_data[month] = []
            monthly_data[month].append(record.watt)
        
        # Aylık ortalamaları hesapla
        monthly_averages = {}
        for month, watts in monthly_data.items():
            monthly_averages[month] = sum(watts) / len(watts)
        
        return jsonify(monthly_averages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_sample_data', methods=['POST'])
def add_sample_data():
    """Test için örnek veri ekler"""
    try:
        data = request.get_json()
        
        # Varsayılan değerler
        zaman = data.get('zaman', datetime.now().strftime('%H:%M'))
        tarih = data.get('tarih', datetime.now().strftime('%Y-%m-%d'))
        watt = data.get('watt', 100.0)
        kotu_hava = data.get('kotu_hava', False)
        panel_acik_mi = data.get('panel_acik_mi', True)
        yon = data.get('yon', 180)
        paneli_su_yap = data.get('paneli_su_yap', 'aç')
        
        # Veritabanına kaydet
        panel_data = PanelData(
            zaman=zaman,
            tarih=tarih,
            watt=watt,
            kotu_hava=kotu_hava,
            panel_acik_mi=panel_acik_mi,
            yon=yon,
            paneli_su_yap=paneli_su_yap
        )
        
        db.session.add(panel_data)
        db.session.commit()
        
        # CSV dosyasını güncelle
        update_csv(kotu_hava, panel_acik_mi, yon, paneli_su_yap)
        
        return jsonify({'message': 'Örnek veri eklendi', 'id': panel_data.id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)