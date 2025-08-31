#!/usr/bin/env python3
"""
Telegram бот для Badminton Rating с использованием legacy API
"""

import logging
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
🏸 Привет, {user.first_name}!

Добро пожаловать в Badminton Rating Mini App!

Это приложение поможет вам:
• Создавать и присоединяться к играм в бадминтон
• Отслеживать свой рейтинг по системе Glicko-2
• Играть в командах и индивидуально
• Автоматически рассчитывать рейтинг после каждой игры

Нажмите кнопку ниже, чтобы открыть Mini App:
"""
    
    # Создаем кнопку для открытия Mini App
    keyboard = [
        [InlineKeyboardButton("🏸 Открыть Badminton Rating", web_app={"url": "http://localhost:8000/app"})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup)
    logger.info(f"Пользователь {user.id} ({user.first_name}) запустил бота")

def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help"""
    help_text = """
🔍 Доступные команды:

/start - Запустить Mini App
/help - Показать эту справку
/rating - Информация о системе рейтинга
/about - О проекте

📱 Mini App функции:
• Регистрация игрока
• Создание и поиск игр
• Присоединение к комнатам
• Автоматический расчет рейтинга Glicko-2
• Поддержка командной игры (2v2, 1v1)
"""
    
    update.message.reply_text(help_text)

def rating_info(update: Update, context: CallbackContext) -> None:
    """Информация о системе рейтинга"""
    rating_text = """
🏆 Система рейтинга Glicko-2

Это современная и точная система расчета рейтинга, которая:

📊 Учитывает:
• Текущий рейтинг игрока
• Неопределенность рейтинга (RD)
• Волатильность игрока
• Силу противников

🎯 Особенности:
• Быстрая адаптация к изменениям уровня
• Справедливая оценка для новых игроков
• Учет командной игры
• Автоматический расчет после каждой игры
"""
    
    update.message.reply_text(rating_text)

def about(update: Update, context: CallbackContext) -> None:
    """О проекте"""
    about_text = """
🏸 Badminton Rating Mini App

📱 Что это:
Telegram Mini App для расчета рейтинга в бадминтоне с использованием системы Glicko-2.

🛠️ Технологии:
• Backend: Python + FastAPI
• База данных: SQLite (для тестирования)
• Frontend: HTML + CSS + JavaScript
• Система рейтинга: Glicko-2
• Интеграция: Telegram Bot API

🎯 Возможности:
• Регистрация игроков
• Создание и поиск игр
• Командная игра (1v1, 2v2)
• Автоматический расчет рейтинга
• Красивый интерфейс
• Работа прямо в Telegram
"""
    
    update.message.reply_text(about_text)

def error_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}")
    if update and update.message:
        update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
        )

def main() -> None:
    """Главная функция"""
    # Получаем токен из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не установлен в .env файле!")
        return
    
    print("🤖 Запуск Telegram бота (Legacy API)...")
    print(f"📱 Токен: {token[:20]}...")
    print("🌐 Mini App URL: http://localhost:8000/app")
    print("=" * 50)
    
    try:
        # Создаем updater
        updater = Updater(token)
        
        # Получаем dispatcher для регистрации обработчиков
        dispatcher = updater.dispatcher
        
        # Добавляем обработчики
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("rating", rating_info))
        dispatcher.add_handler(CommandHandler("about", about))
        
        # Добавляем обработчик ошибок
        dispatcher.add_error_handler(error_handler)
        
        print("✅ Бот успешно запущен!")
        print("📱 Отправьте /start в Telegram боту @GoBadmikAppBot")
        print("=" * 50)
        
        # Запускаем бота
        updater.start_polling()
        
        # Ждем завершения
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        print(f"❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

