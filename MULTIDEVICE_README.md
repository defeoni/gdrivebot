# GDrive Bot - Multi-Device Access Setup

Saya telah menyiapkan bot Anda untuk dapat diakses dari perangkat lain. Berikut file-file yang telah dibuat:

## 📁 File yang Telah Ditambahkan

### 1. **`.env.example`** - Template Konfigurasi
Salin ke `.env` dan sesuaikan API keys Anda:
```bash
cp .env.example .env
```

### 2. **`config.py`** - Manajemen Konfigurasi Terpusat
Mengelola konfigurasi dari environment variables dengan fallback

### 3. **`requirements.txt`** - Dependency Management
Untuk install semua package sekaligus:
```bash
pip install -r requirements.txt
```

### 4. **`Dockerfile` & `docker-compose.yml`** - Container Support
Deploy bot di Docker untuk portability maksimal

### 5. **`.gitignore`** - Git Security
Melindungi credentials agar tidak ter-upload ke repository

### 6. **`SETUP_MULTIDEVICE.md`** - Dokumentasi Lengkap
Panduan detail untuk multi-device setup

---

## 🚀 Langkah Cepat (Local Network)

### Di Komputer Utama:

1. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env dengan API keys Anda
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan bot:**
   ```bash
   python gdrivebot.py
   ```

### Di Perangkat Lain (Sama Network):

Bot dapat langsung diakses melalui Telegram dari device lain karena bot sudah terhubung dengan Telegram servers.

---

## ☁️ Cloud Deployment (Recommended untuk Akses Dimana Saja)

### Option 1: Railway.app (5 credits gratis)
```bash
npm install -g railway
railway link
railway up
```

### Option 2: Render.com (Free tier)
- Push ke GitHub
- Connect ke Render
- Deploy otomatis

### Option 3: VPS (DigitalOcean 5$/bulan)
```bash
ssh root@your_server_ip
git clone your-repo
cd gdrivebot
pip install -r requirements.txt
python gdrivebot.py 2>&1 | tee bot.log &
```

---

## 🐳 Docker Deployment

### Build & Run Lokal:
```bash
docker build -t gdrivebot .
docker run -e BOT_TOKEN="your_token" -e CLAUDE_API="your_api" gdrivebot
```

### Dengan Docker Compose:
```bash
# Edit docker-compose.yml dengan .env values
docker-compose up -d
```

---

## 🔐 Security Tips

1. **JANGAN share `.env` file**
   - Gunakan `.env.example` sebagai template
   - Add `.env` ke `.gitignore` (sudah ada)

2. **Untuk Team Collaboration:**
   ```bash
   # Encrypt .env
   gpg -c .env
   # Share .env.gpg ke team
   ```

3. **Setup GitHub Secrets (untuk CI/CD)**
   ```
   Settings → Secrets → Add BOT_TOKEN, CLAUDE_API, dll
   ```

---

## 📊 Monitor Bot Status

```bash
# Check if bot is running
ps aux | grep gdrivebot

# View live logs
tail -f bot.log

# Restart bot
pkill -f gdrivebot
python gdrivebot.py &
```

---

## 🆘 Troubleshooting

**Bot tidak bisa connect:**
- Cek internet connection
- Verify BOT_TOKEN di Telegram (cek format)
- Restart bot: `python gdrivebot.py`

**Config tidak ter-load:**
- Pastikan `config.py` di folder yang sama
- Check `.env` file exists
- Jalankan `python setup.py` untuk validate

**Akses dari device lain gagal:**
- Jika lokal network: pastikan devices di network yang sama
- Jika cloud: periksa firewall settings
- Test dengan: `ping your_server_ip`

---

## 💡 Next Steps

1. [ ] Setup `.env` dengan credentials
2. [ ] Test bot di lokal: `python gdrivebot.py`
3. [ ] Pilih deployment method (cloud/local/docker)
4. [ ] Setup monitoring & logging
5. [ ] Configure auto-restart (systemd/PM2/Docker)

---

**Questions?** Lihat `SETUP_MULTIDEVICE.md` untuk dokumentasi lengkap.
