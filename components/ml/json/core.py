import json
from pathlib import Path
from typing import Any


class Json:
    def __init__(self, path: Path):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        data = self._load()
        return data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self._load()
        data[key] = value
        self._save(data)

    def increment(self, key: str, amount: int = 1) -> int:
        data = self._load()
        current = data.get(key, 0)
        new_value = current + amount
        data[key] = new_value
        self._save(data)
        return new_value

    def get_all(self) -> dict:
        return self._load()

    def set_all(self, data: dict) -> None:
        self._save(data)

    def append(self, item: dict) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

