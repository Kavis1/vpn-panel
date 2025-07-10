"""
API для управления конфигурациями Xray и их синхронизацией между нодами.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.api.deps import get_current_active_superuser, get_current_user
from app.core.config import settings
from app.db.session import get_async_db
from app.models.config_version import ConfigVersion
from app.schemas.config import (
    Config, ConfigCreate, ConfigDeployRequest, ConfigDeployResponse,
    ConfigList, ConfigSyncResponse, ConfigTemplate, ConfigUpdate, ConfigValidationResponse,
    ConfigRollbackRequest, ConfigRollbackResponse, NodeSyncStatus, ConfigDiffResponse
)
from app.services.config_sync_service import ConfigSyncService

router = APIRouter()
logger = logging.getLogger(__name__)

# Регистрируем теги для документации API
router.tags = ["config"]

# --- Конфигурации ---

@router.get(
    "/",
    response_model=ConfigList,
    dependencies=[Depends(get_current_user)],
    summary="Получить список конфигураций"
)
async def list_configs(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_default: Optional[bool] = None,
) -> Any:
    """
    Получить список конфигураций с пагинацией.
    """
    # Строим фильтр
    filters = []
    if status:
        filters.append(ConfigVersion.status == status)
    if is_active is not None:
        filters.append(ConfigVersion.is_active.is_(is_active))
    if is_default is not None:
        filters.append(ConfigVersion.is_default.is_(is_default))
    
    # Получаем общее количество конфигураций
    total = await crud.config.count(db, *filters)
    
    # Получаем список конфигураций с пагинацией
    configs = await crud.config.get_multi(
        db,
        skip=skip,
        limit=limit,
        *filters,
        order_by=ConfigVersion.created_at.desc()
    )
    
    return {
        "items": configs,
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@router.get(
    "/active",
    response_model=Config,
    summary="Получить активную конфигурацию"
)
async def get_active_config(
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Получить активную конфигурацию.
    """
    config = await crud.config.get_active_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активная конфигурация не найдена"
        )
    return config

