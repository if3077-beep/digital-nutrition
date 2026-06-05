"""
本地 HTTP server - 用于展示报告页面（带类型注解）
"""
import contextlib
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Generator, Optional


def find_free_port() -> int:
    """找到一个可用的空闲端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class QuietHandler(SimpleHTTPRequestHandler):
    """静默的请求处理器（不打印日志 + 禁用缓存方便开发调试）"""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - 覆盖父类签名
        pass

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve_directory(directory: Path, port: Optional[int] = None) -> int:
    """在指定目录启动 HTTP server（阻塞）。

    Args:
        directory: 要服务的目录
        port: 端口（None 则自动选择）

    Returns:
        实际使用的端口
    """
    if port is None:
        port = find_free_port()
    handler = partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Serving {directory} at http://127.0.0.1:{port}/")
    server.serve_forever()
    return port


@contextlib.contextmanager
def serve_directory_context(
    directory: Path, port: int
) -> Generator[ThreadingHTTPServer, None, None]:
    """以 context manager 形式启动 HTTP server（v0.6.0: 确保资源被释放）

    用于 daemon thread 调用场景：调用方在 thread 里 serve_forever，context 退出时 cleanup。
    """
    handler = partial(QuietHandler, directory=str(directory))
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        yield httpd
