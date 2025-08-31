#!/usr/bin/env python3
"""
Простой Telegram бот для тестирования Badminton Rating Mini App
"""

import asyncio
import logging
from telegram import Update, WebAppInfo, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import settings

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

🏸 Система рейтинга:
• F (ниже 500) - Начинающий
• E (500-799) - Любитель  
• D (800-1099) - Продвинутый
• C (1100-1399) - Опытный
• B (1400-1699) - Мастер
• A (1700+) - Эксперт
"""
    
    await update.message.reply_text(help_text)
    logger.info(f"Пользователь {update.effective_user.id} запросил справку")

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

🔄 Как это работает:
1. Игроки регистрируются с начальным рейтингом
2. После каждой игры система пересчитывает рейтинги
3. Рейтинг растет при победах и падает при поражениях
4. Учитывается сила противников и неожиданность результата

📈 Категории рейтинга:
• F: ниже 500 (начинающий)
• E: 500-799 (любитель)
• D: 800-1099 (продвинутый)
• C: 1100-1399 (опытный)
• B: 1400-1699 (мастер)
• A: 1700+ (эксперт)
"""
    
    await update.message.reply_text(rating_text)
    logger.info(f"Пользователь {update.effective_user.id} запросил информацию о рейтинге")

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

🚀 Разработка:
Создано как профессиональное решение для турниров по бадминтону с современной системой рейтинга.

📊 Glicko-2:
Используется в профессиональном спорте для точного расчета рейтингов игроков.
"""
    
    await update.message.reply_text(about_text)
    logger.info(f"Пользователь {update.effective_user.id} запросил информацию о проекте")

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка данных от Mini App"""
    if update.effective_message.web_app_data:
        data = update.effective_message.web_app_data.data
        logger.info(f"Получены данные от Mini App: {data}")
        
        await update.message.reply_text(
            "📱 Данные получены от Mini App!\n\n"
            "Это означает, что Mini App работает корректно.\n"
            "Вы можете использовать все функции приложения."
        )

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

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
        )

async def main() -> None:
    """Главная функция"""
    # Проверяем токен
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    print("🤖 Запуск Telegram бота...")
    print(f"📱 Токен: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
    print("🌐 Mini App URL: http://localhost:8000/app")
    print("=" * 50)
    
    # Создаем приложение
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Настраиваем команды
    await setup_commands(application)
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rating", rating_info))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    print("✅ Бот успешно запущен!")
    print("📱 Отправьте /start в Telegram боту @GoBadmikAppBot")
    print("=" * 50)
    
    # Запускаем бота
    await application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
