import os
from abc import ABC, abstractmethod
from typing import Dict

from pydantic import BaseModel


class Service(BaseModel, ABC):
    name: str

    @abstractmethod
    async def run_check(self) -> bool:
        pass


class HuggingFaceService(Service):
    name: str = "huggingface"

    async def run_check(self) -> bool:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get("https://huggingface.co/api/health", timeout=5.0)
                return resp.status_code == 200
        except Exception:
            return False


class HealthCheck:
    _instance = None

    def __init__(self, services_to_check=None):
        self.all_services = {
            "huggingface": HuggingFaceService(),
        }

        if services_to_check:
            self.services = {
                service: service_obj
                for service, service_obj in self.all_services.items()
                if service in services_to_check
            }
        else:
            self.services = self.all_services

    def get_available_dependencies(self) -> Dict[str, bool]:
        """Check available dependencies by looking at env variables."""
        return {
            "huggingface": bool(os.getenv("HF_TOKEN")),
        }

    @classmethod
    def get_instance(cls, services_to_check=None):
        if cls._instance is None:
            cls._instance = cls(services_to_check)
        return cls._instance

    async def run_checks(self) -> dict:
        results = {}
        for service in self.services.values():
            if self.get_available_dependencies().get(service.name):
                results[service.name] = await service.run_check()
        return results