@router.get(
    "/default",
    response_model=Config,
    summary="Получить конфигурацию по умолчанию"
)
async def get_default_config(
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Получить конфигурацию по умолчанию.
    """
    config = await crud.config.get_default_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конфигурация по умолчанию не найдена"
        )
    return config

@router.post(
    "/",
    response_model=Config,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_superuser)],
    summary="Создать новую конфигурацию"
)
async def create_config(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_in: ConfigCreate,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    """
    Создать новую конфигурацию.
    
    Требуются права суперпользователя.
    """
    # Проверяем, существует ли уже конфигурация с такой версией
    existing_config = await crud.config.get_by_version(db, version=config_in.version)
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Конфигурация с версией {config_in.version} уже существует"
        )
    
    # Создаем конфигурацию
    config = await crud.config.create_with_owner(
        db, obj_in=config_in, owner_id=current_user.id
    )
    
    return config

@router.get(
    "/{config_id}",
    response_model=Config,
    dependencies=[Depends(get_current_user)],
    summary="Получить конфигурацию по ID"
)
async def get_config(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_id: int,
) -> Any:
    """
    Получить конфигурацию по ID.
    """
    config = await crud.config.get(db, id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Конфигурация с ID {config_id} не найдена"
        )
    return config

@router.put(
    "/{config_id}",
    response_model=Config,
    dependencies=[Depends(get_current_active_superuser)],
    summary="Обновить конфигурацию"
)
async def update_config(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_id: int,
    config_in: ConfigUpdate,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    """
    Обновить конфигурацию.
    
    Требуются права суперпользователя.
    """
    config = await crud.config.get(db, id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Конфигурация с ID {config_id} не найдена"
        )
    
    # Проверяем, существует ли другая конфигурация с такой же версией
    if config_in.version and config_in.version != config.version:
        existing_config = await crud.config.get_by_version(db, version=config_in.version)
        if existing_config and existing_config.id != config_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Конфигурация с версией {config_in.version} уже существует"
            )
    
    # Обновляем конфигурацию
    config = await crud.config.update(db, db_obj=config, obj_in=config_in)
    
    return config

@router.delete(
    "/{config_id}",
    response_model=schemas.Msg,
    dependencies=[Depends(get_current_active_superuser)],
    summary="Удалить конфигурацию"
)
async def delete_config(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_id: int,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    """
    Удалить конфигурацию.
    
    Требуются права суперпользователя.
    """
    config = await crud.config.get(db, id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Конфигурация с ID {config_id} не найдена"
        )
    
    # Проверяем, является ли конфигурация активной или по умолчанию
    if config.is_active or config.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно удалить активную конфигурацию или конфигурацию по умолчанию"
        )
    
    # Удаляем конфигурацию
    await crud.config.remove(db, id=config_id)
    
    return {"msg": f"Конфигурация с ID {config_id} успешно удалена"}

# --- Синхронизация конфигурации ---

@router.post(
    "/{config_id}/deploy",
    response_model=ConfigDeployResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(get_current_active_superuser)],
    summary="Развернуть конфигурацию на нодах"
)
async def deploy_config(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_id: int,
    deploy_in: ConfigDeployRequest,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    """
    Развернуть конфигурацию на указанных нодах.
    
    Требуются права суперпользователя.
    """
    # Получаем конфигурацию
    config = await crud.config.get(db, id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Конфигурация с ID {config_id} не найдена"
        )
    
    # Создаем сервис синхронизации
    sync_service = ConfigSyncService(db)
    
    # Запускаем развертывание
    response = await sync_service.deploy_config(
        config_version=config,
        nodes=deploy_in.nodes,
        force=deploy_in.force,
        restart_services=deploy_in.restart_services,
        current_user=current_user
    )
    
    return response

@router.post(
    "/sync-all",
    response_model=ConfigDeployResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(get_current_active_superuser)],
    summary="Синхронизировать конфигурацию на всех нодах"
)
async def sync_all_nodes(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_version: Optional[str] = None,
    force: bool = False,
    restart_services: bool = True,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    """
    Синхронизировать конфигурацию на всех активных нодах.
    
    Требуются права суперпользователя.
    """
    # Создаем сервис синхронизации
    sync_service = ConfigSyncService(db)
    
    # Запускаем синхронизацию
    response = await sync_service.sync_all_nodes(
        config_version=config_version,
        force=force,
        restart_services=restart_services,
        current_user=current_user
    )
    
    return response

@router.get(
    "/{config_id}/sync-status",
    response_model=List[NodeSyncStatus],
    dependencies=[Depends(get_current_user)],
    summary="Получить статус синхронизации конфигурации"
)
async def get_config_sync_status(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_id: int,
    node_id: Optional[int] = None,
) -> Any:
    """
    Получить статус синхронизации конфигурации.
    
    Если указан node_id, возвращается статус для указанной ноды,
    иначе возвращается статус для всех нод.
    """
    # Проверяем, существует ли конфигурация
    config = await crud.config.get(db, id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Конфигурация с ID {config_id} не найдена"
        )
    
    # Создаем сервис синхронизации
    sync_service = ConfigSyncService(db)
    
    # Получаем статус синхронизации
    statuses = await sync_service.get_sync_status(config, node_id=node_id)
    
    return statuses

@router.get(
    "/{config_id}/sync-summary",
    response_model=Dict[str, Any],
    dependencies=[Depends(get_current_user)],
    summary="Получить сводную информацию о синхронизации конфигурации"
)
async def get_config_sync_summary(
    *,
    db: AsyncSession = Depends(get_async_db),
    config_id: int,
) -> Any:
    """
    Получить сводную информацию о синхронизации конфигурации.
    
    Возвращает общее количество нод, количество синхронизированных нод,
    количество нод в процессе синхронизации, количество нод с ошибками
    и общий статус синхронизации.
    """
    # Проверяем, существует ли конфигурация
    config = await crud.config.get(db, id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Конфигурация с ID {config_id} не найдена"
        )
    
    # Создаем сервис синхронизации
    sync_service = ConfigSyncService(db)
    
    # Получаем сводную информацию
    summary = await sync_service.get_config_sync_summary(config)
    
    return summary

# --- Вспомогательные эндпоинты ---

@router.post(
    "/validate",
    response_model=ConfigValidationResponse,
    summary="Проверить валидность конфигурации"
)
async def validate_config(
    *,
    config: Dict[str, Any] = Body(..., embed=True),
) -> Any:
    """
    Проверить валидность конфигурации Xray.
    
    Проверяет синтаксис и семантику конфигурации.
    """
    try:
        # Реальная валидация через XrayService
        from app.services.xray import XrayService
        import logging
        
        logger = logging.getLogger(__name__)
        xray_service = XrayService()
        
        # Валидируем конфигурацию
        validation_result = await xray_service.validate_config(config)
        
        if not validation_result.get("is_valid", False):
            return {
                "is_valid": False,
                "errors": validation_result.get("errors", ["Неизвестная ошибка валидации"]),
                "warnings": validation_result.get("warnings", [])
            }
        
        return {
            "is_valid": True,
            "errors": [],
            "warnings": validation_result.get("warnings", [])
        }
    except Exception as e:
        logger.error(f"Ошибка валидации конфигурации Xray: {e}")
        return {
            "is_valid": False,
            "errors": [f"Ошибка валидации: {str(e)}"],
            "warnings": []
        }

@router.get(
    "/templates",
    response_model=List[ConfigTemplate],
    summary="Получить список шаблонов конфигураций"
)
async def list_config_templates() -> Any:
    """
    Получить список доступных шаблонов конфигураций.
    
    Возвращает предопределенные шаблоны конфигураций,
    которые можно использовать в качестве отправной точки.
    """
    try:
        # Загружаем шаблоны из файлов или базы данных
        from pathlib import Path
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        templates_dir = Path(settings.BASE_DIR) / "templates" / "xray"
        templates = []
        
        # Создаем директорию шаблонов, если она не существует
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем шаблоны из файлов
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        templates.append({
                            "name": template_file.stem,
                            "description": template_data.get("description", f"Шаблон {template_file.stem}"),
                            "template": template_data.get("template", {}),
                            "variables": template_data.get("variables", {})
                        })
                except Exception as e:
                    logger.error(f"Ошибка загрузки шаблона {template_file}: {e}")
        
        # Если шаблоны не найдены, возвращаем базовые шаблоны
        if not templates:
            templates = [
                {
                    "name": "basic",
                    "description": "Базовая конфигурация с минимальными настройками",
                    "template": {
                        "log": {
                            "loglevel": "warning"
                        },
                        "inbounds": [],
                        "outbounds": [
                            {
                                "protocol": "freedom",
                                "tag": "direct"
                            },
                            {
                                "protocol": "blackhole",
                                "tag": "blocked"
                            }
                        ],
                        "routing": {
                            "domainStrategy": "AsIs",
                            "rules": []
                        }
                    },
                    "variables": {}
                },
                {
                    "name": "full",
                    "description": "Полная конфигурация со всеми возможными настройками",
                    "template": {
                        "log": {
                            "access": "logs/xray/access.log",
                            "error": "logs/xray/error.log",
                            "loglevel": "warning"
                        },
                        "api": {
                            "tag": "api",
                            "services": ["HandlerService", "LoggerService", "StatsService"]
                        },
                        "stats": {},
                        "policy": {
                            "levels": {
                                "0": {
                                    "handshake": 4,
                                    "connIdle": 300,
                                    "uplinkOnly": 2,
                                    "downlinkOnly": 5
                                }
                            },
                            "system": {
                                "statsInboundUplink": True,
                                "statsInboundDownlink": True
                            }
                        },
                        "inbounds": [],
                        "outbounds": [
                            {
                                "protocol": "freedom",
                                "tag": "direct"
                            },
                            {
                                "protocol": "blackhole",
                                "tag": "blocked"
                            }
                        ],
                        "transport": {},
                        "routing": {
                            "domainStrategy": "AsIs",
                            "rules": []
                        }
                    },
                    "variables": {}
                }
            ]
        
        return templates
        
    except Exception as e:
        logger.error(f"Ошибка загрузки шаблонов конфигурации: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки шаблонов конфигурации"
        )

@router.get(
    "/templates/{template_name}",
    response_model=ConfigTemplate,
    summary="Получить шаблон конфигурации по имени"
)
async def get_config_template(
    template_name: str,
) -> Any:
    """
    Получить шаблон конфигурации по имени.
    
    Возвращает предопределенный шаблон конфигурации
    с указанным именем.
    """
    # TODO: Загружать шаблон из файла или базы данных
    # Это примерный шаблон
    if template_name == "basic":
        return {
            "name": "basic",
            "description": "Базовая конфигурация с минимальными настройками",
            "template": {
                "log": {
                    "loglevel": "warning"
                },
                "inbounds": [],
                "outbounds": [
                    {
                        "protocol": "freedom",
                        "tag": "direct"
                    },
                    {
                        "protocol": "blackhole",
                        "tag": "blocked"
                    }
                ],
                "routing": {
                    "domainStrategy": "AsIs",
                    "rules": []
                }
            },
            "variables": {}
        }
    elif template_name == "full":
        return {
            "name": "full",
            "description": "Полная конфигурация со всеми возможными настройками",
            "template": {
                "log": {
                    "access": "logs/xray/access.log",
                    "error": "logs/xray/error.log",
                    "loglevel": "warning"
                },
                "api": {
                    "tag": "api",
                    "services": ["HandlerService", "LoggerService", "StatsService"]
                },
                "stats": {},
                "policy": {
                    "levels": {
                        "0": {
                            "handshake": 4,
                            "connIdle": 300,
                            "uplinkOnly": 2,
                            "downlinkOnly": 5
                        }
                    },
                    "system": {
                        "statsInboundUplink": True,
                        "statsInboundDownlink": True
                    }
                },
                "inbounds": [],
                "outbounds": [
                    {
                        "protocol": "freedom",
                        "tag": "direct"
                    },
                    {
                        "protocol": "blackhole",
                        "tag": "blocked"
                    }
                ],
                "transport": {},
                "routing": {
                    "domainStrategy": "AsIs",
                    "rules": []
                }
            },
            "variables": {}
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Шаблон конфигурации '{template_name}' не найден"
        )


@router.post("/validate", summary="Валидация конфигурации")
async def validate_config(
    config_data: Dict[str, Any] = Body(...),
    current_user: models.User = Depends(get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Валидация конфигурации Xray.
    
    Проверяет корректность переданной конфигурации.
    """
    try:
        # Базовая валидация структуры
        required_fields = ["inbounds", "outbounds"]
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            return {
                "valid": False,
                "errors": [f"Отсутствует обязательное поле: {field}" for field in missing_fields],
                "warnings": []
            }
        
        # Проверка inbounds
        errors = []
        warnings = []
        
        if not isinstance(config_data["inbounds"], list):
            errors.append("Поле 'inbounds' должно быть массивом")
        elif not config_data["inbounds"]:
            warnings.append("Не настроены входящие подключения")
        
        # Проверка outbounds
        if not isinstance(config_data["outbounds"], list):
            errors.append("Поле 'outbounds' должно быть массивом")
        elif not config_data["outbounds"]:
            errors.append("Должно быть настроено хотя бы одно исходящее подключение")
        
        # Проверка портов
        used_ports = set()
        for inbound in config_data.get("inbounds", []):
            if isinstance(inbound, dict) and "port" in inbound:
                port = inbound["port"]
                if port in used_ports:
                    errors.append(f"Порт {port} используется несколько раз")
                used_ports.add(port)
                
                if not (1 <= port <= 65535):
                    errors.append(f"Некорректный порт: {port}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "summary": {
                "inbounds_count": len(config_data.get("inbounds", [])),
                "outbounds_count": len(config_data.get("outbounds", [])),
                "ports_used": list(used_ports)
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка валидации конфигурации: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка валидации: {str(e)}"
        )
