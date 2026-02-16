
from typing import Dict, Type
from .base import CloudProvider
from .gcp import GCPProvider
from .aws import AWSProvider
from .azure import AzureProvider

class ProviderFactory:
    _providers: Dict[str, Type[CloudProvider]] = {
        'gcp': GCPProvider,
        'aws': AWSProvider,
        'azure': AzureProvider
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> CloudProvider:
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class()
