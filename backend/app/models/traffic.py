from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import axios, { AxiosResponse } from 'axios';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления токена авторизации
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('vpn_panel_auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обработки ответов и ошибок
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Если получили 401 и это не повторный запрос
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Пытаемся обновить токен
      const refreshToken = localStorage.getItem('vpn_panel_refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          
          const newToken = response.data.access_token;
          localStorage.setItem('vpn_panel_auth_token', newToken);
          
          // Повторяем оригинальный запрос с новым токеном
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Если обновление токена не удалось, очищаем хранилище и редиректим
          localStorage.removeItem('vpn_panel_auth_token');
          localStorage.removeItem('vpn_panel_refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // Нет refresh токена, редиректим на логин
        localStorage.removeItem('vpn_panel_auth_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Типы для API ответов
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Утилитарные функции для работы с API
export const apiUtils = {
  // Обработка ошибок
  handleError: (error: any): string => {
    if (error.response?.data?.detail) {
      return Array.isArray(error.response.data.detail) 
        ? error.response.data.detail.map((e: any) => e.msg).join(', ')
        : error.response.data.detail;
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return 'Произошла неизвестная ошибка';
  },

  // Построение URL с параметрами
  buildUrl: (endpoint: string, params?: Record<string, any>): string => {
    if (!params) return endpoint;
    
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    
    const queryString = searchParams.toString();
    return queryString ? `${endpoint}?${queryString}` : endpoint;
  },

  // Форматирование данных для FormData
  toFormData: (data: Record<string, any>): FormData => {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (value instanceof File) {
          formData.append(key, value);
        } else if (typeof value === 'object') {
          formData.append(key, JSON.stringify(value));
        } else {
          formData.append(key, String(value));
        }
      }
    });
    return formData;
  }
};

export default api;from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, and_

import uuid
import ipaddress

from ..database import Base
from .types import UUID, INET

class TrafficLog(Base):
    """Модель для логирования трафика пользователей."""
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(), default=uuid.uuid4, unique=True, index=True)
    
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api, { apiUtils } from '../services/api';
import { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY } from '../config';

interface User {
  id: number;
  email: string;
  username?: string;
  full_name?: string;
  is_superuser: boolean;
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Check if user is already logged in on initial load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (token) {
        try {
          const response = await api.get<User>('/auth/me');
          setUser(response.data);
          setError(null);
        } catch (error) {
          console.error('Failed to get current user:', error);
          // Clear invalid token
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
          setError(apiUtils.handleError(error));
        }
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Отправляем данные как form data для OAuth2PasswordRequestForm
      const formData = new FormData();
      formData.append('username', email); // FastAPI OAuth2 ожидает username
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { access_token, refresh_token } = response.data;

      // Store tokens
      localStorage.setItem(AUTH_TOKEN_KEY, access_token);
      if (refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
      }

      // Get user data
      const userResponse = await api.get<User>('/auth/me');
      setUser(userResponse.data);
      
      setIsLoading(false);
      navigate('/dashboard');
    } catch (error) {
      setIsLoading(false);
      const errorMessage = apiUtils.handleError(error);
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };      setIsLoading(false);
    };

    checkAuth();
  }, []);  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();  is_superuser: boolean;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}    
    # Связи
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True, index=True)
    
    # Информация о подключении
    remote_ip = Column(INET, nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_id = Column(String(100), nullable=True, index=True)
    
    # Статистика трафика
    upload = Column(BigInteger, default=0)    # Исходящий трафик в байтах
    download = Column(BigInteger, default=0)  # Входящий трафик в байтах
    
    # Временные метки
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Дополнительная информация
    protocol = Column(String(50), nullable=True)  # Протокол (vmess, vless и т.д.)
    metadata_ = Column("metadata", JSON, default=dict)  # Дополнительные метаданные
    
    # Связи
    user = relationship("User", back_populates="traffic_logs")
    node = relationship("Node", back_populates="traffic_logs")
    
    def __repr__(self):
        return f"<TrafficLog User:{self.user_id} Node:{self.node_id} {self.upload}↑ {self.download}↓>"
    
    @property
    def total_traffic(self) -> int:
        """Общий объем трафика в байтах."""
        return self.upload + self.download
    
    @property
    def formatted_total_traffic(self) -> str:
        """Отформатированный общий объем трафика."""
        return self.format_bytes(self.total_traffic)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Длительность сессии."""
        if not self.started_at or not self.ended_at:
            return None
        return self.ended_at - self.started_at
    
    @property
    def is_active(self) -> bool:
        """Активна ли сессия."""
        return self.ended_at is None
    
    @staticmethod
    def format_bytes(size: int) -> str:
        """Форматирует размер в байтах в читаемый вид."""
        if not size:
            return "0 Б"
        
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ПБ"


class TrafficLimit(Base):
    """Модель для хранения лимитов трафика по периодам."""
    __tablename__ = "traffic_limits"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(), default=uuid.uuid4, unique=True, index=True)
    
    # Связи
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Период
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Лимиты
    data_limit = Column(BigInteger, nullable=True)  # В байтах, None = безлимит
    data_used = Column(BigInteger, default=0)       # Использованный трафик в байтах
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<TrafficLimit User:{self.user_id} {self.period_type} {self.period_start.date()}>"
    
    @property
    def data_remaining(self) -> Optional[int]:
        """Оставшийся трафик в байтах."""
        if self.data_limit is None:
            return None
        return max(0, self.data_limit - self.data_used)
    
    @property
    def is_exceeded(self) -> bool:
        """Превышен ли лимит трафика."""
        if self.data_limit is None:
            return False
        return self.data_used >= self.data_limit
