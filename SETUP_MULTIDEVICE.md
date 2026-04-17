# GDrive Bot - Setup Guide untuk Multi-Device Access

## 📱 Akses dari Perangkat Lain

### Langkah 1: Persiapan di Komputer Utama

1. **Copy `.env.example` ke `.env`:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` dan sesuaikan konfigurasi:**
   ```
   BOT_TOKEN=your_bot_token
   CLAUDE_API=your_claude_api_key
   GOOGLE_CREDENTIALS_FILE=credentials.json
   GOOGLE_TOKEN_FILE=token.pickle
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Jalankan setup validation:**
   ```bash
   python setup.py
   ```

### Langkah 2: Opsi Deployment

#### Option A: Local Network Access (LAN)
1. Catat IP Address komputer Anda: `ipconfig` (Windows) atau `ifconfig` (Linux/Mac)
2. Jalankan bot
3. Akses dari perangkat lain di network yang sama

#### Option B: Cloud Deployment (Recommended)
Pilih salah satu platform:

**Heroku** (Free tier deprecated, gunakan alternatif)
```bash
heroku login
heroku create your-bot-name
git push heroku main
```

**Railway.app** (5 credits gratis)
```bash
railway link
railway up
```

**Replit** (Free tier terbatas)
- Upload project ke Replit
- Jalankan di terminal

**VPS (DigitalOcean, Linode, AWS)**
```bash
# SSH ke server
ssh root@your_server_ip

# Setup bot
git clone your-repo
cd gdrivebot
pip install -r requirements.txt
python gdrivebot.py
```

#### Option C: Docker (Portable)
```bash
# Build image
docker build -t gdrivebot .

# Run container
docker run -e BOT_TOKEN=your_token -e CLAUDE_API=your_api gdrivebot
```

### Langkah 3: Sharing Credentials Safely

**JANGAN share credentials melalui git atau public!**

1. **Gunakan `.env` file (ignored by git)**
2. **Untuk team collaboration:**
   ```bash
   # Encrypt .env
   gpg -c .env
   
   # Share saja .env.gpg
   ```

3. **Atau gunakan secret manager:**
   - GitHub Secrets (untuk CI/CD)
   - LastPass, 1Password, Bitwarden
   - Environment variables di platform hosting

### Langkah 4: Akses dari Perangkat Lain

**Via Telegram (Recommended)**
- Bot sudah di-host, cukup add bot di Telegram dari device lain
- Tidak perlu setup apapun

**Via SSH (untuk development)**
```bash
ssh user@server_ip
cd gdrivebot
python gdrivebot.py
```

**Via Remote IDE**
- VSCode Remote SSH
- PyCharm Professional
- Cursor dengan remote support

## 🔐 Security Best Practices

1. **Environment Variables:**
   - Simpan API keys di `.env` (jangan di git)
   - Gunakan `.gitignore` untuk `.env`

2. **Token Rotation:**
   - Rotate API keys secara berkala
   - Monitor bot activity logs

3. **Rate Limiting:**
   - Implementasi throttling untuk API calls
   - Gunakan caching untuk hasil yang sama

4. **Logging & Monitoring:**
   - Log semua activities
   - Setup alerts untuk error

## 📊 Monitoring Bot Health

```bash
# Check if bot is running
ps aux | grep gdrivebot

# View logs
tail -f bot.log

# Monitor resources
top -p $(pgrep -f gdrivebot)
```

## 🐛 Troubleshooting

**Bot tidak connect:**
- Check internet connection
- Verify BOT_TOKEN valid
- Check telegram API status

**Permission denied Google Drive:**
- Refresh token: `rm token.pickle` & restart
- Check credentials.json permissions
- Verify scopes

**Claude API error:**
- Check CLAUDE_API key valid
- Check rate limits
- Verify network access

## 📝 Development Workflow

1. **Setup di lokal:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Test sebelum deploy:**
   ```bash
   python -m pytest tests/
   ```

3. **Deploy:**
   ```bash
   git add .
   git commit -m "feat: description"
   git push origin main
   ```

## 💡 Tips

- Gunakan **webhooks** untuk event handling yang lebih efisien
- Setup **systemd service** untuk auto-restart di Linux
- Gunakan **PM2** untuk process management
- Implement **graceful shutdown** untuk clean exit

---

Untuk pertanyaan lebih lanjut, cek dokumentasi:
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- [Google Drive API](https://developers.google.com/drive/api)
- [Anthropic Claude](https://docs.anthropic.com/)
