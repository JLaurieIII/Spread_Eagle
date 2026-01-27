from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn

# Project root directory (where .env lives)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    ENV: str = "dev"
    # Optional full DSN; if not provided, one is built from the fields below.
    DATABASE_URL: str | None = None

    # Database settings (supply via environment or Secrets Manager)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "spread_eagle"
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

    def database_url(self) -> str:
        """Return the configured database URL, building from components when needed."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
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
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
