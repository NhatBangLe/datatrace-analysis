from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.models.service import Trace, TraceFile


class IAnalyticsService(ABC):

    @abstractmethod
    def create_trace(self, data: Trace) -> Optional[Trace]:
        raise NotImplementedError

    @abstractmethod
    def add_trace_file(self, trace_id: str, data: TraceFile) -> Optional[TraceFile]:
        raise NotImplementedError

    @abstractmethod
    def get_trace_stats(self, trace_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_analysis_summary(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class IStorageService(ABC):

    @abstractmethod
    def upload_file(self, file_content: bytes, filename: str, **kwargs) -> str:
        raise NotImplementedError
