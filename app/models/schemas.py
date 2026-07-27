from pydantic import BaseModel


class Region(BaseModel):
    id: str
    name: str


class Device(BaseModel):
    id: str
    name: str


class QueryRequest(BaseModel):
    hostname: str
    question: str


class ErrorResponse(BaseModel):
    error: str
