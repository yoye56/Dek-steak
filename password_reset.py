"""One-time email codes; credentials stay in environment variables or secrets."""
import hashlib
import hmac
import os
import secrets
import smtplib
import ssl
import time
import tomllib
import re
from pathlib import Path
from contextlib import contextmanager
from html import escape
from email.message import EmailMessage
from email.utils import parseaddr
from core import RuleError

MESSAGE = 'หากอีเมลนี้มีบัญชีอยู่ ระบบจะส่งรหัสให้ทางอีเมล กรุณาตรวจกล่องจดหมายและสแปม'


def load_mail_config(path=None):  # อ่านค่าจาก secrets.toml และ environment โดยไม่แสดงรหัสลับ
    path=Path(path) if path else Path(__file__).resolve().parent/'.streamlit'/'secrets.toml'
    config={}
    if path.exists():
        try:
            with path.open('rb') as stream: config.update(tomllib.load(stream).get('smtp',{}))
        except (tomllib.TOMLDecodeError,TypeError,ValueError,OSError):
            raise RuleError('อ่านการตั้งค่าอีเมลไม่ได้ กรุณาตรวจรูปแบบ .streamlit/secrets.toml') from None
    config.update({key:value for key,value in os.environ.items() if key.startswith('DEK_SMTP_')})
    return config


