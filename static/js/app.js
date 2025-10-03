class EnergyMonitor {
    constructor() {
        this.chart = null;
        this.currentChartType = 'daily-hourly';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPanelStatus();
        this.loadChartData();
        
        // Her 30 saniyede bir panel durumunu güncelle
        setInterval(() => {
            this.loadPanelStatus();
        }, 30000);
    }

    setupEventListeners() {
        // Grafik seçenekleri
        document.querySelectorAll('[data-chart]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchChart(e.target.dataset.chart);
            });
        });

        // Panel kontrol butonları
        document.getElementById('panelOnBtn').addEventListener('click', () => {
            this.controlPanel('ac');
        });

        document.getElementById('panelOffBtn').addEventListener('click', () => {
            this.controlPanel('kapat');
        });

        // Test verisi gönderme
        document.getElementById('sendTestData').addEventListener('click', () => {
            this.sendTestData();
        });
    }

    switchChart(chartType) {
        // Aktif butonu güncelle
        document.querySelectorAll('[data-chart]').forEach(btn => {
            btn.classList.remove('active', 'btn-primary');
            btn.classList.add('btn-outline-primary');
        });
        
        const activeBtn = document.querySelector(`[data-chart="${chartType}"]`);
        activeBtn.classList.add('active', 'btn-primary');
        activeBtn.classList.remove('btn-outline-primary');

        this.currentChartType = chartType;
        this.loadChartData();
    }

    async loadChartData() {
        this.showLoading(true);
        
        try {
            const response = await fetch(`/api/${this.currentChartType}`);
            const data = await response.json();
            
            if (response.ok) {
                this.updateChart(data);
            } else {
                this.showToast('Veri yüklenirken hata oluştu: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Bağlantı hatası: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    updateChart(data) {
        const ctx = document.getElementById('energyChart').getContext('2d');
        
        // Mevcut grafiği yok et
        if (this.chart) {
            this.chart.destroy();
        }

        let labels, datasets, title;

        switch (this.currentChartType) {
            case 'daily-hourly':
                labels = data.map(item => `${item.saat}:00`);
                datasets = [{
                    label: 'Saatlik Ortalama Watt',
                    data: data.map(item => item.ortalama_watt),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }];
                title = 'Günlük Saatlik Watt Ortalamaları';
                break;

            case 'current-hour':
                labels = data.map(item => item.zaman);
                datasets = [{
                    label: 'Anlık Watt Değerleri',
                    data: data.map(item => item.watt),
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                }];
                title = 'O Saat İçindeki Anlık Veriler';
                break;

            case 'weekly-hourly':
                labels = data.map(item => `${item.tarih} ${item.saat}:00`);
                datasets = [{
                    label: 'Haftalık Saatlik Ortalama Watt',
                    data: data.map(item => item.ortalama_watt),
                    borderColor: '#fd7e14',
                    backgroundColor: 'rgba(253, 126, 20, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }];
                title = 'Haftalık Saatlik Watt Ortalamaları';
                break;

            case 'monthly-daily':
                labels = data.map(item => item.tarih);
                datasets = [{
                    label: 'Aylık Günlük Ortalama Watt',
                    data: data.map(item => item.ortalama_watt),
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }];
                title = 'Aylık Günlük Watt Ortalamaları';
                break;

            case 'yearly-monthly':
                const monthNames = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                                  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
                labels = data.map(item => monthNames[item.ay - 1]);
                datasets = [{
                    label: 'Yıllık Aylık Ortalama Watt',
                    data: data.map(item => item.ortalama_watt),
                    borderColor: '#6f42c1',
                    backgroundColor: 'rgba(111, 66, 193, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }];
                title = 'Yıllık Aylık Watt Ortalamaları';
                break;
        }

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: title,
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        color: '#333'
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Watt',
                            font: {
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: this.getXAxisLabel(),
                            font: {
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                elements: {
                    point: {
                        radius: 4,
                        hoverRadius: 8
                    }
                }
            }
        });
    }

    getXAxisLabel() {
        switch (this.currentChartType) {
            case 'daily-hourly':
                return 'Saat';
            case 'current-hour':
                return 'Zaman';
            case 'weekly-hourly':
                return 'Tarih ve Saat';
            case 'monthly-daily':
                return 'Tarih';
            case 'yearly-monthly':
                return 'Ay';
            default:
                return 'Zaman';
        }
    }

    async loadPanelStatus() {
        try {
            const response = await fetch('/api/panel-status');
            const data = await response.json();
            
            if (response.ok) {
                this.updatePanelStatus(data);
            }
        } catch (error) {
            console.error('Panel durumu yüklenirken hata:', error);
        }
    }

    updatePanelStatus(data) {
        // Panel durumu
        const panelStatus = document.getElementById('panelStatus');
        if (data.panel_acik_mi) {
            panelStatus.textContent = 'Açık';
            panelStatus.className = 'badge bg-success';
        } else {
            panelStatus.textContent = 'Kapalı';
            panelStatus.className = 'badge bg-danger';
        }

        // Hava durumu
        const weatherStatus = document.getElementById('weatherStatus');
        if (data.kotuhava) {
            weatherStatus.textContent = 'Kötü';
            weatherStatus.className = 'badge bg-warning';
        } else {
            weatherStatus.textContent = 'İyi';
            weatherStatus.className = 'badge bg-info';
        }

        // Son güncelleme
        const lastUpdate = document.getElementById('lastUpdate');
        if (data.updated_at) {
            const date = new Date(data.updated_at);
            lastUpdate.textContent = date.toLocaleString('tr-TR');
        }
    }

    async controlPanel(action) {
        try {
            const response = await fetch('/api/panel-control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: action })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.showToast(data.message, 'success');
                this.loadPanelStatus();
            } else {
                this.showToast('Panel kontrolünde hata: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Bağlantı hatası: ' + error.message, 'error');
        }
    }

    async sendTestData() {
        const now = new Date();
        const testData = {
            zaman: now.toTimeString().split(' ')[0], // HH:MM:SS formatında
            tarih: now.toISOString().split('T')[0], // YYYY-MM-DD formatında
            watt: Math.floor(Math.random() * 1000) + 100, // 100-1100 arası rastgele
            kotuhava: Math.random() > 0.8, // %20 ihtimalle kötü hava
            panel_acik_mi: Math.random() > 0.3, // %70 ihtimalle açık
            paneli_su_yap: Math.random() > 0.5 ? 'aç' : 'kapat'
        };

        try {
            const response = await fetch('/api/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(testData)
            });

            const data = await response.json();
            
            if (response.ok) {
                this.showToast('Test verisi başarıyla gönderildi', 'success');
                this.loadPanelStatus();
                // Grafik verilerini yenile
                setTimeout(() => {
                    this.loadChartData();
                }, 1000);
            } else {
                this.showToast('Test verisi gönderilirken hata: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Bağlantı hatası: ' + error.message, 'error');
        }
    }

    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const chartContainer = document.querySelector('.chart-container');
        
        if (show) {
            loadingIndicator.style.display = 'block';
            chartContainer.style.opacity = '0.5';
        } else {
            loadingIndicator.style.display = 'none';
            chartContainer.style.opacity = '1';
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastBody = document.getElementById('toastBody');
        
        // Toast rengini ayarla
        const toastHeader = toast.querySelector('.toast-header');
        const icon = toastHeader.querySelector('i');
        
        toastHeader.className = 'toast-header';
        icon.className = 'fas me-2';
        
        switch (type) {
            case 'success':
                toastHeader.classList.add('bg-success', 'text-white');
                icon.classList.add('fa-check-circle', 'text-white');
                break;
            case 'error':
                toastHeader.classList.add('bg-danger', 'text-white');
                icon.classList.add('fa-exclamation-circle', 'text-white');
                break;
            case 'warning':
                toastHeader.classList.add('bg-warning', 'text-dark');
                icon.classList.add('fa-exclamation-triangle', 'text-dark');
                break;
            default:
                toastHeader.classList.add('bg-primary', 'text-white');
                icon.classList.add('fa-info-circle', 'text-white');
        }
        
        toastBody.textContent = message;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Sayfa yüklendiğinde uygulamayı başlat
document.addEventListener('DOMContentLoaded', () => {
    new EnergyMonitor();
});