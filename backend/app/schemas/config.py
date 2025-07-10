"""
Pydantic-схемы для управления конфигурацией Xray.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator, HttpUrl

class ConfigStatus(str, Enum):
    """Статус конфигурации."""
    DRAFT = "draft"          # Черновик
    ACTIVE = "active"        # Активна
    DEPRECATED = "deprecated"  # Устарела
    ARCHIVED = "archived"    # Архивирована

class ConfigBase(BaseModel):
    """Базовая схема конфигурации."""
    version: str = Field(..., max_length=50, description="Версия конфигурации")
    description: Optional[str] = Field(None, description="Описание изменений")
    config: Dict[str, Any] = Field(..., description="Конфигурация в формате JSON")
    status: ConfigStatus = Field(default=ConfigStatus.DRAFT, description="Статус конфигурации")
    is_default: bool = Field(default=False, description="Является ли конфигурация конфигурацией по умолчанию")

class ConfigCreate(ConfigBase):
    """Схема для создания конфигурации."""
    pass

class ConfigUpdate(BaseModel):
    """Схема для обновления конфигурации."""
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[ConfigStatus] = None
    is_default: Optional[bool] = None

class ConfigInDBBase(ConfigBase):
    """Базовая схема конфигурации в БД."""
    id: int
    checksum: str
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class Config(ConfigInDBBase):
    """Схема для возврата данных о конфигурации."""
    pass

class ConfigInDB(ConfigInDBBase):
    """Схема для конфигурации в БД."""
    pass

class ConfigList(BaseModel):
    """Схема для списка конфигураций с пагинацией."""
    items: List[Config] = []
    total: int = 0
    page: int = 1
    size: int = 50
    pages: int = 1

class ConfigSyncStatus(str, Enum):
    """Статус синхронизации конфигурации."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    OUTDATED = "outdated"

class NodeSyncStatus(BaseModel):
    """Статус синхронизации конфигурации на ноде."""
    node_id: int
    node_name: str
    status: ConfigSyncStatus
    last_sync: Optional[datetime] = None
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    is_online: bool = False
    node_status: Optional[str] = None

class ConfigSyncResponse(BaseModel):
    """Ответ о статусе синхронизации конфигурации."""
    config_id: int
    config_version: str
    status: ConfigSyncStatus
    nodes: List[NodeSyncStatus] = []
    created_at: datetime
    updated_at: datetime

class ConfigDiff(BaseModel):
    """Различия между версиями конфигурации."""
    added: Dict[str, Any] = {}
    removed: Dict[str, Any] = {}
    changed: Dict[str, Any] = {}

class ConfigDiffResponse(BaseModel):
    """Ответ с различиями между версиями конфигурации."""
    from_version: str
    to_version: str
    diff: ConfigDiff

class ConfigTemplate(BaseModel):
    """Шаблон конфигурации Xray."""
    name: str = Field(..., description="Название шаблона")
    description: Optional[str] = Field(None, description="Описание шаблона")
    template: Dict[str, Any] = Field(..., description="Шаблон конфигурации")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Переменные шаблона")

class ConfigValidationError(BaseModel):
    """Ошибка валидации конфигурации."""
    field: str
    message: str
    error_type: str

class ConfigValidationResponse(BaseModel):
    """Ответ с результатами валидации конфигурации."""
    is_valid: bool
    errors: List[ConfigValidationError] = []
    warnings: List[ConfigValidationError] = []

class ConfigDeployRequest(BaseModel):
    """Запрос на развертывание конфигурации."""
    version: str
    nodes: Optional[List[int]] = None  # Если None, развертываем на всех нодах
    force: bool = False  # Принудительное развертывание, даже если версия совпадает
    restart_services: bool = True  # Перезапускать ли сервисы после развертывания

class ConfigDeployResponse(BaseModel):
    """Ответ на запрос развертывания конфигурации."""
    job_id: str
    status: str
    message: str
    started_at: datetime

class ConfigRollbackRequest(BaseModel):
    """Запрос на откат конфигурации."""
    version: str  # Версия, на которую нужно откатиться
    nodes: Optional[List[int]] = None  # Если None, откатываем на всех нодах
    force: bool = False  # Принудительный откат

class ConfigRollbackResponse(BaseModel):
    """Ответ на запрос отката конфигурации."""
    job_id: str
    status: str
    message: str
    started_at: datetime

class ConfigTemplateList(BaseModel):
    """Список шаблонов конфигурации."""
    templates: List[ConfigTemplate]
    total: int

class ConfigTemplateCreate(ConfigTemplate):
    """Схема для создания шаблона конфигурации."""
    pass

class ConfigTemplateUpdate(BaseModel):
    """Схема для обновления шаблона конфигурации."""
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None

class ConfigTemplateResponse(ConfigTemplate):
    """Ответ с данными шаблона конфигурации."""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True
