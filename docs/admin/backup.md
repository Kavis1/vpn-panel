# Резервное копирование и восстановление

## Обзор резервного копирования

Система резервного копирования VPN Panel позволяет защитить ваши данные от потери в случае сбоев оборудования, человеческих ошибок или кибератак. Рекомендуется настроить автоматическое резервное копирование следующих компонентов:

- **Конфигурация системы**
- **База данных**
- **Файлы приложения**
- **Сертификаты и ключи**
- **Пользовательские данные**

## Стратегия резервного копирования

### 1. Ежедневные полные резервные копии
- Хранение: 7 дней
- Время: 2:00 ночи
- Сжатие: GZIP

### 2. Еженедельные полные резервные копии
- Хранение: 4 недели
- День: Воскресенье
- Время: 3:00 ночи

### 3. Ежемесячные полные резервные копии
- Хранение: 12 месяцев
- День: Первое число месяца
- Время: 4:00 ночи

## Настройка резервного копирования

### Автоматическое резервное копирование

1. **Создайте скрипт резервного копирования** (`/usr/local/bin/backup-vpn-panel.sh`):

```bash
#!/bin/bash

# Конфигурация
BACKUP_DIR="/var/backups/vpn-panel"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7

# Создаем директорию для бэкапов
mkdir -p "$BACKUP_DIR"

# Останавливаем сервисы
systemctl stop vpn-panel

# Бэкап базы данных PostgreSQL
PGPASSWORD=$DB_PASSWORD pg_dump -U $DB_USER -h $DB_HOST -d $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

# Бэкап конфигурации и сертификатов
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /etc/vpn-panel /etc/xray

# Бэкап пользовательских данных
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" /var/lib/vpn-panel

# Запускаем сервисы обратно
systemctl start vpn-panel

# Удаляем старые бэкапы
find "$BACKUP_DIR" -type f -mtime +$KEEP_DAYS -delete

# Проверяем успешность выполнения
if [ $? -eq 0 ]; then
    echo "Резервное копирование успешно завершено: $DATE" | mail -s "Успешное резервное копирование VPN Panel" admin@example.com
else
    echo "Ошибка при создании резервной копии: $DATE" | mail -s "Ошибка резервного копирования VPN Panel" admin@example.com
fi
```

2. **Сделайте скрипт исполняемым**:
```bash
chmod +x /usr/local/bin/backup-vpn-panel.sh
```

3. **Добавьте задание в cron**:
```
# Ежедневное резервное копирование в 2:00
0 2 * * * /usr/local/bin/backup-vpn-panel.sh
```

## Восстановление из резервной копии

### Восстановление базы данных

1. Остановите сервисы:
```bash
systemctl stop vpn-panel
```

2. Восстановите базу данных:
```bash
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $DB_HOST -d $DB_NAME < /path/to/backup/db_YYYYMMDD_HHMMSS.sql
```

3. Восстановите конфигурацию и сертификаты:
```bash
tar -xzf /path/to/backup/config_YYYYMMDD_HHMMSS.tar.gz -C /
```

4. Восстановите пользовательские данные:
```bash
tar -xzf /path/to/backup/data_YYYYMMDD_HHMMSS.tar.gz -C /
```

5. Перезапустите сервисы:
```bash
systemctl start vpn-panel
```

## Проверка резервных копий

Рекомендуется регулярно проверять целостность резервных копий:

1. **Проверка целостности архива**:
```bash
tar -tzf /path/to/backup/config_YYYYMMDD_HHMMSS.tar.gz
```

2. **Проверка дампа базы данных**:
```bash
pg_restore -l /path/to/backup/db_YYYYMMDD_HHMMSS.dump
```

## Ротация логов

Настройте logrotate для управления логами:

```
/var/log/vpn-panel/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 vpn-panel vpn-panel
    sharedscripts
    postrotate
        systemctl reload vpn-panel > /dev/null 2>&1 || true
    endscript
}
```

## Аварийное восстановление

### Минимальный набор для восстановления:
1. Ключи шифрования
2. Сертификаты TLS/SSL
3. Конфигурация Xray
4. База данных пользователей

### Процедура аварийного восстановления:

1. **Разверните чистую ОС** с теми же характеристиками
2. **Установите VPN Panel** по инструкции
3. **Восстановите данные** из резервной копии
4. **Проверьте работоспособность** всех сервисов
5. **Обновите DNS-записи** при необходимости

## Автоматизация мониторинга бэкапов

Добавьте в систему мониторинга проверки:

1. **Проверка свежести бэкапов**
2. **Проверка размера бэкапов**
3. **Проверка целостности**
4. **Оповещения о проблемах**

### Пример скрипта проверки:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/vpn-panel"
MAX_AGE_HOURS=26  # Максимальный возраст бэкапа в часах
MIN_SIZE_MB=10    # Минимальный размер бэкапа в МБ

# Проверяем наличие свежих бэкапов
if ! find "$BACKUP_DIR" -name "db_*.sql" -mmin -$((MAX_AGE_HOURS * 60)) | read; then
    echo "CRITICAL: Нет свежих бэкапов базы данных!" >&2
    exit 2
fi

# Проверяем размер бэкапов
for file in "$BACKUP_DIR"/*.tar.gz "$BACKUP_DIR"/*.sql; do
    if [ -f "$file" ]; then
        size_mb=$(du -m "$file" | cut -f1)
        if [ "$size_mb" -lt "$MIN_SIZE_MB" ]; then
            echo "WARNING: Слишком маленький файл бэкапа: $file (${size_mb}M)" >&2
            exit 1
        fi
    fi
done

echo "OK: Все бэкапы в порядке"
exit 0
```

## Рекомендации по безопасности

1. **Шифрование бэкапов**:
   ```bash
   # Шифрование
   gpg --symmetric --cipher-algo AES256 -o backup_$(date +%Y%m%d).tar.gz.gpg backup.tar.gz
   
   # Дешифровка
   gpg -d -o backup.tar.gz backup_$(date +%Y%m%d).tar.gz.gpg
   ```

2. **Хранение за пределами сервера**:
   - Облачное хранилище (S3, Google Cloud Storage)
   - Другой сервер
   - Внешний накопитель

3. **Проверка прав доступа**:
   ```bash
   chmod 600 /var/backups/vpn-panel/*
   chown root:root /var/backups/vpn-panel/*
   ```
