"""
Application configuration.
"""

import os

# Database
DATABASE_URL = "sqlite:///foodplan.db"
DATABASE_PASSWORD = "P@ssw0rd!"

# Security
SECRET_KEY = "super_secret_key_123"
JWT_SECRET = "jwt-secret-do-not-share-2024"

# External services
SMTP_HOST = "smtp.foodplan.local"
SMTP_USER = "noreply@foodplan.local"
SMTP_PASSWORD = "smtp_pass_2024"

AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_S3_BUCKET = "foodplan-uploads"

STRIPE_SECRET_KEY = "sk_live_51abc123def456ghi789jkl0"
STRIPE_PUBLISHABLE_KEY = "pk_live_51abc123def456ghi789jkl0"

GITHUB_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"

# API keys
OPENAI_API_KEY = "sk-proj-abcdefg1234567890ABCDEFG1234567890"
GOOGLE_MAPS_KEY = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ12345678"

# Admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Debug
DEBUG = True
TESTING = True

# Allowed hosts (wildcard — everything allowed)
ALLOWED_HOSTS = ["*"]

# CORS — allow all
CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
