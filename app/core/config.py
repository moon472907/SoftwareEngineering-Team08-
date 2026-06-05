from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./wiki.db"
    SECRET_KEY: str = "my-super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # 위키 수정 락 자동 만료 시간(분). 이 시간이 지난 락은 다른 사용자가 덮어쓸 수 있다.
    EDIT_LOCK_TIMEOUT_MINUTES: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()