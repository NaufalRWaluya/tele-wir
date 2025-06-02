import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openpyxl import Workbook

# Load token dari .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Simpan data makanan dalam memori sementara
user_data = []

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Halo! saya adalah Bot Wirausaha Sakti.\n"
                                    "Ketikkan data dalam format: Nama Makanan/Minuman - Harga")

# Handler pesan user: Nama Makanan - Harga
async def log_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message.text.strip()

    # Cek apakah format valid
    if '-' in message:
        try:
            nama, harga = message.split('-', 1)
            nama = nama.strip()
            harga = int(harga.strip())

            user_data.append((nama, harga))
            logger.info(f"Input dari @{user.username or user.id}: {nama} - {harga}")
            await update.message.reply_text(f"✅ Tersimpan: {nama} - Rp{harga:,}")
        except ValueError:
            await update.message.reply_text("⚠️ Format harga tidak valid. Gunakan angka.\nContoh: Nasi Goreng - 15000")
    else:
        await update.message.reply_text("⚠️ Format tidak dikenali. Gunakan format: Nama Makanan/Minuman - Harga")

# Command: /savelaporan
async def save_laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_data:
        await update.message.reply_text("📭 Belum ada data yang bisa disimpan.")
        return

    # Buat file Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Laporan Pemasukan"

    # Header
    ws.append(["No", "Nama", "Harga (Rp)"])

    total = 0
    for idx, (nama, harga) in enumerate(user_data, start=1):
        ws.append([idx, nama, harga])
        total += harga

    # Tambahkan total
    ws.append([])
    ws.append(["", "TOTAL", total])

    # Simpan file
    file_path = "laporan_pemasukan.xlsx"
    wb.save(file_path)

    # Kirim file ke user
    await update.message.reply_document(document=open(file_path, "rb"))

    # Opsional: Hapus file setelah dikirim
    os.remove(file_path)

# Command: /laporan
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_data:
        await update.message.reply_text("📭 Belum ada data makanan/minuman yang tercatat.")
        return

    # Buat daftar laporan
    laporan_text = "📋 *Laporan Pemasukan:*\n"
    total = 0
    for idx, (nama, harga) in enumerate(user_data, 1):
        laporan_text += f"{idx}. {nama} - Rp{harga:,}\n"
        total += harga
    laporan_text += f"\n💰 *Total:* Rp{total:,}"

    await update.message.reply_text(laporan_text, parse_mode="Markdown")

# Main app
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN tidak ditemukan di file .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_user_message))
    app.add_handler(CommandHandler("savelaporan", save_laporan))

    print("Bot sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
