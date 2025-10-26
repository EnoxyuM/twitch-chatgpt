import requests
import telegram
import time
import os

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET')
TWITCH_USERNAME = os.environ.get('TWITCH_USERNAME')

# --- Переменная для отслеживания состояния стрима ---
is_live = False

# --- Функции ---
def get_twitch_access_token():
    """Получает токен доступа для Twitch API."""
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, params=params)
    response.raise_for_status() # Проверка на ошибки HTTP
    return response.json().get('access_token')

def check_stream_status(access_token):
    """Проверяет, онлайн ли стрим."""
    url = f'https://api.twitch.tv/helix/streams?user_login={TWITCH_USERNAME}'
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('data')[0] if data.get('data') else None
    except Exception as e:
        print(f"Ошибка при запросе к Twitch API: {e}")
        return None

def send_telegram_notification(bot, stream_info):
    """Отправляет уведомление в Telegram."""
    title = stream_info.get('title', 'Без названия')
    game = stream_info.get('game_name', 'Не указана')
    message = (
        f"🔥 СТРИМ НАЧАЛСЯ! 🔥\n\n"
        f"💬 **{title}**\n"
        f"🎮 Игра: **{game}**\n\n"
        f"🔗 Присоединяйтесь: https://www.twitch.tv/{TWITCH_USERNAME}"
    )
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode=telegram.ParseMode.MARKDOWN
        )
        print("Уведомление успешно отправлено в Telegram.")
    except Exception as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")

# --- Основной цикл ---
if __name__ == '__main__':
    # Проверяем наличие всех переменных окружения
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_USERNAME]):
        print("Ошибка: не все переменные окружения заданы!")
    else:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        access_token = get_twitch_access_token()

        if not access_token:
            print("Не удалось получить токен доступа Twitch. Проверьте Client ID и Secret.")
        else:
            print("Бот запущен. Начинаю проверку статуса стрима...")
            while True:
                stream_info = check_stream_status(access_token)
                
                if stream_info and not is_live:
                    print(f"{TWITCH_USERNAME} онлайн! Отправляю уведомление.")
                    send_telegram_notification(bot, stream_info)
                    is_live = True
                elif not stream_info and is_live:
                    print(f"{TWITCH_USERNAME} теперь оффлайн.")
                    is_live = False
                else:
                    # Просто для отладки, чтобы видеть, что скрипт работает
                    status = "Онлайн" if is_live else "Оффлайн"
                    print(f"Проверка... {TWITCH_USERNAME} сейчас {status}. Следующая проверка через 60 секунд.")

                time.sleep(60) # Пауза 60 секунд