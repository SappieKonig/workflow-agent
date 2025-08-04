from pydantic import BaseModel
import json
from pathlib import Path


class N8NCredential(BaseModel):
    api_key: str
    api_url: str

    def write(self, path: Path) -> None:
        with open(path, "w") as f:
            json.dump(self.model_dump(), f)

    @classmethod
    def read(cls, path: Path) -> "N8NCredential":
        with open(path, "r") as f:
            return cls(**json.load(f))
    
