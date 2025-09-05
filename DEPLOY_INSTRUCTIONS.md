# 🚀 Инструкция по деплою API на Vercel

## 📋 Что нужно сделать:

### 1. Зайти на https://vercel.com
- Войти в аккаунт GitHub
- Нажать "New Project"
- Выбрать репозиторий `vanporigon-tech/badminton-api-vercel`

### 2. Настройки проекта:
- **Framework Preset**: Other
- **Root Directory**: `/` (корень)
- **Build Command**: оставить пустым
- **Output Directory**: оставить пустым

### 3. Environment Variables:
- Никаких переменных окружения не нужно

### 4. Деплой:
- Нажать "Deploy"
- Дождаться завершения (2-3 минуты)

### 5. Получить URL:
- После деплоя получишь URL типа: `https://badminton-api-vercel-xxx.vercel.app`
- Обновить этот URL в файлах:
  - `bot_simple_api.py` (заменить `https://badminton-api-vercel.vercel.app`)
  - `badminton-rating-app/index.html` (заменить в строке 597)

## 🔧 Альтернативный способ (через GitHub):

1. Зайти на https://vercel.com
2. Нажать "Import Project"
3. Выбрать "Import Git Repository"
4. Ввести: `vanporigon-tech/badminton-api-vercel`
5. Нажать "Import"
6. Нажать "Deploy"

## ✅ После деплоя:

1. API будет доступен по URL: `https://your-project.vercel.app`
2. Все команды бота будут работать
3. Мини-приложение будет работать с облачным API
4. Система турниров будет работать 24/7

## 🎯 Тестирование:

1. Отправить боту `/start_tournament`
2. Отправить боту `/end_tournament`
3. Проверить, что мини-приложение работает
4. Проверить, что создаются Google Таблицы

## 📱 Финальные URL:

- **API**: `https://your-project.vercel.app`
- **Мини-приложение**: `https://vanporigon-tech.github.io/badminton-rating-app`
- **Бот**: `@GoBadmikAppBot`
