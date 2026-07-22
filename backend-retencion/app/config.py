from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./retenciones.db"
    AGENT_TOKEN: str = "dev-token-inseguro"
    SRI_RUC: str = ""
    SRI_PASSWORD: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:4200"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
