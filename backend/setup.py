from setuptools import setup, find_packages

setup(
    name="vpn_panel",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.95.0",
        "uvicorn[standard]==0.22.0",
        "sqlalchemy[asyncio]==2.0.20",
        "alembic==1.12.0",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.18",
        "python-dotenv==1.0.0",
        "psycopg2-binary==2.9.6",
        "python-dateutil==2.8.2",
        "pydantic[email]==1.10.7",
        "python-slugify==8.0.1",
        "typing-extensions==4.5.0",
        "aiosmtplib==2.0.1",
        "jinja2==3.1.6",
        "python-json-logger==2.0.7",
        "pyotp==2.8.0",
        "qrcode==7.4.2",
        "pytz==2023.3",
        "email-validator==2.0.0",
    ],
    entry_points={
        'console_scripts': [
            'vpn-panel=app.main:main',
        ],
    },
)
