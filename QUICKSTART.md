# 🚀 Быстрый запуск Badminton Rating Mini App

## 📋 Что нужно сделать за 5 минут

### 1. Установка зависимостей
```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка базы данных PostgreSQL
```bash
# Установите PostgreSQL (если еще не установлен)
brew install postgresql  # macOS
brew services start postgresql

# Создайте пользователя и базу данных
sudo -u postgres psql
CREATE USER badminton_user WITH PASSWORD 'your_password';
CREATE DATABASE badminton_rating OWNER badminton_user;
GRANT ALL PRIVILEGES ON DATABASE badminton_rating TO badminton_user;
\q
```

### 3. Создайте файл .env
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=badminton_rating
DB_USER=badminton_user
DB_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_USERNAME=your_bot_username
SECRET_KEY=your_secret_key_here
DEBUG=True
```

### 4. Настройка базы данных
```bash
python setup_database.py
```

### 5. Запуск приложения
```bash
python run.py
```

## 🌐 Доступ к приложению

- **API**: http://localhost:8000
- **Mini App**: http://localhost:8000/app
- **Документация API**: http://localhost:8000/docs

## 🧪 Тестирование

```bash
# Тест API
python test_app.py

# Демонстрация Glicko-2
python demo_glicko2.py
```

## 📱 Настройка Telegram Bot

1. Найдите @BotFather в Telegram
2. Создайте бота: `/newbot`
3. Настройте Menu Button: `/mybots` → Bot Settings → Menu Button
4. Укажите URL: `https://your-domain.com/app`

## 🎯 Основные функции

- ✅ Регистрация игроков
- ✅ Создание/поиск комнат
- ✅ Присоединение к играм
- ✅ Автоматический расчет рейтинга Glicko-2
- ✅ Поддержка 1v1 и 2v2 игр
- ✅ Красивый интерфейс в вашей цветовой схеме

## 🆘 Если что-то не работает

1. **Проверьте PostgreSQL**: `brew services list | grep postgresql`
2. **Проверьте переменные окружения**: `echo $DB_HOST`
3. **Пересоздайте базу**: `python setup_database.py`
4. **Проверьте логи**: `tail -f logs/app.log`

## 🚀 Готово!

Ваш Badminton Rating Mini App готов к работе! 🏸

---

**Нужна помощь?** Смотрите подробную документацию в `README.md`

