import sys
import subprocess
import re

def kill_ports(ports=(8000, 5173)):
    """Kills any process listening on the specified ports using netstat and taskkill."""
    try:
        out = subprocess.check_output(['netstat', '-ano'], text=True, errors='ignore')
        pids = set()
        for line in out.splitlines():
            for port in ports:
                if f":{port} " in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) > 4:
                            pids.add(int(pid))
        for pid in pids:
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True)
                print(f"[clean_services] Terminated PID {pid} listening on port")
            except Exception:
                pass
    except Exception as e:
        print(f"[clean_services] Error checking ports: {e}")

def kill_orphaned_browsers():
    """Kills any orphaned Playwright chromium processes."""
    try:
        cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq \'chrome.exe\' -and ($_.CommandLine -match \'playwright\' -or $_.CommandLine -match \'--remote-debugging-pipe\') } | Select-Object -ExpandProperty ProcessId"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        for line in res.stdout.splitlines():
            pid = line.strip()
            if pid.isdigit() and int(pid) > 4:
                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                print(f"[clean_services] Terminated orphaned chrome PID {pid}")
    except Exception:
        pass

if __name__ == '__main__':
    kill_ports()
    kill_orphaned_browsers()
