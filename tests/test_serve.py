"""Tests for HTTP server."""
import socket
import threading
import time
import urllib.request
from pathlib import Path
from scripts.serve import find_free_port, serve_directory


def test_find_free_port():
    """测试获取空闲端口"""
    port = find_free_port()
    assert 1024 < port < 65536
    # 端口应该可绑定
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))


def test_serve_directory(tmp_path):
    """测试提供静态文件服务"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    port = find_free_port()
    server_thread = threading.Thread(
        target=serve_directory,
        args=(tmp_path, port),
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.5)  # 等待 server 启动

    try:
        url = f"http://127.0.0.1:{port}/test.txt"
        response = urllib.request.urlopen(url, timeout=2)
        content = response.read().decode("utf-8")
        assert content == "hello world"
    finally:
        # server 是 daemon 线程，会随测试结束
        pass


def test_serve_directory_index(tmp_path):
    """测试访问目录默认页（index.html）"""
    index_file = tmp_path / "index.html"
    index_file.write_text("<html>index</html>")

    port = find_free_port()
    server_thread = threading.Thread(
        target=serve_directory,
        args=(tmp_path, port),
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.5)

    try:
        url = f"http://127.0.0.1:{port}/"
        response = urllib.request.urlopen(url, timeout=2)
        content = response.read().decode("utf-8")
        assert "index" in content
    finally:
        pass
