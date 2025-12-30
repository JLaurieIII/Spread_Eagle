from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: PostgresDsn = "postgresql://user:pass@localhost:5432/spread_eagle"

    # Database settings
    DB_HOST: str = "spread-eagle-db.cluster-cbwyw8ky62xm.us-east-2.rds.amazonaws.com"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # API Keys
    CFB_API_KEY: str | None = None
    CBB_API_KEY: str | None = None

    @property
    def db_host(self) -> str:
        return self.DB_HOST

    @property
    def db_port(self) -> int:
        return self.DB_PORT

    @property
    def db_name(self) -> str:
        return self.DB_NAME

    @property
    def db_user(self) -> str:
        return self.DB_USER

    @property
    def db_password(self) -> str:
        return self.DB_PASSWORD

    @property
    def cfb_api_key(self) -> str:
        """Backwards-compatible alias for CFB ingest scripts."""
        return (self.CFB_API_KEY or "").strip()

    @property
    def cbb_api_key(self) -> str:
        """CBB API key for college basketball data."""
        return (self.CBB_API_KEY or "").strip()

    def require_cfb(self) -> None:
        """Validate CFB API key at runtime."""
        if not self.cfb_api_key:
            raise RuntimeError(
                "Missing CFBD API key. Set CFB_API_KEY in .env"
            )

    def require_cbb(self) -> None:
        """Validate CBB API key at runtime."""
        if not self.cbb_api_key:
            raise RuntimeError(
                "Missing CBB API key. Set CBB_API_KEY in .env"
            )

    def require(self, sport: str = "cfb") -> None:
        """Validate API key for a sport."""
        if sport == "cfb":
            self.require_cfb()
        elif sport == "cbb":
            self.require_cbb()
        else:
            raise ValueError(f"Unknown sport: {sport}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
