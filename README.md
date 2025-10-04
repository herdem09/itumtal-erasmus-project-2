# Panel Veri Toplama ve Görselleştirme Sunucusu

Bu proje, güneş paneli verilerini toplayan, veritabanında saklayan ve web arayüzü ile görselleştiren bir Flask sunucusudur.

## Özellikler

### API Endpointleri
- **POST /api/panel_control**: Panel kontrol komutunu alır (sadece paneli_su_yap: true/false)
- **GET /api/status**: Mevcut durumu döndürür
- **POST /api/add_sample_data**: Test için örnek veri ekler
- **GET /api/daily_data/<date>**: Belirli bir günün saatlik verilerini döndürür
- **GET /api/yearly_data**: Yıl boyunca günlük ortalamaları döndürür
- **GET /api/weekly_data/<start_date>**: Belirli bir haftanın günlük verilerini döndürür
- **GET /api/monthly_data/<year>/<month>**: Belirli bir ayın günlük verilerini döndürür
- **GET /api/monthly_averages/<year>**: Belirli bir yılın aylık ortalamalarını döndürür

### Veri Yapısı
**Ana API Endpoint (/api/panel_control):**
- `paneli_su_yap` (bool): Panel kontrolü (true = aç, false = kapat)

**Test API Endpoint (/api/add_sample_data):**
- `watt` (float): Watt değeri
- `kotu_hava` (bool): Kötü hava durumu
- `panel_acik_mi` (bool): Panel açık mı durumu
- `yon` (int): Yön bilgisi
- `paneli_su_yap` (string): Panel kontrolü ("aç" veya "kapat")

### Veri Saklama
- Tüm veriler SQLite veritabanında saklanır
- `kotu_hava`, `panel_acik_mi`, `yon` ve `paneli_su_yap` değerleri ayrıca CSV dosyasında güncel olarak tutulur

### Web Arayüzü
5 farklı analiz sayfası:
1. **Günlük Analiz**: Belirli bir günün saatlik watt ortalamaları
2. **Yıllık Analiz**: Yıl boyunca günlük watt ortalamaları
3. **Haftalık Analiz**: Belirli bir haftanın günlük ortalamaları
4. **Aylık Analiz**: Belirli bir ayın günlük ortalamaları
5. **Aylık Ortalamalar**: Yıl boyunca aylık watt ortalamaları

Her sayfada mevcut durum bilgileri (kötü hava, panel açık mı, yön, panel şu yap) ve son watt değeri gösterilir.

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Sunucuyu başlatın:
```bash
python app.py
```

3. Tarayıcınızda `http://localhost:5000` adresine gidin.

## Kullanım

### Panel Kontrolü
Panel kontrol komutunu göndermek için:

```bash
curl -X POST http://localhost:5000/api/panel_control \
  -H "Content-Type: application/json" \
  -d '{
    "paneli_su_yap": true
  }'
```

### Test Verisi Ekleme
Grafikleri test etmek için örnek veri ekleyebilirsiniz:

```bash
curl -X POST http://localhost:5000/api/add_sample_data \
  -H "Content-Type: application/json" \
  -d '{
    "watt": 150.5,
    "kotu_hava": false,
    "panel_acik_mi": true,
    "yon": 180,
    "paneli_su_yap": "aç"
  }'
```

### Analiz Sayfaları
- **Günlük**: Tarih seçerek o günün saatlik analizini görün
- **Yıllık**: Tüm yılın günlük ortalamalarını görün
- **Haftalık**: Hafta başlangıç tarihi seçerek o haftanın analizini görün
- **Aylık**: Yıl ve ay seçerek o ayın günlük analizini görün
- **Aylık Ortalamalar**: Yıl seçerek o yılın aylık ortalamalarını görün

## Teknolojiler

- **Backend**: Python Flask
- **Veritabanı**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap, Chart.js
- **Veri İşleme**: Pandas
- **Grafik**: Chart.js

## Dosya Yapısı

```
├── app.py                 # Ana Flask uygulaması
├── requirements.txt       # Python paket gereksinimleri
├── README.md             # Bu dosya
├── templates/            # HTML şablonları
│   ├── base.html         # Temel şablon
│   ├── index.html        # Ana sayfa
│   ├── daily.html        # Günlük analiz
│   ├── yearly.html       # Yıllık analiz
│   ├── weekly.html       # Haftalık analiz
│   ├── monthly.html      # Aylık analiz
│   └── monthly_averages.html # Aylık ortalamalar
├── panel_data.db         # SQLite veritabanı (otomatik oluşur)
└── panel_status.csv      # Güncel durum CSV dosyası (otomatik oluşur)
```

## API Dokümantasyonu

### POST /api/panel_control
Panel kontrol komutunu alır.

**Request Body:**
```json
{
  "paneli_su_yap": true
}
```

**Response:**
```json
{
  "message": "Panel kontrol komutu alındı",
  "paneli_su_yap": true
}
```

### POST /api/add_sample_data
Test için örnek veri ekler.

**Request Body:**
```json
{
  "watt": 150.5,
  "kotu_hava": false,
  "panel_acik_mi": true,
  "yon": 180,
  "paneli_su_yap": "aç"
}
```

**Response:**
```json
{
  "message": "Örnek veri eklendi",
  "id": 1
}
```

### GET /api/status
Mevcut durumu döndürür.

**Response:**
```json
{
  "csv_status": {
    "kotu_hava": false,
    "panel_acik_mi": true,
    "yon": 180,
    "paneli_su_yap": "aç",
    "timestamp": "2024-01-15T14:30:00"
  },
  "latest_data": {
    "id": 1,
    "zaman": "14:30",
    "tarih": "2024-01-15",
    "watt": 150.5,
    "kotu_hava": false,
    "panel_acik_mi": true,
    "yon": 180,
    "paneli_su_yap": "aç",
    "timestamp": "2024-01-15T14:30:00"
  }
}
```