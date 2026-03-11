import time
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime
from telegram import Bot
import asyncio
from flask import Flask
from threading import Thread

# ------------------ সেটিংস ------------------
TELEGRAM_TOKEN = "8691655581:AAFiyQ_5ZhnCscNktX_AhyQBP4w2v5AkZak"
CHAT_ID = "7819937011"
SYMBOL = "EURUSD=X"
TIMEFRAME = "1m"
EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

bot = Bot(token=TELEGRAM_TOKEN)

# --- বটের স্থায়িত্বের জন্য Flask সার্ভার ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()
# -----------------------------------------

async def send_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
    except Exception as e:
        print(f"Telegram পাঠাতে সমস্যা: {e}")

def get_data():
    try:
        data = yf.download(tickers=SYMBOL, period="1d", interval=TIMEFRAME, progress=False)
        if data.empty:
            return None
        data = data[['Open', 'High', 'Low', 'Close']]
        data.columns = ['open', 'high', 'low', 'close']
        return data
    except Exception as e:
        print(f"ডেটা ডাউনলোডে সমস্যা: {e}")
        return None

def generate_signal(df):
    if len(df) < EMA_SLOW + 10:
        return None, None, None

    df['ema_fast'] = ta.ema(df['close'], length=EMA_FAST)
    df['ema_slow'] = ta.ema(df['close'], length=EMA_SLOW)
    df['rsi'] = ta.rsi(df['close'], length=RSI_PERIOD)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    direction = None
    if prev['ema_fast'] < prev['ema_slow'] and last['ema_fast'] > last['ema_slow']:
        direction = "UP 🔼 (Call)"
    elif prev['ema_fast'] > prev['ema_slow'] and last['ema_fast'] < last['ema_slow']:
        direction = "DOWN 🔽 (Put)"

    if direction == "UP 🔼 (Call)" and last['rsi'] < RSI_OVERSOLD + 15:
        pass
    elif direction == "DOWN 🔽 (Put)" and last['rsi'] > RSI_OVERBOUGHT - 15:
        pass
    else:
        direction = None

    return direction, round(float(last['rsi']), 1), round(float(last['close']), 5)

async def main_loop():
    last_time = None
    print("Signal Bot Starting...")
    
    while True:
        try:
            df = get_data()
            if df is None:
                await asyncio.sleep(30)
                continue

            current_time = df.index[-1]
            if last_time == current_time:
                await asyncio.sleep(10)
                continue

            last_time = current_time
            signal, rsi_val, price = generate_signal(df)

            if signal:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                msg = (
                    f"**EUR/USD {TIMEFRAME} সিগন্যাল**\n"
                    f"**{signal}**\n"
                    f"Price: {price}\n"
                    f"RSI: {rsi_val}\n"
                    f"Time: {now}\n"
                    f"Channel: @sheikhsabbiryt"
                )
                await send_message(msg)

            await asyncio.sleep(10)
        except Exception as e:
            print(f"লুপে সমস্যা: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    keep_alive() # সার্ভার চালু করা
    asyncio.run(main_loop()) # বট লুপ চালু করা
