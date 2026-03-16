import requests
import time
from datetime import datetime
import pytz
from flask import Flask
import threading
import os

# ================= CẤU HÌNH =================
BOT_TOKEN = "8590476877:AAEzGcryuXjIk3E1zk7c7FBePHGSoTrWTCs"
CHAT_ID = "8405954014" # UID của bạn
WALLET_ADDRESS = "0x8b93f35D755B3a751722783652CBB083D343723d"

TRACKED_COINS = {
    "BABYDOGE": {"symbol": "🐶", "min_payout": 1000000000}, 
    "POL": {"symbol": "🟣", "min_payout": 3}       
}

CHECK_INTERVAL = 60  # Đã đổi thành 60 giây (1 phút)
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    return "Trang web giả này giúp Bot Unmineable luôn thức 24/7 trên Render!"

def get_unmineable_balance(coin):
    api_url = f"https://api.unmineable.com/v4/address/{WALLET_ADDRESS}?coin={coin}"
    try:
        response = requests.get(api_url, timeout=10)
        data = response.json()
        if data.get('success'):
            return float(data['data']['balance'])
        return None
    except Exception as e:
        print(f"Lỗi khi kết nối API cho {coin}: {e}")
        return None

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi khi gửi tin Telegram: {e}")

def bot_loop():
    print("🚀 Bắt đầu chạy Bot ngầm...")
    last_balances = {}
    
    for coin in TRACKED_COINS:
        balance = get_unmineable_balance(coin)
        last_balances[coin] = balance if balance is not None else 0.0
        print(f"[*] Số dư khởi tạo {coin}: {last_balances[coin]:.6f}")

    while True:
        now_log = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{now_log}] 🔍 Đang quét API kiểm tra số dư mới...")
        
        for coin, info in TRACKED_COINS.items():
            symbol = info["symbol"]
            min_payout = info["min_payout"]
            current_balance = get_unmineable_balance(coin)
            
            if current_balance is not None and current_balance > last_balances[coin]:
                added_amount = current_balance - last_balances[coin]
                remaining = min_payout - current_balance
                if remaining <= 0:
                    remaining_text = "✅ Đã đủ số lượng min rút!"
                else:
                    remaining_text = f"<code>{remaining:,.6f}</code> {coin}"
                
                vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                current_time_vn = datetime.now(vn_tz).strftime('%H:%M:%S | %d/%m/%Y')
                short_wallet = f"{WALLET_ADDRESS[:6]}...{WALLET_ADDRESS[-4:]}"
                
                message = (
                    f"{symbol} <b>THÔNG BÁO NHẬN {coin}</b> {symbol}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔹 <b>Đồng coin:</b> {coin}\n"
                    f"🔹 <b>Cộng thêm:</b> <code>+{added_amount:,.6f}</code> {coin}\n"
                    f"🔹 <b>Tổng số dư:</b> <code>{current_balance:,.6f}</code> {coin}\n"
                    f"🎯 <b>Còn thiếu (Min {min_payout:,.0f}):</b> {remaining_text}\n"
                    f"⏰ <b>Thời gian:</b> {current_time_vn} (VN)\n"
                    f"🔗 <b>Địa chỉ ví:</b> {short_wallet}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡️ <i>Hệ thống theo dõi tự động</i>"
                )
                
                send_telegram_message(message)
                print(f"[{current_time_vn}] ✅ Đã gửi thông báo: +{added_amount:.6f} {coin}")
                last_balances[coin] = current_balance
            
            time.sleep(2)
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Chạy vòng lặp bot ở một luồng (thread) chạy ngầm
    t = threading.Thread(target=bot_loop)
    t.daemon = True
    t.start()
    
    # Chạy trang web giả trên luồng chính
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
