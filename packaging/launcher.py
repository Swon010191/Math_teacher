"""Launcher desktop cho AI Teaching Assistant (bản Setup.exe).

Nhiệm vụ:
1. Chọn port trống cho backend (ưu tiên 8000).
2. Khởi động MathBackend (FastAPI + frontend đóng gói sẵn).
3. Khởi động Pix2Text nếu runtime đã được cài (không có thì backend
   tự dùng Mock - app vẫn chạy đầy đủ tính năng toán + bảng vẽ).
4. Chờ backend sẵn sàng rồi mở trình duyệt.
5. Nằm ở tray icon: Mở bảng dạy / Khởi động lại / Thoát.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

APP_NAME = "AI Teaching Assistant"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_P2T_PORT = 8503

if sys.platform == "win32":
    _CREATE_NO_WINDOW = 0x08000000
else:  # pragma: no cover
    _CREATE_NO_WINDOW = 0


def install_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def find_port(preferred: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", preferred))
        except OSError:
            sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class Backend:
    def __init__(self) -> None:
        self.base = install_dir()
        self.backend_exe = os.path.join(self.base, "backend", "MathBackend.exe")
        self.p2t_exe = os.path.join(
            self.base, "pix2text-runtime", ".venv", "Scripts", "p2t.exe"
        )
        self.port = find_port(
            int(os.environ.get("MATH_BACKEND_PORT", str(DEFAULT_BACKEND_PORT)))
        )
        self.p2t_port = int(os.environ.get("P2T_PORT", str(DEFAULT_P2T_PORT)))
        self.server_proc: subprocess.Popen[bytes] | None = None
        self.p2t_proc: subprocess.Popen[bytes] | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def p2t_available(self) -> bool:
        return os.path.isfile(self.p2t_exe)

    def start_server(self) -> None:
        env = dict(os.environ)
        env["MATH_BACKEND_PORT"] = str(self.port)
        env["CORS_ORIGINS"] = f"http://127.0.0.1:{self.port},http://localhost:{self.port}"
        if self.p2t_available():
            env["RECOGNITION_PROVIDER"] = "pix2text"
            env["PIX2TEXT_URL"] = f"http://127.0.0.1:{self.p2t_port}"
        self.server_proc = subprocess.Popen(
            [self.backend_exe],
            env=env,
            cwd=os.path.join(self.base, "backend"),
            creationflags=_CREATE_NO_WINDOW,
        )

    def start_p2t(self) -> None:
        if not self.p2t_available():
            return
        env = dict(os.environ)
        models_dir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), APP_NAME, "models")
        os.makedirs(models_dir, exist_ok=True)
        env["PIX2TEXT_HOME"] = os.path.join(models_dir, ".pix2text")
        try:
            self.p2t_proc = subprocess.Popen(
                [self.p2t_exe, "serve", "--port", str(self.p2t_port)],
                env=env,
                cwd=os.path.dirname(os.path.dirname(self.p2t_exe)),
                creationflags=_CREATE_NO_WINDOW,
            )
        except OSError:
            self.p2t_proc = None

    def wait_ready(self, timeout_seconds: float = 60.0) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.server_proc is not None and self.server_proc.poll() is not None:
                return False
            try:
                with urllib.request.urlopen(
                    f"{self.url}/health", timeout=3
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    if payload.get("status") == "ok":
                        return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def stop(self) -> None:
        for proc in (self.p2t_proc, self.server_proc):
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        for proc in (self.p2t_proc, self.server_proc):
            if proc is not None:
                try:
                    proc.wait(timeout=10)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        self.server_proc = None
        self.p2t_proc = None


def make_icon() -> object:
    """Icon tray vẽ bằng PIL (chữ AI trên nền xanh)."""
    from PIL import Image, ImageDraw

    size = 64
    image = Image.new("RGBA", (size, size), (37, 99, 235, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=14, fill=(37, 99, 235, 255))
    draw.text((size // 2, size // 2 - 2), "AI", fill=(255, 255, 255, 255), anchor="mm")
    return image


def main() -> None:
    backend = Backend()
    if not os.path.isfile(backend.backend_exe):
        try:
            import tkinter.messagebox as messagebox

            messagebox.showerror(
                APP_NAME,
                f"Không tìm thấy backend tại:\n{backend.backend_exe}\nHãy cài lại từ Setup.exe.",
            )
        except Exception:
            pass
        return

    backend.start_server()
    backend.start_p2t()
    ready = backend.wait_ready()

    stop_event = threading.Event()

    def open_app() -> None:
        webbrowser.open(backend.url)

    def restart() -> None:
        backend.stop()
        backend.port = find_port(DEFAULT_BACKEND_PORT)
        backend.start_server()
        backend.start_p2t()
        if backend.wait_ready():
            webbrowser.open(backend.url)

    def quit_app(icon: object) -> None:
        backend.stop()
        try:
            icon.stop()  # type: ignore[attr-defined]
        except Exception:
            pass
        stop_event.set()

    if ready:
        open_app()
    else:
        try:
            import tkinter.messagebox as messagebox

            messagebox.showwarning(
                APP_NAME,
                "Backend khởi động quá lâu. Hãy thử chạy lại app.",
            )
        except Exception:
            pass

    try:
        import pystray

        menu = pystray.Menu(
            pystray.MenuItem("Mở bảng dạy", lambda icon: open_app(), default=True),
            pystray.MenuItem("Khởi động lại backend", lambda icon: restart()),
            pystray.MenuItem("Thoát", quit_app),
        )
        icon = pystray.Icon(APP_NAME, make_icon(), APP_NAME, menu)
        icon.run()
    except Exception:
        # Không có tray (thiếu lib): giữ tiến trình sống tới khi bị tắt.
        try:
            stop_event.wait()
        except KeyboardInterrupt:
            pass
        finally:
            backend.stop()


if __name__ == "__main__":
    main()
