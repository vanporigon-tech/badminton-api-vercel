#!/usr/bin/env python3
"""
Простая версия Telegram бота для тестирования
"""

import asyncio
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        [{
            "text": "🏸 Открыть Badminton Rating",
            "web_app": {"url": "http://localhost:8000/app"}
        }]
    ]
    
    await update.message.reply_text(
        welcome_text,
        reply_markup={"inline_keyboard": keyboard}
    )
    
    logger.info(f"Пользователь {user.id} ({user.first_name}) запустил бота")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    await update.message.reply_text(help_text)

async def rating_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    await update.message.reply_text(rating_text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    await update.message.reply_text(about_text)

async def setup_commands(application: Application) -> None:
    """Настройка команд бота"""
    commands = [
        BotCommand("start", "🏸 Запустить Badminton Rating"),
        BotCommand("help", "🔍 Справка по командам"),
        BotCommand("rating", "🏆 Информация о системе рейтинга"),
        BotCommand("about", "ℹ️ О проекте"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("Команды бота настроены")

async def main() -> None:
    """Главная функция"""
    # Получаем токен из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не установлен в .env файле!")
        return
    
    print("🤖 Запуск Telegram бота...")
    print(f"📱 Токен: {token[:20]}...")
    print("🌐 Mini App URL: http://localhost:8000/app")
    print("=" * 50)
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Настраиваем команды
    await setup_commands(application)
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rating", rating_info))
    application.add_handler(CommandHandler("about", about))
    
    print("✅ Бот успешно запущен!")
    print("📱 Отправьте /start в Telegram боту @GoBadmikAppBot")
    print("=" * 50)
    
    # Запускаем бота
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

