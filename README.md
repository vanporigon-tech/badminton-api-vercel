# 🏸 Badminton Rating System

Система рейтинга для бадминтона с Telegram Mini App и GitHub Pages API.

## 🚀 Деплой

### GitHub Pages
1. Загрузите все файлы в репозиторий
2. Включите GitHub Pages в настройках репозитория
3. Выберите источник: Deploy from a branch
4. Выберите ветку: main
5. Выберите папку: / (root)

### Структура API
- `api/rooms.json` - статические комнаты
- `api/tournament/start.json` - начало турнира
- `api/tournament/end.json` - завершение турнира
- `api/tournament/1.json` - данные турнира

## 🔧 Локальная разработка

### Запуск API
```bash
uvicorn main:app --reload --port 8000
```

### Запуск фронтенда
```bash
cd badminton-rating-app
python3 -m http.server 8080
```

## 📱 Использование

1. Откройте мини-приложение в Telegram
2. Создайте комнату или присоединитесь к существующей
3. Играйте и отслеживайте рейтинг!

## 🌐 URL

- **GitHub Pages**: https://vanporigon-tech.github.io/badminton-api-vercel
- **Локально фронтенд**: http://localhost:8080
- **Локально API**: http://localhost:8000

В Mini App/браузере можно задать адрес API кнопкой (в диалоге prompt) или через localStorage ключ `API_BASE_URL`.

## 📊 Особенности

- ✅ Синхронизация комнат между пользователями
- ✅ Система рейтинга Glicko-2
- ✅ Локальное хранение данных
- ✅ Статические API файлы для GitHub Pages
- ✅ Telegram Mini App интеграция