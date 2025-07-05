"""
XTLS Service Module

This module provides integration with XTLS-SDK for enhanced security features.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import shutil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_vpn_user import vpn_user as crud_vpn_user
from app.schemas.vpn_user import VPNUserCreate, VPNUserUpdate

logger = logging.getLogger(__name__)

class XTLSService:
    """Service for handling XTLS-related operations."""
    
    def __init__(self, xray_config_dir: str = "/etc/xray"):
        """Initialize XTLS service with configuration directory.
        
        Args:
            xray_config_dir: Directory containing Xray configuration files
        """
        self.xray_config_dir = Path(xray_config_dir)
        self.xray_config_file = self.xray_config_dir / "config.json"
        self.xtls_cert_dir = self.xray_config_dir / "certs"
        self.xtls_cert_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_user_certificate(self, user_id: str, email: str) -> Dict[str, str]:
        """Generate XTLS certificate for a user.
        
        Args:
            user_id: Unique user ID
            email: User's email for certificate subject
            
        Returns:
            Dict containing certificate paths and expiration info
        """
        try:
            # Create user-specific certificate directory
            user_cert_dir = self.xtls_cert_dir / f"user_{user_id}"
            user_cert_dir.mkdir(exist_ok=True)
            
            # Certificate paths
            key_path = user_cert_dir / "xtls.key"
            cert_path = user_cert_dir / "xtls.crt"
            
            # Generate private key and certificate
            subprocess.run([
                "openssl", "req", "-x509", "-nodes", "-days", "365", "-newkey", "rsa:2048",
                "-keyout", str(key_path), "-out", str(cert_path),
                "-subj", f"/CN={email}/O=VPN Panel/C=US"
            ], check=True)
            
            # Set proper permissions
            key_path.chmod(0o600)
            cert_path.chmod(0o644)
            
            return {
                "key_path": str(key_path),
                "cert_path": str(cert_path),
                "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
                "user_id": user_id
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate XTLS certificate: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate XTLS certificate"
            )
            
    def get_xray_config(self) -> Dict[str, Any]:
        """Get current Xray configuration with XTLS settings.
        
        Returns:
            Current Xray configuration as a dictionary
        """
        if not self.xray_config_file.exists():
            return self._get_default_xray_config()
            
        with open(self.xray_config_file, 'r') as f:
            return json.load(f)
            
    def update_xray_config(self, config: Dict[str, Any]) -> None:
        """Update Xray configuration file.
        
        Args:
            config: New Xray configuration
        """
        # Create backup of current config
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.xray_config_file.with_suffix(f".{timestamp}.bak")
        if self.xray_config_file.exists():
            shutil.copy2(self.xray_config_file, backup_path)
            
        # Save new config
        with open(self.xray_config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
    def _get_default_xray_config(self) -> Dict[str, Any]:
        """Get default Xray configuration with XTLS support.
        
        Returns:
            Default Xray configuration dictionary
        """
        return {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "port": 443,
                    "protocol": "vless",
                    "settings": {
                        "clients": [],
                        "decryption": "none"
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "xtls",
                        "xtlsSettings": {
                            "alpn": ["h2", "http/1.1"],
                            "certificates": [
                                {
                                    "certificateFile": "/etc/xray/cert.pem",
                                    "keyFile": "/etc/xray/key.pem"
                                }
                            ]
                        }
                    }
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom"
                }
            ]
        }
        
    async def add_user_to_xray(self, user_id: str, email: str) -> Dict[str, str]:
        """Add a new user to Xray configuration with XTLS.
        
        Args:
            user_id: Unique user ID
            email: User's email
            
        Returns:
            User's connection details
        """
        # Generate certificate for the user
        cert_info = await self.generate_user_certificate(user_id, email)
        
        # Get current config
        config = self.get_xray_config()
        
        # Generate VLESS user ID
        vless_user_id = str(os.urandom(16).hex())
        
        # Add user to Xray config
        client_config = {
            "id": vless_user_id,
            "email": email,
            "flow": "xtls-rprx-direct"
        }
        
        # Find or create clients array in the first inbound
        if not config["inbounds"]:
            config["inbounds"] = [{"settings": {"clients": []}}]
            
        if "settings" not in config["inbounds"][0]:
            config["inbounds"][0]["settings"] = {}
            
        if "clients" not in config["inbounds"][0]["settings"]:
            config["inbounds"][0]["settings"]["clients"] = []
            
        # Add user to clients
        config["inbounds"][0]["settings"]["clients"].append(client_config)
        
        # Save updated config
        self.update_xray_config(config)
        
        return {
            "id": user_id,
            "vless_id": vless_user_id,
            "certificate": {
                "key": cert_info["key_path"],
                "cert": cert_info["cert_path"],
                "expires_at": cert_info["expires_at"]
            },
            "connection_string": f"vless://{vless_user_id}@{settings.SERVER_HOST}:443?security=xtls&flow=xtls-rprx-direct#VPN-{email}"
        }
        
    async def remove_user_from_xray(self, user_id: str) -> bool:
        """Remove a user from Xray configuration.
        
        Args:
            user_id: User ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current config
            config = self.get_xray_config()
            
            # Remove user from clients
            if config["inbounds"] and "settings" in config["inbounds"][0] and "clients" in config["inbounds"][0]["settings"]:
                config["inbounds"][0]["settings"]["clients"] = [
                    client for client in config["inbounds"][0]["settings"]["clients"]
                    if client.get("email") != user_id
                ]
                
                # Save updated config
                self.update_xray_config(config)
                
                # Remove user's certificate directory
                user_cert_dir = self.xtls_cert_dir / f"user_{user_id}"
                if user_cert_dir.exists():
                    shutil.rmtree(user_cert_dir)
                    
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove user from Xray: {e}")
            
        return False

# Create a singleton instance
xtls_service = XTLSService()
