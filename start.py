"""Canonical entry point matching the installation guide."""
from deksteak import main
import subprocess

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nStopped.')
    except (OSError, subprocess.CalledProcessError) as error:
        print('Unable to start:', error)
        print('Check Python and your Internet connection, then run again.')
        raise SystemExit(1)
    
#จุดเริ่มสำหรับผู้ใช้ เรียกตัวเตรียมและเปิดระบบ