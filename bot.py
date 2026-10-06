import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from tradingview_ta import TA_Handler, Interval

# --- KONFIGURASI BOT ---
TOKEN = '8002426439:AAGklbO3nNo6k8oEfdXyYzCslIw0Z5UBDeE'
bot = telebot.TeleBot(TOKEN)

# Kamus daftar pair default untuk fitur Scanning Massal
DAFTAR_PAIR = {
    "CRYPTO": [
        {"symbol": "BTCUSDT", "screener": "crypto", "exchange": "BINANCE"},
        {"symbol": "ETHUSDT", "screener": "crypto", "exchange": "BINANCE"},
        {"symbol": "BNBUSDT", "screener": "crypto", "exchange": "BINANCE"},
        {"symbol": "SOLUSDT", "screener": "crypto", "exchange": "BINANCE"}
    ],
    "FOREX": [
        {"symbol": "EURUSD", "screener": "forex", "exchange": "FX_IDC"},
        {"symbol": "GBPUSD", "screener": "forex", "exchange": "FX_IDC"},
        {"symbol": "USDJPY", "screener": "forex", "exchange": "FX_IDC"}
    ],
    "COMMODITY": [
        {"symbol": "XAUUSD", "screener": "forex", "exchange": "FX_IDC"}
    ]
}

MAP_TIMEFRAME = {
    "M1": Interval.INTERVAL_1_MINUTE,
    "M5": Interval.INTERVAL_5_MINUTES,
    "M15": Interval.INTERVAL_15_MINUTES,
    "H1": Interval.INTERVAL_1_HOUR,
    "H4": Interval.INTERVAL_4_HOURS,
    "D1": Interval.INTERVAL_1_DAY
}

user_states = {}

def get_user_tf(chat_id):
    if chat_id not in user_states:
        user_states[chat_id] = {"tf": "D1", "mode": "FREE"}
    return user_states[chat_id]["tf"]

def dapatkan_analisis(symbol, screener="crypto", exchange="BINANCE", tf_str="D1"):
    try:
        interval_obj = MAP_TIMEFRAME.get(tf_str, Interval.INTERVAL_1_DAY)
        analisis = TA_Handler(
            symbol=symbol.strip().upper(),
            screener=screener.strip().lower(),
            exchange=exchange.strip().upper(),
            interval=interval_obj
        )
        hasil = analisis.get_analysis()

        rekomendasi = hasil.summary['RECOMMENDATION']
        buy = hasil.summary['BUY']
        sell = hasil.summary['SELL']
        neutral = hasil.summary['NEUTRAL']

        pesan = f"📊 *Analisis Pasaran: {symbol.upper()}*\n"
        pesan += f"⏱ *Timeframe:* {tf_str}\n"
        pesan += f"🏛 *Exchange:* {exchange.upper()}\n\n"
        pesan += f"📢 *Rekomendasi Utama:* `{rekomendasi}`\n"
        pesan += f"📈 Indikator Beli (Buy): {buy}\n"
        pesan += f"📉 Indikator Jual (Sell): {sell}\n"
        pesan += f"⏳ Netral: {neutral}\n\n"
        pesan += "_Disclaimer: Analisis matematika indikator, bukan ajakan finansial._"
        return pesan
    except Exception as e:
        print(f"Error pada {symbol}: {e}")
        return f"❌ Gagal menganalisis `{symbol}`."

def menu_utama_markup(chat_id):
    tf_aktif = get_user_tf(chat_id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔍 Scan Massal", callback_data="menu_scan"),
        InlineKeyboardButton("🔎 Cari Pair Custom", callback_data="menu_cari")
    )
    markup.add(InlineKeyboardButton(f"⏱ Timeframe: [{tf_aktif}]", callback_data="menu_tf"))
    return markup

def menu_tf_markup():
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(tf, callback_data=f"set_tf_{tf}") for tf in MAP_TIMEFRAME.keys()]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("⬅️ Kembali", callback_data="kembali_utama"))
    return markup

def menu_scan_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🚀 Crypto Populer", callback_data="scan_CRYPTO"),
        InlineKeyboardButton("💵 Forex Mayor", callback_data="scan_FOREX"),
        InlineKeyboardButton("👑 XAUUSD (Emas)", callback_data="scan_COMMODITY"),
        InlineKeyboardButton("⬅️ Kembali", callback_data="kembali_utama")
    )
    return markup

@bot.message_handler(commands=['start', 'help', 'menu'])
def kirim_sambutan(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = {"tf": "D1", "mode": "FREE"}
    bot.send_message(chat_id, "🤖 *Selamat Datang di TradingView Signal Bot!*", parse_mode="Markdown", reply_markup=menu_utama_markup(chat_id))

@bot.callback_query_handler(func=lambda call: True)
def proses_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    if data == "kembali_utama":
        bot.edit_message_text("🤖 *Menu Utama Analisis:*", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=menu_utama_markup(chat_id))

    elif data == "menu_tf":
        bot.edit_message_text("⏱ *Pilih Timeframe:*", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=menu_tf_markup())

    elif data.startswith("set_tf_"):
        tf_baru = data.replace("set_tf_", "")
        user_states[chat_id] = {"tf": tf_baru}
        bot.edit_message_text(f"✅ Timeframe diatur ke *{tf_baru}*.", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=menu_utama_markup(chat_id))

    elif data == "menu_scan":
        bot.edit_message_text("🔍 *Pilih Kelompok Pasar:*", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=menu_scan_markup())

    elif data.startswith("scan_"):
        kategori = data.replace("scan_", "")
        tf_sekarang = get_user_tf(chat_id)
        bot.send_message(chat_id, f"⏳ Scanning {kategori} (TF: {tf_sekarang})...")
        
        for item in DAFTAR_PAIR.get(kategori, []):
            teks = dapatkan_analisis(item["symbol"], item["screener"], item["exchange"], tf_sekarang)
            bot.send_message(chat_id, teks, parse_mode="Markdown")
            time.sleep(1.5)

    elif data == "menu_cari":
        bot.edit_message_text("🔎 *Mode Cari:* Ketik nama pair (misal: `btc`, `eurusd`, `xauusd`):", chat_id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def proses_input_teks(message):
    chat_id = message.chat.id
    symbol = message.text.strip().upper()
    tf_sekarang = get_user_tf(chat_id)
    screener, exchange = "crypto", "BINANCE"

    if "USD" not in symbol and len(symbol) <= 5: symbol += "USDT"
    if any(f in symbol for f in ["EUR", "GBP", "JPY", "AUD", "CAD"]):
        screener, exchange = "forex", "FX_IDC"
    elif "XAU" in symbol or "GOLD" in symbol:
        symbol, screener, exchange = "XAUUSD", "forex", "FX_IDC"

    bot.reply_to(message, f"⏳ Menganalisis `{symbol}`...", parse_mode="Markdown")
    hasil = dapatkan_analisis(symbol, screener, exchange, tf_sekarang)
    bot.send_message(chat_id, hasil, parse_mode="Markdown", reply_markup=menu_utama_markup(chat_id))

if __name__ == "__main__":
    print("Bot Fly.io berjalan...")
    bot.infinity_polling()