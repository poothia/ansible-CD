"""Flask application configuration."""

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "aap-demo-secret-key")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