class SMTPMailer:  # ดูแลการเชื่อมต่อและส่งอีเมล ไม่ดูแลกฎ OTP
    def __init__(self, config=None):  # เตรียมค่าผู้ส่งอีเมล
        config = os.environ if config is None else config
        self.host = str(config.get('DEK_SMTP_HOST', '')).strip()
        self.username = str(config.get('DEK_SMTP_USERNAME', '')).strip()
        self.password = str(config.get('DEK_SMTP_PASSWORD', ''))
        self.sender = str(config.get('DEK_SMTP_FROM', '')).strip()
        self.port_text = str(config.get('DEK_SMTP_PORT', '587'))
        self.security = str(config.get('DEK_SMTP_SECURITY', 'starttls')).lower()
        if self.host.lower()=='smtp.gmail.com': self.password=self.password.replace(' ','')

    @property
    def configured(self):  # ตรวจว่าค่าผู้ส่งและรูปแบบการเชื่อมต่อครบตามที่รองรับ
        address=parseaddr(self.sender)[1]
        return bool(self.host and not re.search(r'\s',self.host) and self.username and self.password
                    and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',address)
                    and not re.search(r'[\r\n]',self.sender)
                    and self.security in ('starttls','ssl') and self.port_text.isdigit() and 1<=int(self.port_text)<=65535)

    @contextmanager
    def connection(self):  # เชื่อม SMTP ผ่าน TLS และล็อกอินโดยไม่เปิดเผยรายละเอียดลับเมื่อผิดพลาด
        if not self.configured:
            raise RuleError('การตั้งค่าอีเมลไม่ครบหรือไม่ถูกต้อง กรุณาตรวจผู้ส่ง พอร์ต และ TLS')
        context=ssl.create_default_context()
        connection=smtplib.SMTP_SSL if self.security=='ssl' else smtplib.SMTP
        options={'context':context} if self.security=='ssl' else {}
        try:
            with connection(self.host,int(self.port_text),timeout=15,**options) as smtp:
                if self.security=='starttls':
                    smtp.ehlo(); smtp.starttls(context=context); smtp.ehlo()
                smtp.login(self.username,self.password)
                yield smtp
        except smtplib.SMTPAuthenticationError:
            raise RuleError('ผู้ให้บริการไม่ยอมรับบัญชีผู้ส่ง กรุณาตรวจ Gmail App Password และการยืนยันตัวตนสองขั้นตอน') from None
        except (smtplib.SMTPException,OSError):
            raise RuleError('เชื่อมต่อบริการอีเมลไม่สำเร็จ กรุณาตรวจการตั้งค่าและเครือข่าย') from None

    def check_connection(self):  # ทดสอบเชื่อมต่อและล็อกอิน SMTP โดยไม่ส่งอีเมล
        with self.connection(): pass

    def send_test(self,email):  # ส่งอีเมลทดสอบการตั้งค่า ซึ่งไม่ใช่ OTP
        message=EmailMessage()
        message['From']=self.sender; message['To']=email
        message['Subject']='Dek Steak • ทดสอบการส่งอีเมล'
        message.set_content('ระบบ Dek Steak ส่งอีเมลทดสอบสำเร็จ\nข้อความนี้ไม่มี OTP และไม่เปลี่ยนรหัสผ่าน\nกรุณาทดลองขอ OTP จากหน้าเข้าสู่ระบบด้วยอีเมลที่สมัครไว้')
        with self.connection() as smtp:
            if smtp.send_message(message): raise RuleError('ผู้ให้บริการปฏิเสธอีเมลผู้รับ')

    def send_code(self, email, code):  # ส่ง OTP ทางอีเมลทั้งรูปแบบข้อความและ HTML
        if not self.configured or self.security not in ('starttls', 'ssl'):
            raise RuleError('ยังไม่ได้ตั้งค่าบริการส่งอีเมลอย่างครบถ้วน')
        message = EmailMessage()
        message['From'] = self.sender
        message['To'] = email
        message['Subject'] = 'Dek Steak • รหัสสำหรับตั้งรหัสผ่านใหม่'
        message.set_content(f'รหัสยืนยันของคุณคือ {code}\n\nรหัสมีอายุ 10 นาทีและใช้ได้ครั้งเดียว\n'
                            'หากคุณไม่ได้ขอเปลี่ยนรหัสผ่าน ไม่ต้องดำเนินการใด ๆ และอย่าเปิดเผยรหัสนี้ให้ผู้อื่น\n\nDek Steak')
        message.add_alternative(f'''<html lang="th"><body style="margin:0;background:#f6f1e9;font-family:Tahoma,Arial,sans-serif;color:#35281f;padding:32px 16px">
        <div style="max-width:480px;margin:auto;padding:32px;background:#fff;border-radius:20px;border-top:5px solid #e66b27">
        <h1 style="margin:0 0 24px;font-size:24px">DEK STEAK</h1><h2 style="font-size:18px">รหัสยืนยันสำหรับตั้งรหัสผ่านใหม่</h2>
        <p>นำรหัสนี้ไปกรอกที่หน้าลืมรหัสผ่าน</p><div style="padding:20px;text-align:center;background:#fff1e2;border-radius:12px;font-size:32px;font-weight:bold;letter-spacing:5px;color:#a0471c">{escape(code)}</div>
        <p>รหัสมีอายุ 10 นาที และใช้ได้ครั้งเดียว</p><p style="font-size:12px;color:#735f50">หากคุณไม่ได้ขอเปลี่ยนรหัสผ่าน ให้ข้ามอีเมลนี้ และอย่าเปิดเผย OTP ให้ผู้อื่น</p></div></body></html>''',subtype='html')
        with self.connection() as smtp:
            if smtp.send_message(message): raise RuleError('ผู้ให้บริการปฏิเสธอีเมลผู้รับ')


