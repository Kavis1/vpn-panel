# Установка VPN Panel с помощью Docker

## Требования

- Linux-сервер с Docker и Docker Compose
- Минимум 2 ГБ оперативной памяти
- Минимум 20 ГБ свободного места на диске
- Открытые порты: 80, 443, 8000, 10085

## Быстрый старт

1. Установите Docker и Docker Compose, если они еще не установлены:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Установка Docker Compose
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

2. Выполните команду для автоматической установки:

```bash
curl -s https://raw.githubusercontent.com/yourusername/vpn-panel/main/deploy/install_docker.sh | sudo bash
```

Или вручную:

```bash
# Клонируйте репозиторий
cd /opt
git clone https://github.com/yourusername/vpn-panel.git
cd vpn-panel

# Создайте и настройте .env файл
cp .env.example .env
nano .env  # Отредактируйте настройки

# Запустите приложение
docker-compose up -d --build
```

## Доступ к панели

После успешной установки откройте в браузере:

```
http://ваш-ip-адрес:8000
```

Или с настройкой домена и HTTPS:
```
https://ваш-домен
```

## Учетные данные по умолчанию

- **Логин:** admin
- **Пароль:** сгенерирован случайным образом (проверьте вывод скрипта или файл /etc/vpn-panel/credentials)

## Управление сервисами

- **Запуск:** `docker-compose up -d`
- **Остановка:** `docker-compose down`
- **Просмотр логов:** `docker-compose logs -f`
- **Обновление:**
  ```bash
  git pull origin main
  docker-compose build --no-cache
  docker-compose down
  docker-compose up -d
  ```

## Резервное копирование

Резервные копии базы данных и конфигураций сохраняются в директории `./backups`.

## Устранение неполадок

1. **Проверьте статус контейнеров:**
   ```bash
   docker-compose ps
   ```

2. **Просмотрите логи:**
   ```bash
   docker-compose logs -f
   ```

3. **Проверьте настройки брандмауэра:**
   ```bash
   # Для UFW
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 8000/tcp
   sudo ufw allow 10085/tcp
   ```

## Обновление

```bash
cd /opt/vpn-panel
git pull
docker-compose down
docker-compose pull
docker-compose up -d --build
```

## Удаление

```bash
cd /opt/vpn-panel
docker-compose down -v
sudo rm -rf /opt/vpn-panel /etc/vpn-panel
```

## Безопасность

- По умолчанию включен HTTPS с автоматическим получением сертификатов Let's Encrypt
- Все пароли генерируются случайным образом
- Рекомендуется изменить пароль администратора после первого входа
- Не забудьте настроить брандмауэр для ограничения доступа к портам

## Поддержка

По вопросам установки и настройки обращайтесь в [Issues](https://github.com/yourusername/vpn-panel/issues).
