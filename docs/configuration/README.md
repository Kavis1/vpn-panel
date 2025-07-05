# Настройка конфигурации

В этом разделе описаны все доступные настройки конфигурации VPN Panel.

## Файл .env

Основные настройки приложения задаются в файле `.env`. Пример файла `.env.example`:

```ini
# Основные настройки
APP_ENV=production
DEBUG=false
SECRET_KEY=ваш_секретный_ключ

# Настройки базы данных
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vpn_panel
DB_USER=postgres
DB_PASSWORD=ваш_пароль

# Настройки API
API_PREFIX=/api/v1
JWT_SECRET=ваш_jwt_секрет
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Настройки почты
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=ваш_пароль
EMAIL_FROM=no-reply@example.com

# Настройки Xray
XRAY_API_HOST=127.0.0.1
XRAY_API_PORT=10085
XRAY_EXECUTABLE=/usr/local/bin/xray

# Настройки безопасности
ALLOWED_HOSTS=*
CORS_ORIGINS=["*"]
RATE_LIMIT=100/1 minute

# Настройки HWID
HWID_DEVICE_LIMIT_ENABLED=true
HWID_FALLBACK_DEVICE_LIMIT=3
```

## Обязательные настройки

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `SECRET_KEY` | Секретный ключ приложения | - |
| `DB_HOST` | Хост базы данных | localhost |
| `DB_NAME` | Имя базы данных | vpn_panel |
| `DB_USER` | Пользователь БД | - |
| `DB_PASSWORD` | Пароль БД | - |

## Рекомендуемые настройки безопасности

1. **В продакшене** установите `DEBUG=false`
2. Используйте сложный `SECRET_KEY`
3. Ограничьте `ALLOWED_HOSTS` и `CORS_ORIGINS`
4. Включите HTTPS
5. Ограничьте доступ к API по IP

## Перезагрузка конфигурации

После изменения настроек перезапустите сервис:

```bash
sudo systemctl restart vpn-panel
```

## Проверка конфигурации

Проверить текущую конфигурацию можно командой:

```bash
python -c "from app.config import settings; print(settings)"
```

## Переопределение настроек

Вы можете переопределить любую настройку, указав соответствующую переменную окружения с префиксом `VPN_`. Например:

```bash
export VPN_DB_HOST=db.example.com
export VPN_DEBUG=true
```
