from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    admin_id: int
    admin_username: str
    shop_info: str = "Магазин Brand Ochki.\n\nИнформация будет добавлена позже."
    contacts: str = "Контакты будут добавлены позже."


settings = Settings()
