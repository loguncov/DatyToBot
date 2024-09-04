import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from datetime import datetime
import json

# Токен вашего бота
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Имя файла для хранения данных
FILE_NAME = 'user_dates.json'

# Функция для загрузки данных из файла
def load_user_dates():
    try:
        with open(FILE_NAME, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Функция для сохранения данных в файл
def save_user_dates(user_dates):
    with open(FILE_NAME, 'w') as file:
        json.dump(user_dates, file)

# Загрузить данные при запуске
user_dates = load_user_dates()

# Функция для отображения меню с кнопками
def get_main_menu():
    keyboard = [
        ['Узнать оставшееся время', 'Добавить дату'],
        ['Изменить дату', 'Удалить дату'],
        ['Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Команда /start
async def start(update: Update, context):
    await update.message.reply_text(
        "Привет! Выберите действие:",
        reply_markup=get_main_menu()
    )

# Обработка сообщения с датой
async def handle_message(update: Update, context):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if text == 'Узнать оставшееся время':
        if user_id in user_dates and isinstance(user_dates[user_id], dict) and user_dates[user_id]:
            # Если у пользователя есть сохраненные даты, показываем их
            date_names = list(user_dates[user_id].keys())
            keyboard = [[name] for name in date_names] + [['Отмена']]
            await update.message.reply_text(
                "Выберите событие, чтобы узнать оставшееся время:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            context.user_data['awaiting_event_selection'] = True
        else:
            await update.message.reply_text(
                "У вас нет сохранённых дат. Выберите 'Добавить дату', чтобы добавить.",
                reply_markup=get_main_menu()
            )
    elif context.user_data.get('awaiting_event_selection'):
        # Пользователь выбрал событие для отображения времени
        if text in user_dates.get(user_id, {}):
            event_date = datetime.strptime(user_dates[user_id][text], '%Y-%m-%d')
            now = datetime.now()
            delta = event_date - now

            if delta.days < 0:
                await update.message.reply_text(f"Событие '{text}' уже прошло.")
            else:
                years = delta.days // 365
                months = (delta.days % 365) // 30
                days = (delta.days % 365) % 30
                await update.message.reply_text(
                    f"До события '{text}' осталось: {years} лет, {months} месяцев и {days} дней.",
                    reply_markup=get_main_menu()
                )
            context.user_data['awaiting_event_selection'] = False
        else:
            await update.message.reply_text("Событие не найдено. Пожалуйста, выберите событие ещё раз.")
    elif text == 'Добавить дату':
        await update.message.reply_text(
            "Введите название для новой даты:",
            reply_markup=ReplyKeyboardMarkup([['Отмена']], resize_keyboard=True)
        )
        context.user_data['adding_date'] = True
    elif context.user_data.get('adding_date'):
        # Пользователь ввел название события
        context.user_data['event_name'] = text
        await update.message.reply_text(
            "Теперь введите дату в формате ДД.ММ.ГГГГ:",
            reply_markup=ReplyKeyboardMarkup([['Отмена']], resize_keyboard=True)
        )
        context.user_data['adding_date'] = False
        context.user_data['adding_event_date'] = True
    elif context.user_data.get('adding_event_date'):
        # Пользователь ввел дату события
        try:
            user_date = datetime.strptime(text, '%d.%m.%Y')
            if user_id not in user_dates or not isinstance(user_dates[user_id], dict):
                user_dates[user_id] = {}  # Убедимся, что создается словарь для пользователя
            user_dates[user_id][context.user_data['event_name']] = user_date.strftime('%Y-%m-%d')
            save_user_dates(user_dates)  # Сохраняем дату в файл
            await update.message.reply_text(
                f"Дата '{context.user_data['event_name']}' сохранена.",
                reply_markup=get_main_menu()
            )
            context.user_data['adding_event_date'] = False
        except ValueError:
            await update.message.reply_text("Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")
    elif text == 'Изменить дату':
        if user_id in user_dates and isinstance(user_dates[user_id], dict) and user_dates[user_id]:
            # Если у пользователя есть сохраненные даты, показываем их для выбора
            date_names = list(user_dates[user_id].keys())
            keyboard = [[name] for name in date_names] + [['Отмена']]
            await update.message.reply_text(
                "Выберите событие, чтобы изменить его дату:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            context.user_data['changing_date'] = True
        else:
            await update.message.reply_text(
                "У вас нет сохранённых дат. Выберите 'Добавить дату', чтобы добавить.",
                reply_markup=get_main_menu()
            )
    elif context.user_data.get('changing_date'):
        if text in user_dates.get(user_id, {}):
            context.user_data['event_name'] = text
            await update.message.reply_text(
                "Введите новую дату в формате ДД.ММ.ГГГГ:",
                reply_markup=ReplyKeyboardMarkup([['Отмена']], resize_keyboard=True)
            )
            context.user_data['changing_date'] = False
            context.user_data['changing_event_date'] = True
        else:
            await update.message.reply_text("Событие не найдено.")
    elif context.user_data.get('changing_event_date'):
        try:
            user_date = datetime.strptime(text, '%d.%m.%Y')
            user_dates[user_id][context.user_data['event_name']] = user_date.strftime('%Y-%m-%d')
            save_user_dates(user_dates)  # Сохраняем дату в файл
            await update.message.reply_text(
                f"Дата для события '{context.user_data['event_name']}' изменена.",
                reply_markup=get_main_menu()
            )
            context.user_data['changing_event_date'] = False
        except ValueError:
            await update.message.reply_text("Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")
    elif text == 'Удалить дату':
        if user_id in user_dates and isinstance(user_dates[user_id], dict) and user_dates[user_id]:
            # Если у пользователя есть сохраненные даты, показываем их для удаления
            date_names = list(user_dates[user_id].keys())
            keyboard = [[name] for name in date_names] + [['Отмена']]
            await update.message.reply_text(
                "Выберите событие, чтобы удалить его:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            context.user_data['deleting_date'] = True
        else:
            await update.message.reply_text(
                "У вас нет сохранённых дат. Выберите 'Добавить дату', чтобы добавить.",
                reply_markup=get_main_menu()
            )
    elif context.user_data.get('deleting_date'):
        if text in user_dates.get(user_id, {}):
            del user_dates[user_id][text]
            save_user_dates(user_dates)  # Сохраняем изменения
            await update.message.reply_text(
                f"Событие '{text}' удалено.",
                reply_markup=get_main_menu()
            )
            context.user_data['deleting_date'] = False
        else:
            await update.message.reply_text("Событие не найдено.")
    elif text == 'Отмена':
        await update.message.reply_text(
            "Действие отменено. Возвращаюсь в меню.",
            reply_markup=get_main_menu()
        )
        context.user_data.clear()

# Основная функция запуска бота
def main():
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем хэндлеры команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем получение обновлений
    application.run_polling()

if __name__ == '__main__':
    main()
