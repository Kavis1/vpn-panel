"""
Сервис для отправки электронных писем.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings
from app.core.logging import logger

class EmailService:
    """Сервис для отправки электронных писем."""
    
    @classmethod
    async def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Отправляет электронное письмо.
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            html_content: HTML-содержимое письма
            text_content: Текстовое содержимое письма (опционально)
            
        Returns:
            bool: True, если письмо успешно отправлено, иначе False
        """
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            logger.warning("SMTP settings not configured, email will not be sent")
            return False
            
        if not text_content:
            # Генерируем текстовую версию из HTML, если не предоставлена
            import re
            text_content = re.sub(r'<[^>]*>', ' ', html_content)
            text_content = ' '.join(text_content.split())
            
        # Создаем сообщение
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg['To'] = to_email
        
        # Прикрепляем текстовую и HTML версии
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            # Создаем безопасное соединение с сервером
            context = ssl.create_default_context()
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls(context=context)
                
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
                logger.info(f"Email sent to {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @classmethod
    async def send_reset_password_email(
        cls, 
        email_to: str, 
        username: str,
        token: str
    ) -> bool:
        """
        Отправляет письмо для сброса пароля.
        
        Args:
            email_to: Email пользователя
            username: Имя пользователя
            token: Токен для сброса пароля
            
        Returns:
            bool: True, если письмо успешно отправлено, иначе False
        """
        subject = f"{settings.PROJECT_NAME} - Восстановление пароля"
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body>
                <h2>Восстановление пароля</h2>
                <p>Здравствуйте, {username}!</p>
                <p>Для сброса пароля перейдите по ссылке ниже:</p>
                <p><a href="{reset_url}">Сбросить пароль</a></p>
                <p>Ссылка действительна в течение {settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS} часов.</p>
                <p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
                <p>С уважением,<br/>{settings.PROJECT_NAME}</p>
            </body>
        </html>
        """
        
        return await cls.send_email(
            to_email=email_to,
            subject=subject,
            html_content=html_content
        )
    
    @classmethod
    async def send_email_verification(
        cls, 
        email_to: str, 
        username: str,
        token: str
    ) -> bool:
        """
        Отправляет письмо для подтверждения email.
        
        Args:
            email_to: Email пользователя
            username: Имя пользователя
            token: Токен для подтверждения email
            
        Returns:
            bool: True, если письмо успешно отправлено, иначе False
        """
        subject = f"{settings.PROJECT_NAME} - Подтверждение email"
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        html_content = f"""
        <html>
            <body>
                <h2>Подтверждение email</h2>
                <p>Здравствуйте, {username}!</p>
                <p>Спасибо за регистрацию в {settings.PROJECT_NAME}.</p>
                <p>Для подтверждения вашего email перейдите по ссылке ниже:</p>
                <p><a href="{verification_url}">Подтвердить email</a></p>
                <p>Ссылка действительна в течение {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} часов.</p>
                <p>Если вы не регистрировались в нашем сервисе, проигнорируйте это письмо.</p>
                <p>С уважением,<br/>{settings.PROJECT_NAME}</p>
            </body>
        </html>
        """
        
        return await cls.send_email(
            to_email=email_to,
            subject=subject,
            html_content=html_content
        )
