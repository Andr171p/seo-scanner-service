from typing import Final, Literal

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


class EmbeddingsSettings(BaseSettings):
    base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_prefix="EMBEDDINGS_")


class RabbitMQSettings(BaseSettings):
    port: int = 5672
    host: str = "localhost"
    user: str = "<USER>"
    password: str = "<PASSWORD>"

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"


class PostgresSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    user: str = "<USER>"
    password: str = "<PASSWORD>"
    db: str = "postgres"
    driver: Literal["asyncpg"] = "asyncpg"

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    @property
    def sqlalchemy_url(self) -> str:
        return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    embeddings: EmbeddingsSettings = EmbeddingsSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    postgres: PostgresSettings = PostgresSettings()


settings: Final[Settings] = Settings()