class ResetService:  # ดูแลอายุ OTP จำกัดการขอและการเปลี่ยนรหัสผ่าน
    def __init__(self, store, mailer):  # รับ Store และตัวส่งอีเมล แล้วเตรียมตาราง OTP
        self.store = store
        self.mailer = mailer
        with store.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS password_reset_codes(
              email TEXT PRIMARY KEY, digest TEXT NOT NULL, salt TEXT NOT NULL,
              expires INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
              auth_version INTEGER, requested INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS password_reset_requests(
              id INTEGER PRIMARY KEY, email TEXT NOT NULL, created INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS reset_request_email_time
              ON password_reset_requests(email,created);
            ''')

    @staticmethod
    def digest(code, salt):  # สร้าง hash ของ OTP ร่วมกับ salt เพื่อไม่เก็บรหัสยืนยันตรง ๆ
        return hashlib.pbkdf2_hmac('sha256', code.encode(), bytes.fromhex(salt), 100000).hex()

    def request(self, email):  # จำกัดการขอ สร้าง OTP อายุ 10 นาที และส่งเฉพาะบัญชีที่มีอยู่
        email = self.store.email(email)
        if not self.mailer.configured:
            raise RuleError('ร้านยังไม่ได้เปิดบริการส่งอีเมล กรุณาลองใหม่เมื่อร้านตั้งค่าเสร็จ')
        now = int(time.time())
        code = f'{secrets.randbelow(100000000):08}'
        salt = secrets.token_hex(16)
        digest = self.digest(code, salt)
        with self.store.tx() as c:
            recent = c.execute('SELECT created FROM password_reset_requests WHERE email=? ORDER BY created DESC LIMIT 1', (email,)).fetchone()
            count = c.execute('SELECT count(*) FROM password_reset_requests WHERE email=? AND created>?', (email, now-86400)).fetchone()[0]
            total = c.execute('SELECT count(*) FROM password_reset_requests WHERE created>?', (now-3600,)).fetchone()[0]
            if (recent and now-recent['created'] < 60) or count >= 6 or total >= 100:
                raise RuleError('ขอรหัสหลายครั้งเกินไป กรุณารอแล้วลองใหม่ภายหลัง')
            user = c.execute('SELECT id,auth_version FROM users WHERE email=? AND active=1', (email,)).fetchone()
            c.execute('INSERT INTO password_reset_requests(email,created) VALUES(?,?)', (email, now))
            c.execute('INSERT OR REPLACE INTO password_reset_codes(email,digest,salt,expires,attempts,auth_version,requested) VALUES(?,?,?,?,0,?,?)',
                      (email, digest, salt, now+600, user['auth_version'] if user else None, now))
            c.execute('DELETE FROM password_reset_requests WHERE created<?', (now-172800,))
            c.execute('DELETE FROM password_reset_codes WHERE expires<?', (now-86400,))
        if user:
            try:
                self.mailer.send_code(email, code)
            except Exception:
                # Never expose provider errors or credentials, and never keep an undelivered code valid.
                with self.store.tx() as c:
                    c.execute('UPDATE password_reset_codes SET expires=0 WHERE email=? AND digest=?', (email, digest))
                    self.store.log(c, user['id'], None, 'password_reset_delivery_failed')
        return MESSAGE

    def complete(self, email, code, new_password):  # ตรวจ OTP อายุ จำนวนลองและเวอร์ชันบัญชีก่อนเปลี่ยนรหัสและลบ OTP
        email = self.store.email(email)
        encoded = self.store.hash_password(new_password)
        now = int(time.time())
        success = False
        with self.store.tx() as c:
            row = c.execute('SELECT * FROM password_reset_codes WHERE email=?', (email,)).fetchone()
            user = c.execute('SELECT id,auth_version FROM users WHERE email=? AND active=1', (email,)).fetchone()
            if row and row['expires'] > now and row['attempts'] < 5:
                candidate = self.digest(str(code).strip(), row['salt'])
                valid = hmac.compare_digest(candidate, row['digest'])
                if valid and user and row['auth_version'] == user['auth_version']:
                    c.execute('UPDATE users SET password=?,auth_version=auth_version+1 WHERE id=?', (encoded, user['id']))
                    c.execute('DELETE FROM password_reset_codes WHERE email=?', (email,))
                    c.execute('DELETE FROM login_attempts WHERE email=?', (email,))
                    self.store.log(c, user['id'], None, 'email_password_reset')
                    success = True
                else:
                    c.execute('UPDATE password_reset_codes SET attempts=attempts+1 WHERE email=?', (email,))
        if not success:
            raise RuleError('รหัสไม่ถูกต้อง หมดอายุ หรือใช้แล้ว กรุณาตรวจรหัสหรือขอรหัสใหม่')
