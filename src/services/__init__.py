from abc import ABC, abstractmethod
from typing import Any, Dict

from src.schemas import TraceMetadata


class IAnalyticsService(ABC):

    @abstractmethod
    def connect(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def insert_trace_metadata(self, metadata: TraceMetadata):
        raise NotImplementedError

    @abstractmethod
    def get_trace_stats(self, trace_id: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_analysis_summary(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class IStorageService(ABC):

    @abstractmethod
    def upload_file(self, file_content: bytes, filename: str, **kwargs) -> str:
        raise NotImplementedError
