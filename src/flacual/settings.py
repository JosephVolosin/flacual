from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class Settings(Environment):
    library: str


settings = Settings()
