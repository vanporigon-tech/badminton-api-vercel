#!/usr/bin/env python3
"""
Простой Telegram бот для тестирования Badminton Rating Mini App
"""

import asyncio
import logging
from telegram import Update, BotCommand, WebAppInfo, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
import httpx
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Локальная карта соответствия ранга стартовому рейтингу
RANK_TO_RATING = {
    "G": 600,
    "F": 700,
    "E": 800,
    "D": 900,
    "C": 1100,
    "B": 1400,
    "A": 1700,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
🏸 Привет, {user.first_name}!

Добро пожаловать в Badminton Rating Mini App!

Это приложение поможет вам:
• Создавать и присоединяться к играм в бадминтон
• Отслеживать свой рейтинг
• Играть в командах и индивидуально
• Автоматически рассчитывать рейтинг после каждой игры

Нажмите кнопку ниже, чтобы открыть Mini App:
"""
    
    # Кнопка для открытия Mini App через InlineKeyboardButton + web_app
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🏸 Открыть Badminton Rating", web_app=WebAppInfo(url=settings.MINI_APP_URL))]
    ])

    await update.message.reply_text(welcome_text, reply_markup=keyboard)
    
    logger.info(f"Пользователь {user.id} ({user.first_name}) запустил бота")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    base_text = """
🔍 Доступные команды:

/start - Запустить Mini App
/help - Показать эту справку
/rating - Информация о системе рейтинга
/about - О проекте
/whoami - Мой ID и рейтинг
"""
    admin_text = """

Админ-команды (только в личке):
/tstart [название] — начать турнир (по умолчанию: сегодняшняя дата)
/tend [id] — завершить турнир (без id — последний активный)
/treport <id> — показать отчёт по турниру
"""
    tail_text = """

📱 Mini App функции:
• Регистрация игрока
• Создание и поиск игр
• Присоединение к комнатам
• Автоматический расчет рейтинга
• Поддержка командной игры (2v2, 1v1)

🏸 Система рейтинга:
• F (ниже 500) - Начинающий
• E (500-799) - Любитель  
• D (800-1099) - Продвинутый
• C (1100-1399) - Опытный
• B (1400-1699) - Мастер
• A (1700+) - Эксперт
"""

    chat = update.effective_chat
    is_admin = _is_admin(update.effective_user.id)
    help_text = base_text + (admin_text if is_admin and chat.type == "private" else "") + tail_text
    
    await update.message.reply_text(help_text)
    logger.info(f"Пользователь {update.effective_user.id} запросил справку")

async def rating_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Информация о системе рейтинга"""
    rating_text = """
🏆 Система рейтинга

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
Telegram Mini App для расчета рейтинга в бадминтоне.

🎯 Возможности:
• Регистрация игроков
• Создание и поиск игр
• Командная игра (1v1, 2v2)
• Автоматический расчет рейтинга
• Удобный интерфейс прямо в Telegram
"""
    
    await update.message.reply_text(about_text)
    logger.info(f"Пользователь {update.effective_user.id} запросил информацию о проекте")

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tid = update.effective_user.id
    uname = update.effective_user.username or "-"
    fn = update.effective_user.first_name or ""
    ln = update.effective_user.last_name or ""
    api_line = ""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{settings.API_BASE_URL}/players/{tid}")
            if r.status_code == 200:
                pj = r.json()
                api_line = f"\nAPI: rating={pj.get('rating')} rank={pj.get('initial_rank')} games={pj.get('games_count')}"
            else:
                api_line = f"\nAPI: not found ({r.status_code})"
    except Exception as e:
        api_line = f"\nAPI error: {e}"
    await update.message.reply_text(
        f"ID: {tid}\nUsername: @{uname}\nName: {fn} {ln}{api_line}"
    )

def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

async def tstart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat = update.effective_chat
    if not _is_admin(user_id) or chat.type != "private":
        return
    name = " ".join(context.args) if context.args else datetime.now().strftime("%Y-%m-%d")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{settings.API_BASE_URL}/tournaments/start", json={"name": name})
            if resp.status_code != 200:
                text = resp.text
                try:
                    j = resp.json()
                    text = j.get("detail") or j
                except Exception:
                    pass
                await update.message.reply_text(f"Ошибка запуска турнира: {resp.status_code} {text}")
                return
            data = resp.json()
            tid = data.get("id") or data.get("tournament_id")
            await update.message.reply_text(f"🏁 Турнир #{tid} начат — {name}")
    except httpx.RequestError as e:
        await update.message.reply_text(f"Ошибка сети: {e.__class__.__name__}: {e}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e.__class__.__name__}: {e}")

async def tend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat = update.effective_chat
    if not _is_admin(user_id) or chat.type != "private":
        return
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            if context.args:
                tid = int(context.args[0])
                resp = await client.post(f"{settings.API_BASE_URL}/tournaments/{tid}/end")
                if resp.status_code != 200:
                    await update.message.reply_text(f"Ошибка завершения турнира: {resp.status_code} {resp.text}")
                    return
                ended = resp.json()
                tid = ended.get("tournament_id") or tid
            else:
                resp = await client.post(f"{settings.API_BASE_URL}/tournaments/end_latest")
                if resp.status_code != 200:
                    await update.message.reply_text(f"Ошибка завершения турнира: {resp.status_code} {resp.text}")
                    return
                ended = resp.json()
                tid = ended.get("tournament_id")

            # Получить отчёт
            report_resp = await client.get(f"{settings.API_BASE_URL}/tournaments/{tid}/report")
            if report_resp.status_code == 200:
                report = report_resp.json().get("report", "")
                await update.message.reply_text(report[:4000])
            else:
                await update.message.reply_text(f"Турнир #{tid} завершён. Отчёт недоступен.")
    except httpx.RequestError as e:
        await update.message.reply_text(f"Ошибка сети: {e.__class__.__name__}: {e}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e.__class__.__name__}: {e}")

async def treport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat = update.effective_chat
    if not _is_admin(user_id) or chat.type != "private":
        return
    if not context.args:
        await update.message.reply_text("Укажите id турнира: /treport <id>")
        return
    try:
        tid = int(context.args[0])
        async with httpx.AsyncClient(timeout=10.0) as client:
            report_resp = await client.get(f"{settings.API_BASE_URL}/tournaments/{tid}/report")
            if report_resp.status_code == 200:
                report = report_resp.json().get("report", "")
                await update.message.reply_text(report[:4000])
            else:
                await update.message.reply_text(f"Отчёт недоступен: {report_resp.text}")
    except httpx.RequestError as e:
        await update.message.reply_text(f"Ошибка сети: {e.__class__.__name__}: {e}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e.__class__.__name__}: {e}")

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
    base_commands = [
        BotCommand("start", "🏸 Запустить Badminton Rating"),
        BotCommand("help", "🔍 Справка по командам"),
        BotCommand("rating", "🏆 Информация о системе рейтинга"),
        BotCommand("about", "ℹ️ О проекте"),
        BotCommand("whoami", "Мой ID и рейтинг"),
    ]

    # Для всех пользователей в личке — только базовые команды
    await application.bot.set_my_commands(base_commands)

    # Для админов (точечно по chat_id) добавим админ-команды в их личку
    admin_commands = base_commands + [
        BotCommand("tstart", "Начать турнир (admin)"),
        BotCommand("tend", "Завершить турнир (admin)"),
        BotCommand("treport", "Отчёт турнира (admin)"),
    ]
    for admin_id in settings.ADMIN_IDS:
        try:
            await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception:
            continue
    logger.info("Команды бота настроены")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
        )

def main() -> None:
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
    
    # Настраиваем команды после инициализации приложения
    application.post_init = setup_commands
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rating", rating_info))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("whoami", whoami))
    # Admin-only tournament commands
    application.add_handler(CommandHandler("tstart", tstart))
    application.add_handler(CommandHandler("tend", tend))
    application.add_handler(CommandHandler("treport", treport))
    # Убрали /setrank; ввод рейтинга теперь в Mini App
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    # Игнорируем известные команды в "неизвестной" заглушке
    application.add_handler(MessageHandler(
        filters.COMMAND & ~filters.Regex(r"^/(start|help|rating|about|tstart|tend|treport)(\s|$)"),
        help_command
    ))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    print("✅ Бот успешно запущен!")
    print("📱 Отправьте /start в Telegram боту @GoBadmikAppBot")
    print("=" * 50)
    
    # Запускаем бота (блокирующий вызов)
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
