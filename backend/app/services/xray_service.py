import logging
from typing import Dict, Any, Optional, List
import aiohttp
import json
from datetime import datetime
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.xray import XrayConfig, XrayConfigInDB, XrayConfigCreate, XrayConfigUpdate
from app.crud.crud_xray import crud_xray_config
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

class XrayService:
    """
    Сервис для работы с Xray-core
    """
    
    def __init__(self):
        self.xray_config_path = settings.XRAY_CONFIG_PATH
        self.xray_api_url = settings.XRAY_API_URL
        self.xray_api_timeout = settings.XRAY_API_TIMEOUT
    
    async def get_config(self) -> XrayConfigInDB:
        """Получение текущей конфигурации Xray"""
        async with AsyncSessionLocal() as db:
            config = await crud_xray_config.get_active_config(db)
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Активная конфигурация Xray не найдена"
                )
            return config
    
    async def update_config(self, config_in: XrayConfigUpdate) -> XrayConfigInDB:
        """Обновление конфигурации Xray"""
        async with AsyncSessionLocal() as db:
            # Получаем текущую активную конфигурацию
            current_config = await crud_xray_config.get_active_config(db)
            
            # Создаем новую версию конфигурации
            config_data = config_in.dict(exclude_unset=True)
            new_config = XrayConfigCreate(**config_data)
            
            # Деактивируем старую конфигурацию
            if current_config:
                await crud_xray_config.deactivate(db, db_obj=current_config)
            
            # Создаем новую конфигурацию
            config = await crud_xray_config.create(db, obj_in=new_config)
            
            # Применяем конфигурацию к Xray
            await self._apply_config(config.config)
            
            return config
    
    async def _apply_config(self, config: Dict[str, Any]) -> bool:
        """Применение конфигурации к Xray через API"""
        if not self.xray_api_url:
            logger.warning("XRAY_API_URL не настроен, конфигурация не применена")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.xray_api_url}/config",
                    json={"config": config},
                    timeout=self.xray_api_timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Ошибка применения конфигурации Xray: {response.status} - {error_text}"
                        )
                        return False
                    return True
        except Exception as e:
            logger.error(f"Исключение при применении конфигурации Xray: {str(e)}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики Xray"""
        if not self.xray_api_url:
            logger.warning("XRAY_API_URL не настроен, статистика недоступна")
            return {}
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.xray_api_url}/stats",
                    timeout=self.xray_api_timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Ошибка получения статистики Xray: {response.status} - {error_text}"
                        )
                        return {}
                    return await response.json()
        except Exception as e:
            logger.error(f"Исключение при получении статистики Xray: {str(e)}")
            return {}
    
    async def restart(self) -> bool:
        """Перезапуск Xray"""
        if not self.xray_api_url:
            logger.warning("XRAY_API_URL не настроен, перезапуск невозможен")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.xray_api_url}/restart",
                    timeout=self.xray_api_timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Ошибка перезапуска Xray: {response.status} - {error_text}"
                        )
                        return False
                    return True
        except Exception as e:
            logger.error(f"Исключение при перезапуске Xray: {str(e)}")
            return False

# Создаем экземпляр сервиса
xray_service = XrayService()
