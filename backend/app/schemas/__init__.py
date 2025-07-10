# Импортируем все схемы, чтобы они были доступны через app.schemas
from .base import BaseModel, BaseResponse, PaginatedResponse, Msg
from .token import Token, TokenPayload, TokenData, RefreshToken, TokenCreate, TokenResponse
from .user import (
    UserBase, UserCreate, UserUpdate, UserInDBBase, UserLogin, 
    UserRegister, UserPasswordReset, UserPasswordResetConfirm,
    UserPasswordChange, User, UserInDB, UserList
)
from .vpn_user import VPNUser, VPNUserCreate, VPNUserUpdate, VPNUserInDB
from .config import ConfigCreate, ConfigUpdate, ConfigInDB
from .device import DeviceCreate, DeviceUpdate, DeviceInDB, DeviceStats, Device, DeviceList
from .node import Node, NodeCreate, NodeUpdate, NodeInDB
from .subscription import (
    Plan, PlanCreate, PlanUpdate, PlanInDB,
    Subscription, SubscriptionCreate, SubscriptionUpdate, SubscriptionInDB, SubscriptionWithPlan,
    SubscriptionPlan, SubscriptionPlanCreate, SubscriptionPlanUpdate,
    UserSubscription, UserSubscriptionCreate, UserSubscriptionUpdate
)
from .xray import XrayUserCreate, XrayConfigCreate, XrayConfigUpdate
from .xtls import (
    XTLSUser, XTLSUserCreate, XTLSUserBase, XTLSConfig, XTLSStats,
    XTLSReload, XTLSConnectionInfo, XTLSCertificate
)

__all__ = [
    'BaseModel', 'BaseResponse', 'PaginatedResponse', 'Msg',
    'Token', 'TokenPayload', 'TokenData', 'RefreshToken', 'TokenCreate', 'TokenResponse',
    'UserBase', 'UserCreate', 'UserUpdate', 'UserInDBBase', 'UserLogin',
    'UserRegister', 'UserPasswordReset', 'UserPasswordResetConfirm',
    'UserPasswordChange', 'User', 'UserInDB', 'UserList', 'UserResetPassword', 'UserUpdatePassword',
    'VPNUser', 'VPNUserCreate', 'VPNUserUpdate', 'VPNUserInDB',
    'ConfigCreate', 'ConfigUpdate', 'ConfigInDB',
    'DeviceCreate', 'DeviceUpdate', 'DeviceInDB', 'DeviceStats', 'Device', 'DeviceList',
    'Node', 'NodeCreate', 'NodeUpdate', 'NodeInDB',
    'Plan', 'PlanCreate', 'PlanUpdate', 'PlanInDB',
    'Subscription', 'SubscriptionCreate', 'SubscriptionUpdate', 'SubscriptionInDB', 'SubscriptionWithPlan',
    'SubscriptionPlan', 'SubscriptionPlanCreate', 'SubscriptionPlanUpdate',
    'UserSubscription', 'UserSubscriptionCreate', 'UserSubscriptionUpdate',
    'XrayUserCreate', 'XrayConfigCreate', 'XrayConfigUpdate',
    'XTLSUser', 'XTLSUserCreate', 'XTLSUserBase', 'XTLSConfig', 'XTLSStats',
    'XTLSReload', 'XTLSConnectionInfo', 'XTLSCertificate'
]
