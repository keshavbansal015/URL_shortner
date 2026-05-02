from pydantic import BaseModel
from typing import Optional

class URLRequestShortenRequest(BaseModel):
    long_url: str
    expiration: Optional[int] = None

class URLResponseShortenResponse(BaseModel):
    key: str
    long_url: str
    short_url: str

class URLResponseGet(BaseModel):
    key: str
    long_url: str
    short_url: str

class URLResponseRedirect(BaseModel):
    key: str
    long_url: str
    status_code: int

class URLResponseStats(BaseModel):
    key: str
    long_url: str
    created_at: str
    clicks: int

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str
    active_urls: int

class UserLogin(BaseModel):
    username: str
    password: str