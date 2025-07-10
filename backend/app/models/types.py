"""
Кастомные типы данных для SQLAlchemy моделей.
"""
import uuid
import ipaddress
from sqlalchemy.types import TypeDecorator, CHAR, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, INET as PostgresINET


class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Использует PostgreSQL UUID для PostgreSQL и CHAR(36) для SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class INET(TypeDecorator):
    """Platform-independent INET type.

    Использует PostgreSQL INET для PostgreSQL и String для SQLite.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresINET())
        else:
            return dialect.type_descriptor(String(45))  # Достаточно для IPv6

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        try:
            return ipaddress.ip_address(value)
        except ValueError:
            # Если не удается распарсить как IP, возвращаем строку
            return value
