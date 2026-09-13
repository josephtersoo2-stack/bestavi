import ctypes
import subprocess
import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright

pw = sync_playwright().start()
node_pid = pw._impl_obj._connection._transport._proc.pid

cmd = f"(Get-Process -Id {node_pid}).Threads[0].Id"
tid = int(subprocess.check_output(["powershell", "-Command", cmd]).decode().strip())

user32 = ctypes.windll.user32
hDesk = user32.GetThreadDesktop(tid)
buf = ctypes.create_unicode_buffer(256)
needed = ctypes.c_int(0)
user32.GetUserObjectInformationW(hDesk, 2, buf, 512, ctypes.byref(needed))
print(f"Node PID {node_pid} Desktop: {buf.value}")

pw.stop()
