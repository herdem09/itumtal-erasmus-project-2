# Enerji İzleme ve Kontrol Sistemi

Bu proje, güneş paneli enerji üretimini izlemek ve kontrol etmek için geliştirilmiş bir web uygulamasıdır.

## Özellikler

### API Endpoints
- **POST /api/data** - Sensör verilerini kaydetme
- **GET /api/daily-hourly** - Günlük saatlik ortalamalar
- **GET /api/current-hour** - O saat içindeki anlık veriler
- **GET /api/weekly-hourly** - Haftalık saatlik ortalamalar
- **GET /api/monthly-daily** - Aylık günlük ortalamalar
- **GET /api/yearly-monthly** - Yıllık aylık ortalamalar
- **GET /api/panel-status** - Panel durumu bilgisi
- **POST /api/panel-control** - Panel kontrolü (aç/kapat)

### Web Arayüzü
- 5 farklı grafik görünümü
- Gerçek zamanlı panel durumu
- Panel kontrol butonları
- Test verisi gönderme özelliği
- Responsive tasarım

## Kurulum

### Gereksinimler
- Python 3.7+
- PostgreSQL 12+
- pip

### Adımlar

1. **Projeyi klonlayın:**
```bash
git clone <repository-url>
cd enerji-monitor
```

2. **Sanal ortam oluşturun:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **PostgreSQL veritabanı oluşturun:**
```sql
CREATE DATABASE enerji_monitor;
```

5. **Çevre değişkenlerini ayarlayın:**
```bash
cp .env.example .env
# .env dosyasını düzenleyerek veritabanı bilgilerinizi girin
```

6. **Uygulamayı çalıştırın:**
```bash
python app.py
```

Uygulama http://localhost:5000 adresinde çalışacaktır.

## Veritabanı Şeması

### sensor_data
- `id` - Birincil anahtar
- `zaman` - Zaman (TIME)
- `tarih` - Tarih (DATE)
- `watt` - Watt değeri (REAL)
- `kotuhava` - Kötü hava durumu (BOOLEAN)
- `panel_acik_mi` - Panel açık mı (BOOLEAN)
- `paneli_su_yap` - Panel kontrolü (VARCHAR)
- `created_at` - Oluşturulma zamanı (TIMESTAMP)

### hourly_averages
- `id` - Birincil anahtar
- `tarih` - Tarih (DATE)
- `saat` - Saat (INTEGER)
- `ortalama_watt` - Ortalama watt (REAL)
- `created_at` - Oluşturulma zamanı (TIMESTAMP)

### panel_status
- `id` - Birincil anahtar
- `panel_acik_mi` - Panel açık mı (BOOLEAN)
- `kotuhava` - Kötü hava durumu (BOOLEAN)
- `updated_at` - Güncelleme zamanı (TIMESTAMP)

## API Kullanımı

### Veri Gönderme
```bash
curl -X POST http://localhost:5000/api/data \
  -H "Content-Type: application/json" \
  -d '{
    "zaman": "14:30:00",
    "tarih": "2024-01-15",
    "watt": 750.5,
    "kotuhava": false,
    "panel_acik_mi": true,
    "paneli_su_yap": "aç"
  }'
```

### Panel Kontrolü
```bash
curl -X POST http://localhost:5000/api/panel-control \
  -H "Content-Type: application/json" \
  -d '{"action": "ac"}'
```

## Otomatik İşlemler

- Her saat başı otomatik olarak o saatin watt ortalaması hesaplanır ve kaydedilir
- Panel durumu her 30 saniyede bir güncellenir

## Teknolojiler

- **Backend:** Python Flask
- **Veritabanı:** PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Grafik:** Chart.js
- **UI Framework:** Bootstrap 5
- **İkonlar:** Font Awesome
- **Zamanlama:** APScheduler

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.