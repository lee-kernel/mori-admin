from pydantic import BaseModel


class Branding(BaseModel):
    logo: str | None = None
