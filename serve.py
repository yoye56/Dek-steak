"""Start one Python web instance behind the hosting provider's HTTPS proxy."""
import os
from pathlib import Path
import subprocess
import sys


def main():  # ตรวจพื้นที่ข้อมูลถาวรและพอร์ต ก่อนเปิดเว็บสำหรับโฮสต์
    data = os.environ.get('DEK_STEAK_DATA', '').strip()
    if not data or not Path(data).is_absolute():
        print('Set DEK_STEAK_DATA to an absolute path on your persistent disk.', file=sys.stderr)
        return 1
    try:
        port = int(os.environ.get('PORT', '8501'))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        print('PORT must be an integer from 1 to 65535.', file=sys.stderr)
        return 1
    root = Path(__file__).resolve().parent
    return subprocess.call([
        sys.executable, '-m', 'streamlit', 'run', str(root / 'app.py'),
        '--server.address', '0.0.0.0', '--server.port', str(port),
        '--server.headless', 'true', '--server.enableXsrfProtection', 'true',
        '--server.enableCORS', 'true', '--browser.gatherUsageStats', 'false',
    ], cwd=root)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nStopped.')
