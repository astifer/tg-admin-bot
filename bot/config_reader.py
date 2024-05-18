from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    RABBITMQ_DEFAULT_USER: SecretStr
    RABBITMQ_DEFAULT_PASS: SecretStr
    # RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS: SecretStr
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )


config = Settings()
