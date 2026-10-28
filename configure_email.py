"""Local Gmail setup. Never prints secrets or accepts an app password as a CLI argument."""
import argparse
import getpass
import json
import os
import tempfile
import re
import sys
import tomllib
from pathlib import Path
from core import Store, RuleError
from password_reset import SMTPMailer, load_mail_config

ROOT=Path(__file__).resolve().parent


def save_gmail(path,email,password):  # ตรวจ App Password และบันทึกส่วน SMTP โดยรักษาค่าอื่นและแทนไฟล์แบบ atomic
    email=Store.email(email)
    password=password.replace(' ','').strip()
    if not re.fullmatch(r'[A-Za-z0-9]{16}',password):
        raise RuleError('กรุณาใช้ App Password 16 ตัวอักษรจาก Google')
    config={'DEK_SMTP_HOST':'smtp.gmail.com','DEK_SMTP_PORT':'587','DEK_SMTP_SECURITY':'starttls',
            'DEK_SMTP_USERNAME':email,'DEK_SMTP_PASSWORD':password,'DEK_SMTP_FROM':email}
    previous=path.read_text(encoding='utf-8') if path.exists() else ''
    try: tomllib.loads(previous)
    except tomllib.TOMLDecodeError:
        raise RuleError('ไฟล์ secrets.toml เดิมมีรูปแบบผิด กรุณาแก้ก่อนตั้งค่าอีเมล') from None
    block='[smtp]\n'+''.join(key+' = '+json.dumps(value,ensure_ascii=False)+'\n' for key,value in config.items())
    if re.search(r'(?m)^\[smtp\][^\n]*$',previous):
        updated=re.sub(r'(?ms)^\[smtp\][^\n]*\n.*?(?=^\[|\Z)',lambda _:block+'\n',previous)
    else: updated=previous.rstrip()+'\n\n'+block
    try: tomllib.loads(updated)
    except tomllib.TOMLDecodeError: raise RuleError('อัปเดตส่วน smtp ไม่สำเร็จ ไฟล์เดิมยังคงอยู่') from None
    path.parent.mkdir(parents=True,exist_ok=True)
    # Unique, exclusively created temp file; POSIX mode 0600, inherited ACL on Windows.
    descriptor,temp_name=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.tmp',dir=path.parent)
    temp=Path(temp_name)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8') as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def main():  # รับค่าผู้ส่งแบบซ่อนรหัสและเลือกตรวจหรือทดสอบ SMTP
    parser=argparse.ArgumentParser(description='ตั้งค่า Gmail ของ Dek Steak ในเครื่อง')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--check',action='store_true',help='ตรวจการเชื่อมต่อโดยไม่ส่งอีเมล')
    group.add_argument('--test',action='store_true',help='ส่งอีเมลทดสอบไปยังผู้รับที่กรอกเอง')
    args=parser.parse_args()
    path=ROOT/'.streamlit'/'secrets.toml'
    try:
        if not args.check and not args.test:
            print('เปิดการยืนยันตัวตนสองขั้นตอน และสร้าง Google App Password สำหรับ Dek Steak ก่อน')
            email=input('อีเมล Gmail ผู้ส่งของร้าน: ').strip()
            password=getpass.getpass('Google App Password (ซ่อนตัวอักษร): ')
            save_gmail(path,email,password)
            del password
            print('บันทึกผู้ส่งใน .streamlit/secrets.toml แล้ว ไฟล์นี้ไม่รวมใน ZIP')
        mailer=SMTPMailer(load_mail_config(path))
        mailer.check_connection()
        print('ผู้ให้บริการยอมรับการเชื่อมต่อและเข้าสู่ระบบ SMTP แล้ว')
        if args.test:
            recipient=Store.email(input('อีเมลผู้รับทดสอบ (Enter เพื่อใช้ผู้ส่ง): ').strip() or mailer.sender)
            mailer.send_test(recipient)
            print('ผู้ให้บริการรับอีเมลทดสอบแล้ว กรุณาตรวจ Inbox และ Spam ของผู้รับ')
        else:
            print('ทดสอบรับอีเมลด้วย: python configure_email.py --test')
        print('กลับหน้าเว็บแล้วรีเฟรช จากนั้นขอ OTP ด้วยอีเมลที่สมัครไว้')
        return 0
    except (RuleError,OSError) as error:
        print(str(error) if isinstance(error,RuleError) else 'อ่านหรือบันทึกไฟล์ตั้งค่าไม่สำเร็จ')
        return 1


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
