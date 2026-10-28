"""Local-only owner setup and recovery. Never exposed as a web endpoint."""
import argparse
import getpass
import time
from core import Store, RuleError


def password_prompt():  # รับรหัสผ่านแบบซ่อนและให้พิมพ์ยืนยันก่อนใช้
    password=getpass.getpass('Password (10-128 characters): ')
    if password!=getpass.getpass('Confirm password: '):
        raise RuleError('Passwords do not match')
    return password


def setup_owner(store=None):  # สร้างบัญชีเจ้าของผ่านคำสั่งในเครื่อง ไม่เปิดสมัครสิทธิ์นี้ผ่านเว็บ
    store=store or Store()
    if store.query("SELECT id FROM users WHERE role='owner'"):
        print('Owner account already exists.'); return
    print('\nCreate the restaurant owner account. This account can manage all orders.\n')
    email=input('Owner email: ').strip()
    name=input('Owner name: ').strip()
    store.register(email,name,password_prompt(),role='owner',local=True)
    print('Owner created. Log in with your email and password.')


def main():  # รับคำสั่งสร้างหรือรีเซ็ตรหัสบัญชีเจ้าของอย่างจำกัดสิทธิ์
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['setup-owner','reset-owner'])
    args=parser.parse_args()
    store=Store()
    try:
        if args.command=='setup-owner': setup_owner(store)
        else:
            email=store.email(input('Existing owner email: '))
            encoded=store.hash_password(password_prompt())
            with store.tx() as c:
                u=c.execute("SELECT id FROM users WHERE email=? AND role='owner'",(email,)).fetchone()
                if not u: raise RuleError('Owner not found')
                c.execute('UPDATE users SET password=?,auth_version=auth_version+1 WHERE id=?',(encoded,u['id']))
                c.execute('DELETE FROM login_attempts WHERE email=?',(email,))
                store.log(c,u['id'],None,'owner_password_reset')
            print('Password updated.')
    except RuleError as e:
        print(str(e)); return 1
    return 0

if __name__=='__main__': raise SystemExit(main())


# คำสั่งสร้างหรือรีเซ็ตรหัสบัญชีเจ้าของในเครื่อง รับรหัสผ่านแบบซ่อนตัวอักษร