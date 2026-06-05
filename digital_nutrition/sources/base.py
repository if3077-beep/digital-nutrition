"""
数据源协议 - 所有数据源实现统一接口
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..models import Event


class Source(ABC):
    """数据源抽象基类 - 所有数据源继承此类

    实现示例：
        class MySource(Source):
            name = "my-source"
            def is_available(self) -> bool: ...
            def collect(self, since=None) -> list[Event]: ...
    """
    name: str  # 子类必须定义

    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可访问"""
        ...

    @abstractmethod
    def collect(self, since: Optional[datetime] = None) -> List[Event]:
        """采集事件，过滤 since 之后的"""
        ...
