"""Python launcher: creates isolated environment, installs, sets owner and runs."""
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parent


def main():  # ตรวจสภาพแวดล้อม เตรียม dependencies และเปิดเว็บในเครื่อง
    os.chdir(ROOT)
    if sys.version_info < (3,11):
        print('Please install Python 3.11 or newer.'); return 1
    env=ROOT/'.venv'
    py=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not (ROOT/'requirements.txt').is_file():
        print('requirements.txt not found. Keep it in the same folder as deksteak.py.'); return 1
    requirements=(ROOT/'requirements.txt').read_text(encoding='utf-8')
    stamp=env/'.dek-installed'
    if not py.exists():
        print('1/3 Creating isolated Python environment ...')
        venv.EnvBuilder(with_pip=True).create(env)
    if not stamp.exists() or stamp.read_text(encoding='utf-8')!=requirements:
        print('2/3 Installing dependencies. Internet is required on the first run ...')
        subprocess.run([str(py),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
        stamp.write_text(requirements,encoding='utf-8')
    print('3/3 Checking owner account ...')
    subprocess.run([str(py),str(ROOT/'manage.py'),'setup-owner'],check=True)
    print('\nOpening dek steak at http://localhost:8501\nKeep this window open. Press Ctrl+C to stop.\n')
    return subprocess.call([str(py),'-m','streamlit','run',str(ROOT/'app.py'),'--server.address','127.0.0.1'])

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,subprocess.CalledProcessError) as e:
        print('Unable to start:',e)
        print('Check your Internet connection and Python installation, then run again.')
        input('Press Enter to close ...')
        raise SystemExit(1)
    except KeyboardInterrupt:
        print('\nStopped.')

#ตรวจ Python เตรียม virtual environment และ dependencies ช่วยตั้งบัญชีเจ้าของ แล้วเปิดเว็บในเครื่อง 