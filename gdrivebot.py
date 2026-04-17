import os
import pickle
import io
import json
import urllib.request
import urllib.parse
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import PyPDF2

# Load configuration
try:
    from config import (
        BOT_TOKEN, CLAUDE_API, SCOPES, FINANCE_FILE,
        GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE, LOG_LEVEL, LOG_FILE
    )
except ImportError:
    # Fallback ke environment variables
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8338375836:AAFZzH66ZsThZP-z7dwlgF1t_xlYQAQpJPQ')
    CLAUDE_API = os.getenv('CLAUDE_API', '')
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    FINANCE_FILE = 'finance_data.json'
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.pickle')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("📱 GDrive Bot Starting...")


def load_finance_data():
    if os.path.exists(FINANCE_FILE):
        try:
            with open(FINANCE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_finance_data(data):
    with open(FINANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_finance_entry(user_id, entry_type, amount, note):
    data = load_finance_data()
    entry = {
        'user_id': str(user_id),
        'type': entry_type,
        'amount': float(amount),
        'note': note,
        'date': __import__('datetime').datetime.utcnow().isoformat()
    }
    data.append(entry)
    save_finance_data(data)
    return entry


def finance_summary(user_id, period='daily'):
    from datetime import datetime, timedelta
    data = load_finance_data()
    now = datetime.utcnow()
    if period == 'daily':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    entries = [e for e in data if e['user_id'] == str(user_id) and datetime.fromisoformat(e['date']) >= start]
    income = sum(e['amount'] for e in entries if e['type'] == 'income')
    expense = sum(e['amount'] for e in entries if e['type'] == 'expense')
    balance = income - expense
    lines = [f"Periode: {period.capitalize()}", f"Total pemasukan: Rp{income:,.0f}", f"Total pengeluaran: Rp{expense:,.0f}", f"Saldo: Rp{balance:,.0f}", "Rincian:"]
    for e in entries[-10:]:
        lines.append(f"- {e['date'][:10]} | {e['type']} | Rp{e['amount']:,.0f} | {e['note']}")
    if not entries:
        lines.append("Belum ada catatan untuk periode ini.")
    return "\n".join(lines)


def finance_analyze(user_id, period='daily'):
    from datetime import datetime, timedelta
    data = load_finance_data()
    now = datetime.utcnow()
    if period == 'daily':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    entries = [e for e in data if e['user_id'] == str(user_id) and datetime.fromisoformat(e['date']) >= start]
    income = sum(e['amount'] for e in entries if e['type'] == 'income')
    expense = sum(e['amount'] for e in entries if e['type'] == 'expense')
    balance = income - expense
    expense_breakdown = {}
    for e in entries:
        if e['type'] == 'expense':
            key = e['note'].split()[0] if e['note'] else 'other'
            expense_breakdown[key] = expense_breakdown.get(key, 0) + e['amount']
    analysis = f"📊 Analisis Keuangan {period.capitalize()}:\n\n"
    analysis += f"💰 Pemasukan: Rp{income:,.0f}\n"
    analysis += f"💸 Pengeluaran: Rp{expense:,.0f}\n"
    if balance >= 0:
        analysis += f"✅ Surplus: Rp{balance:,.0f}\n"
    else:
        analysis += f"⚠️ Defisit: Rp{abs(balance):,.0f}\n"
    if expense_breakdown:
        analysis += "\n📈 Pengeluaran by kategori:\n"
        for category, amount in sorted(expense_breakdown.items(), key=lambda x: x[1], reverse=True):
            pct = (amount / expense * 100) if expense > 0 else 0
            bar_length = int(pct / 5)
            bar = '█' * bar_length + '░' * (20 - bar_length)
            analysis += f"{category}: {bar} {pct:.1f}%\n"
    if expense > 0:
        avg_expense = expense / len([e for e in entries if e['type'] == 'expense'])
        analysis += f"\n🔢 Rata-rata per transaksi: Rp{avg_expense:,.0f}\n"
    return analysis


def parse_finance_natural(text):
    lower = text.lower()
    import re
    amount_match = re.search(r'(\d+[,.]?\d*)[k]?', lower)
    if not amount_match:
        return None
    amount_str = amount_match.group(1).replace('.', '').replace(',', '')
    amount = float(amount_str)
    if 'k' in lower[amount_match.end():amount_match.end()+3]:
        amount *= 1000
    if any(word in lower for word in ['masuk', 'dapat', 'terima', 'gaji', 'bonus', 'income', 'earning']):
        entry_type = 'income'
    elif any(word in lower for word in ['keluar', 'bayar', 'beli', 'expense', 'spending', 'belanja', 'beli', 'makan']):
        entry_type = 'expense'
    else:
        return None
    note_start = amount_match.end()
    note = text[note_start:].strip().lstrip('untuk').strip().lstrip('untuk').strip()
    return {'type': entry_type, 'amount': amount, 'note': note or 'catatan'}


def finance_analyze(user_id, period='daily'):
    from datetime import datetime, timedelta
    data = load_finance_data()
    now = datetime.utcnow()
    if period == 'daily':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    entries = [e for e in data if e['user_id'] == str(user_id) and datetime.fromisoformat(e['date']) >= start]
    income = sum(e['amount'] for e in entries if e['type'] == 'income')
    expense = sum(e['amount'] for e in entries if e['type'] == 'expense')
    balance = income - expense
    expense_breakdown = {}
    for e in entries:
        if e['type'] == 'expense':
            key = e['note'].split()[0] if e['note'] else 'other'
            expense_breakdown[key] = expense_breakdown.get(key, 0) + e['amount']
    analysis = f"📊 Analisis Keuangan {period.capitalize()}:\n\n"
    analysis += f"💰 Pemasukan: Rp{income:,.0f}\n"
    analysis += f"💸 Pengeluaran: Rp{expense:,.0f}\n"
    if balance >= 0:
        analysis += f"✅ Surplus: Rp{balance:,.0f}\n"
    else:
        analysis += f"⚠️ Defisit: Rp{abs(balance):,.0f}\n"
    if expense_breakdown:
        analysis += "\n📈 Pengeluaran by kategori:\n"
        for category, amount in sorted(expense_breakdown.items(), key=lambda x: x[1], reverse=True):
            pct = (amount / expense * 100) if expense > 0 else 0
            bar_length = int(pct / 5)
            bar = '█' * bar_length + '░' * (20 - bar_length)
            analysis += f"{category}: {bar} {pct:.1f}%\n"
    if expense > 0:
        avg_expense = expense / len([e for e in entries if e['type'] == 'expense'])
        analysis += f"\n🔢 Rata-rata per transaksi: Rp{avg_expense:,.0f}\n"
    return analysis


def get_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as f:
            pickle.dump(creds, f)
    return build('drive', 'v3', credentials=creds)

def clean_text(text):
    """Remove markdown chars"""
    return text.replace('*', '').replace('_', '').replace('[', '').replace(']', '')

def extract_text(file_content, file_name):
    text = ""
    try:
        if 'pdf' in file_name.lower():
            pdf = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf.pages[:2]:
                text += page.extract_text() + "\n"
    except:
        pass
    return clean_text(text[:3000])


def parse_text_response(result):
    if isinstance(result, dict):
        if 'text' in result:
            return result['text']
        if 'completion' in result:
            return result['completion']
        if 'output_text' in result:
            return result['output_text']
        if 'output' in result and isinstance(result['output'], str):
            return result['output']
        if 'choices' in result and result['choices']:
            choice = result['choices'][0]
            if isinstance(choice, dict):
                return choice.get('text') or choice.get('message', {}).get('content', '') or choice.get('output_text', '')
    return ''


def claude_summary(text):
    if not CLAUDE_API:
        raise ValueError('Claude API key tidak dikonfigurasi')
    url = 'https://api.anthropic.com/v1/complete'
    prompt = 'Ringkas dokumen ini (Indonesia, 100 kata): ' + text
    payload = json.dumps({
        'model': 'claude-3.5',
        'prompt': f"\n\nHuman: {prompt}\n\nAssistant:",
        'max_tokens_to_sample': 200,
        'temperature': 0.2,
        'stop_sequences': ['\n\nHuman:']
    }).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'X-API-Key': CLAUDE_API
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    output = parse_text_response(result)
    if not output:
        raise ValueError('Response Claude tidak berformat seperti yang diharapkan')
    return clean_text(output)


def ask_claude(text, context=None):
    if not CLAUDE_API:
        raise ValueError('Claude API key tidak dikonfigurasi')
    system_msg = "Anda adalah asisten yang membantu dengan jelas. Belajar gaya bahasa pengguna dan gunakan bahasa Indonesia sesuai konteks. Jika pertanyaan tidak jelas, minta klarifikasi."
    prompt = f"System: {system_msg}\n\n"
    if context and 'chat_history' in context.user_data:
        for msg in context.user_data['chat_history']:
            if msg['role'] == 'user':
                prompt += f"Human: {msg['content']}\n\n"
            else:
                prompt += f"Assistant: {msg['content']}\n\n"
    prompt += f"Human: {text}\n\nAssistant:"

    url = 'https://api.anthropic.com/v1/complete'
    payload = json.dumps({
        'model': 'claude-3.5',
        'prompt': prompt,
        'max_tokens_to_sample': 200,
        'temperature': 0.2,
        'stop_sequences': ['\n\nHuman:']
    }).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'X-API-Key': CLAUDE_API
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    output = parse_text_response(result)
    if not output:
        raise ValueError('Response Claude tidak berformat seperti yang diharapkan')
    return clean_text(output)


def normalize_yes(text):
    return text.strip().lower() in ['ya', 'y', 'yes', 'oke', 'ok', 'iya', 'sip']


def normalize_no(text):
    return text.strip().lower() in ['tidak', 'no', 'n', 'gak', 'ga', 'nggak', 'enggak']


def parse_natural_query(text, prefixes):
    lower = text.lower()
    for prefix in prefixes:
        if lower.startswith(prefix + ' '):
            return text[len(prefix) + 1:].strip()
        idx = lower.find(prefix + ' ')
        if idx != -1:
            return text[idx + len(prefix) + 1:].strip()
    return text.strip()


def remember_user_language(context, text):
    data = context.user_data
    if 'user_language' not in data:
        lower = text.lower()
        if any(word in lower for word in ['apa', 'itu', 'bagaimana', 'adakah', 'tolong', 'saya', 'kamu', 'sini']):
            data['user_language'] = 'Indonesia'
        else:
            data['user_language'] = 'Indonesia'
    if 'chat_history' not in data:
        data['chat_history'] = []
    if len(data['chat_history']) > 20:
        data['chat_history'] = data['chat_history'][-20:]


async def save_chat_history(context, role, message):
    history = context.user_data.setdefault('chat_history', [])
    history.append({'role': role, 'content': message})
    if len(history) > 20:
        del history[0]


async def ai_chat(text, context):
    remember_user_language(context, text)
    providers = []
    if CLAUDE_API:
        providers.append(('claude', ask_claude))

    if not providers:
        return 'AI Error: Tidak ada provider AI yang dikonfigurasi'

    last_error = None
    for name, func in providers:
        try:
            answer = func(text, context)
            await save_chat_history(context, 'user', text)
            await save_chat_history(context, 'assistant', answer)
            return answer
        except Exception as e:
            last_error = f'{name}: {e}'
    return f'AI Error: Semua provider gagal. Terakhir: {last_error}'


async def ai_summary(text):
    providers = []
    if CLAUDE_API:
        providers.append(('claude', claude_summary))

    if not providers:
        return 'AI Error: Tidak ada provider AI yang dikonfigurasi'

    last_error = None
    for name, func in providers:
        try:
            return func(text)
        except Exception as e:
            last_error = f'{name}: {e}'

    return f'AI Error: Semua provider gagal. Terakhir: {last_error}'


def get_pending_action(context):
    return context.user_data.get('pending_action')


async def clear_pending_action(context):
    if 'pending_action' in context.user_data:
        del context.user_data['pending_action']


def format_pending_label(pending):
    return pending.get('label', 'melakukan operasi')


async def execute_pending_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = get_pending_action(context)
    if not pending:
        await update.message.reply_text("Tidak ada aksi konfirmasi yang tertunda.")
        return

    action = pending.get('action')
    query = pending.get('query', '')
    await clear_pending_action(context)

    if action == 'cari':
        await execute_search(update, context, query)
    elif action == 'ai':
        await execute_ai_operation(update, context, query)
    elif action == 'photo':
        await execute_photo_operation(update, context, query)
    elif action == 'file':
        await execute_file_operation(update, context, query)
    elif action == 'rename':
        new_name = pending.get('new_name', '')
        await execute_rename_operation(update, context, query, new_name)
    else:
        await update.message.reply_text(f"Aksi tidak dikenal: {action}")


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = get_pending_action(context)
    if not pending:
        return False

    text = update.message.text or ''
    if normalize_yes(text):
        await execute_pending_action(update, context)
        return True
    if normalize_no(text):
        await clear_pending_action(context)
        await update.message.reply_text("Aksi dibatalkan.")
        return True

    await update.message.reply_text("Silakan ketik YA untuk melanjutkan atau TIDAK untuk membatalkan.")
    return True


def extract_dialog_query(text, keywords):
    lower = text.lower()
    for keyword in keywords:
        if keyword in lower:
            start = lower.find(keyword)
            return text[start + len(keyword):].strip()
    return ''


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    if not text:
        return

    if get_pending_action(context):
        acted = await handle_confirmation(update, context)
        if acted:
            return

    lower = text.lower()
    if any(keyword in lower for keyword in ['cari ', 'carikan ', 'search ', 'find ', 'carilah ', 'ambil ', 'ambilkan ', 'download ', 'unduh ']):
        query = extract_dialog_query(text, ['cari ', 'carikan ', 'search ', 'find ', 'carilah ', 'ambil ', 'ambilkan ', 'download ', 'unduh '])
        if query:
            context.user_data['pending_action'] = {
                'action': 'file',
                'query': query,
                'label': f"mengambil file dengan nama '{query}'"
            }
            await update.message.reply_text(
                f"Saya akan mengambil data dari Google Drive untuk {query}. Ketik YA untuk lanjut atau TIDAK untuk batal."
            )
            return
    if any(keyword in lower for keyword in ['foto ', 'photo ', 'image ', 'gambar ']):
        query = extract_dialog_query(text, ['foto ', 'photo ', 'image ', 'gambar '])
        if query:
            context.user_data['pending_action'] = {
                'action': 'photo',
                'query': query,
                'label': f"mengambil foto dengan nama '{query}'"
            }
            await update.message.reply_text(
                f"Saya akan mengambil data dari Google Drive untuk foto {query}. Ketik YA untuk lanjut atau TIDAK untuk batal."
            )
            return
    if any(keyword in lower for keyword in ['ringkas ', 'summar', 'resume ', 'buat ringkasan '] ):
        query = extract_dialog_query(text, ['ringkas ', 'resume ', 'buat ringkasan ', 'summarize ', 'summar '])
        if query:
            context.user_data['pending_action'] = {
                'action': 'ai',
                'query': query,
                'label': f"mencari dan merangkum file '{query}'"
            }
            await update.message.reply_text(
                f"Saya akan mengambil data dari Google Drive untuk file {query}. Ketik YA untuk lanjut atau TIDAK untuk batal."
            )
            return
    if any(keyword in lower for keyword in ['ganti nama ', 'rename '] ):
        query = extract_dialog_query(text, ['ganti nama ', 'rename '])
        if query and ' menjadi ' in query:
            parts = query.split(' menjadi ', 1)
            if len(parts) == 2:
                old_name = parts[0].strip()
                new_name = parts[1].strip()
                context.user_data['pending_action'] = {
                    'action': 'rename',
                    'query': old_name,
                    'new_name': new_name,
                    'label': f"mengganti nama file '{old_name}' menjadi '{new_name}'"
                }
                await update.message.reply_text(
                    f"Saya akan mengganti nama file {old_name} menjadi {new_name}. Ketik YA untuk lanjut atau TIDAK untuk batal."
                )
                return
    if any(keyword in lower for keyword in ['catat income', 'catat pemasukan', 'catat pengeluaran', 'catat expense', 'income ', 'expense ', 'pengeluaran ', 'pemasukan ']):
        finance_entry = parse_finance_natural(text)
        if finance_entry:
            add_finance_entry(update.effective_user.id, finance_entry['type'], finance_entry['amount'], finance_entry['note'])
            await update.message.reply_text(f"✅ {finance_entry['type'].capitalize()} dicatat: Rp{finance_entry['amount']:,.0f} | {finance_entry['note']}")
            return
    if any(keyword in lower for keyword in ['laporan ', 'analisis keuangan', 'laporan keuangan', 'budget', 'keuangan', 'summary keuangan']):
        period = 'daily'
        if any(w in lower for w in ['minggu', 'weekly', 'week', 'mingguan']):
            period = 'weekly'
        analysis = finance_analyze(update.effective_user.id, period=period)
        await update.message.reply_text(analysis)
        return

    answer = await ai_chat(text, context)
    await update.message.reply_text(answer)


async def execute_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    try:
        service = get_drive_service()
        results = service.files().list(
            q="name contains '" + query + "' and trashed=false",
            pageSize=5,
            fields="files(id,name,mimeType)"
        ).execute()
        files = results.get('files', [])
        if not files:
            await update.message.reply_text("File tidak ditemukan: " + query)
            return
        msg = "Hasil pencarian " + query + ":\n\n"
        for f in files:
            icon = "Folder" if "folder" in f['mimeType'] else "File"
            msg += icon + ": " + f['name'] + "\n"
            msg += "https://drive.google.com/file/d/" + f['id'] + "/view\n\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("Error saat mencari file: " + str(e))


async def execute_ai_operation(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    await update.message.reply_text("AI scanning: " + query)
    try:
        service = get_drive_service()
        results = service.files().list(q="name contains '" + query.split()[-1] + "'", pageSize=1).execute()
        files = results.get('files', [])
        if not files:
            await update.message.reply_text("File tidak ditemukan")
            return
        file = files[0]
        request = service.files().get_media(fileId=file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        text = extract_text(fh.read(), file['name'])
        if len(text) < 50:
            await update.message.reply_text("File OK: " + file['name'])
            return
        summary = await ai_summary(text)
        await update.message.reply_text(
            "File: " + file['name'] + "\n" +
            "Link: https://drive.google.com/file/d/" + file['id'] + "/view\n\n" +
            "AI Summary:\n" + summary
        )
    except Exception as e:
        await update.message.reply_text("Error saat mengambil dan merangkum: " + str(e))


async def execute_file_operation(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    try:
        service = get_drive_service()
        mime_clause = normalize_file_type(query)
        files = get_drive_files(service, query, mime_clause=mime_clause, pageSize=3)
        if not files:
            await update.message.reply_text("File tidak ditemukan: " + query)
            return
        msg = "Hasil pencarian file: " + query + ":\n\n"
        for f in files:
            msg += f"{f['mimeType']}: {f['name']}\n"
            msg += "https://drive.google.com/file/d/" + f['id'] + "/view\n\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("Error saat mengambil file: " + str(e))


async def execute_photo_operation(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    try:
        service = get_drive_service()
        files = get_drive_files(service, query, mime_clause="mimeType contains 'image/'", pageSize=1)
        if not files:
            await update.message.reply_text("Foto tidak ditemukan: " + query)
            return
        file = files[0]
        request = service.files().get_media(fileId=file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        await update.message.reply_photo(photo=fh, caption="Foto: " + file['name'])
    except Exception as e:
        await update.message.reply_text("Error saat mengambil foto: " + str(e))


async def execute_rename_operation(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, new_name: str):
    try:
        service = get_drive_service()
        files = get_drive_files(service, query, pageSize=1)
        if not files:
            await update.message.reply_text("File tidak ditemukan: " + query)
            return
        file = files[0]
        updated = service.files().update(fileId=file['id'], body={'name': new_name}).execute()
        await update.message.reply_text(f"Nama file berhasil diganti: {file['name']} -> {updated['name']}")
    except Exception as e:
        await update.message.reply_text("Error saat mengganti nama file: " + str(e))

# ==============================
# COMMANDS - PLAIN TEXT ONLY
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
GDrive AI Bot - Commands:

 /cari nama_file - Cari file
 /file nama_file - Ambil file umum (laporan, aplikasi, video)
 /photo nama_foto - Ambil foto spesifik dari Drive
 /rename nama_file|nama_baru - Ganti nama file di Drive
 /ai nama_file - AI analisis
 /tanya pertanyaan - Chat / pertanyaan umum
 /income jumlah deskripsi - Catat pemasukan
 /expense jumlah deskripsi - Catat pengeluaran
 /finance daily|weekly - Laporan keuangan
 /sum nama_file - Ringkasan
 /list nama_folder - Isi folder

Contoh:
 /cari laporan
 /file video meeting
 /photo liburan
 /rename laporan lama|laporan baru
 /ai proposal.pdf
 /tanya dokumen ini apa isinya?
 /income 500000 gaji
 /expense 75000 makan
 /finance weekly
    """)

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Format: /cari laporan")
        return
    if len(query.strip()) < 3:
        await update.message.reply_text("Nama file terlalu pendek. Jelaskan lebih jelas.")
        return
    context.user_data['pending_action'] = {
        'action': 'cari',
        'query': query.strip(),
        'label': f"mencari file dengan nama '{query.strip()}'"
    }
    await update.message.reply_text(
        f"Saya akan mengambil data dari Google Drive untuk {query.strip()}. Ketik YA untuk lanjut atau TIDAK untuk batal."
    )

async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Format: /ai nama_file")
        return
    if len(query.strip()) < 5:
        await update.message.reply_text("Pertanyaan terlalu singkat. jelaskan nama file dengan lebih jelas, misalnya: /ai proposal.pdf")
        return
    context.user_data['pending_action'] = {
        'action': 'ai',
        'query': query.strip(),
        'label': f"mencari dan merangkum file '{query.strip()}'"
    }
    await update.message.reply_text(
        f"Saya akan mengambil data dari Google Drive untuk {query.strip()}. Ketik YA untuk lanjut atau TIDAK untuk batal."
    )

async def sum_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gunakan /ai untuk ringkasan")

async def file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Format: /file nama_file")
        return
    if len(query.strip()) < 3:
        await update.message.reply_text("Nama file terlalu pendek. Jelaskan lebih jelas.")
        return
    context.user_data['pending_action'] = {
        'action': 'file',
        'query': query.strip(),
        'label': f"mengambil file dengan nama '{query.strip()}'"
    }
    await update.message.reply_text(
        f"Saya akan mengambil data dari Google Drive untuk {query.strip()}. Ketik YA untuk lanjut atau TIDAK untuk batal."
    )


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Format: /photo nama_foto")
        return
    if len(query.strip()) < 3:
        await update.message.reply_text("Pertanyaan foto terlalu pendek. pakai nama file lebih jelas.")
        return
    context.user_data['pending_action'] = {
        'action': 'photo',
        'query': query.strip(),
        'label': f"mengambil foto dengan nama '{query.strip()}'"
    }
    await update.message.reply_text(
        f"Saya akan mengambil data dari Google Drive untuk foto {query.strip()}. Ketik YA untuk lanjut atau TIDAK untuk batal."
    )


async def rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if '|' not in query and ' menjadi ' not in query:
        await update.message.reply_text("Format: /rename nama_file|nama_baru atau /rename nama_file menjadi nama_baru")
        return
    if '|' in query:
        old_name, new_name = [p.strip() for p in query.split('|', 1)]
    else:
        old_name, new_name = [p.strip() for p in query.split(' menjadi ', 1)]
    if not old_name or not new_name:
        await update.message.reply_text("Format: /rename nama_file|nama_baru")
        return
    context.user_data['pending_action'] = {
        'action': 'rename',
        'query': old_name,
        'new_name': new_name,
        'label': f"mengganti nama file '{old_name}' menjadi '{new_name}'"
    }
    await update.message.reply_text(
        f"Saya akan mengganti nama file {old_name} menjadi {new_name}. Ketik YA untuk lanjut atau TIDAK untuk batal."
    )


async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    parsed = parse_finance_natural(text)
    if parsed:
        add_finance_entry(update.effective_user.id, parsed['type'], parsed['amount'], parsed['note'])
        msg = f"Pemasukan dicatat: Rp{parsed['amount']:,.0f}"
        if parsed['note']:
            msg += f" | {parsed['note']}"
        await update.message.reply_text(msg)
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: /income jumlah deskripsi\nContoh: /income 500000 gaji atau /income 500k dapat bonus")
        return
    try:
        amount = float(context.args[0].replace(',', '').replace('k', '000'))
    except ValueError:
        await update.message.reply_text("Jumlah tidak valid. Contoh: /income 500000 gaji")
        return
    note = ' '.join(context.args[1:])
    add_finance_entry(update.effective_user.id, 'income', amount, note)
    await update.message.reply_text(f"Pemasukan dicatat: Rp{amount:,.0f} | {note}")


async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    parsed = parse_finance_natural(text)
    if parsed:
        add_finance_entry(update.effective_user.id, parsed['type'], parsed['amount'], parsed['note'])
        msg = f"Pengeluaran dicatat: Rp{parsed['amount']:,.0f}"
        if parsed['note']:
            msg += f" | {parsed['note']}"
        await update.message.reply_text(msg)
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: /expense jumlah deskripsi\nContoh: /expense 75000 makan atau /expense 50k beli buku")
        return
    try:
        amount = float(context.args[0].replace(',', '').replace('k', '000'))
    except ValueError:
        await update.message.reply_text("Jumlah tidak valid. Contoh: /expense 75000 makan")
        return
    note = ' '.join(context.args[1:])
    add_finance_entry(update.effective_user.id, 'expense', amount, note)
    await update.message.reply_text(f"Pengeluaran dicatat: Rp{amount:,.0f} | {note}")


async def finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    period = 'daily'
    if context.args:
        if context.args[0].lower() in ['weekly', 'week', 'w']:
            period = 'weekly'
        elif context.args[0].lower() in ['daily', 'day', 'd']:
            period = 'daily'
    analysis = finance_analyze(update.effective_user.id, period=period)
    await update.message.reply_text(analysis)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return
    largest = update.message.photo[-1]
    tg_file = await context.bot.get_file(largest.file_id)
    buf = io.BytesIO()
    await tg_file.download(out=buf)
    buf.seek(0)
    context.user_data['last_photo'] = buf.getvalue()
    await update.message.reply_text("Foto diterima. Jelaskan apa yang ingin Anda ketahui tentang foto ini, atau kirim /tanya [pertanyaan].")

async def tanya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Format: /tanya pertanyaan anda")
        return
    if len(query.strip()) < 5:
        await update.message.reply_text("Pertanyaan terlalu singkat. Jelaskan maksud Anda dengan lebih detail.")
        return
    answer = await ai_chat(query)
    await update.message.reply_text(answer)

if __name__ == '__main__':
    try:
        logger.info('🚀 GDrive AI Bot starting...')
        logger.info(f'📍 Bot Token: {BOT_TOKEN[:15]}...')
        logger.info(f'🤖 Claude API: {"Configured" if CLAUDE_API else "Not configured"}')
        
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('cari', cari))
        app.add_handler(CommandHandler('file', file))
        app.add_handler(CommandHandler('photo', photo))
        app.add_handler(CommandHandler('rename', rename))
        app.add_handler(CommandHandler('ai', ai))
        app.add_handler(CommandHandler('tanya', tanya))
        app.add_handler(CommandHandler('income', income))
        app.add_handler(CommandHandler('expense', expense))
        app.add_handler(CommandHandler('finance', finance))
        app.add_handler(CommandHandler('sum', sum_file))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        logger.info('✅ Bot online! Siap melayani...')
        print('✅ Bot running! Access via Telegram.')
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f'❌ Bot error: {e}', exc_info=True)
        raise
