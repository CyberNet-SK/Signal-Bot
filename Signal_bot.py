import yfinance as yf
from telegram import Bot
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime

# ------------------ সেটিংস ------------------
TELEGRAM_TOKEN = "8691655581:AAFiyQ_5ZhnCscNktX_AhyQBP4w2v5AkZak"
CHAT_ID = "7819937011"
SYMBOL = "EURUSD=X"
TIMEFRAME = "1m"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask('')

@app.route('/')
def home(): return "Bot is Running!"

def run_server(): app.run(host='0.0.0.0', port=8080)

def calculate_ema(prices, days):
    if len(prices) < days: return [0]*len(prices)
    ema = [sum(prices[:days]) / days]
    multiplier = 2 / (days + 1)
    for i in range(days, len(prices)):
        ema.append((prices[i] - ema[-1]) * multiplier + ema[-1])
    return [0]*(days-1) + ema

def calculate_rsi(prices, period=14):
    if len(prices) < period: return 50
    deltas = [prices[i+1]-prices[i] for i in range(len(prices)-1)]
    gain = [d if d > 0 else 0 for d in deltas]
    loss = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gain[:period]) / period
    avg_loss = sum(loss[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gain[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

async def main_loop():
    last_time = None
    while True:
        try:
            data = yf.download(tickers=SYMBOL, period="1d", interval=TIMEFRAME, progress=False)
            if data.empty:
                await asyncio.sleep(30); continue
            
            curr_time = data.index[-1]
            if last_time == curr_time:
                await asyncio.sleep(10); continue
            last_time = curr_time

            closes = data['Close'].tolist()
            ema9 = calculate_ema(closes, 9)
            ema21 = calculate_ema(closes, 21)
            rsi = calculate_rsi(closes, 14)

            # Signal Logic
            if ema9[-2] < ema21[-2] and ema9[-1] > ema21[-1] and rsi < 45:
                msg = f"🟢 **BUY (Call)**\nPrice: {round(closes[-1], 5)}\nRSI: {round(rsi, 2)}"
                await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            elif ema9[-2] > ema21[-2] and ema9[-1] < ema21[-1] and rsi > 55:
                msg = f"🔴 **SELL (Put)**\nPrice: {round(closes[-1], 5)}\nRSI: {round(rsi, 2)}"
                await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')

            await asyncio.sleep(15)
        except Exception as e:
            print(f"Error: {e}"); await asyncio.sleep(30)

if __name__ == "__main__":
    Thread(target=run_server).start()
    asyncio.run(main_loop())
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
