"""dek steak domain service. All money is integer satang; SQL is internal storage."""
from __future__ import annotations
import csv
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
import time
from itertools import groupby
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError

BANGKOK = timezone(timedelta(hours=7))
ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('DEK_STEAK_DATA', str(ROOT / 'data'))).resolve()
STATUSES = {'awaiting_payment':'รอชำระเงิน','submitted':'รอตรวจสอบเงิน','paid':'ชำระแล้ว','preparing':'กำลังปรุง','served':'เสิร์ฟแล้ว','completed':'จบรายการ','cancelled':'ยกเลิก'}
ACTIVE = ('awaiting_payment','submitted','paid','preparing','served')
PENDING_PAYMENT = ('awaiting_payment','submitted')
DONENESS = ('ไม่ระบุ','Rare','Medium Rare','Medium','Well Done')
SAUCES = ('เกรวี่','พริกไทยดำ','บาร์บีคิว','ไม่ใส่ซอส')
DRINK_OPTIONS = {'ชาเย็น':('ไม่หวาน (0%)','หวานน้อย (25%)','หวานกลาง (50%)','หวานปกติ (100%)'),
                 'น้ำเปล่า':('เย็น','ไม่เย็น')}
LOGIN_FAIL='อีเมลหรือรหัสผ่านไม่ถูกต้อง'


def item_options(item):  # รวมตัวเลือกอาหารเป็นข้อความสำหรับแสดงรายละเอียด
    parts=[]
    if item.get('doneness','ไม่ระบุ')!='ไม่ระบุ': parts.append('ความสุก: '+item['doneness'])
    if item.get('sauce','ไม่ใส่ซอส')!='ไม่ใส่ซอส': parts.append('ซอส: '+item['sauce'])
    if item.get('drink_option'): parts.append(item['drink_option'])
    if item.get('note'): parts.append(item['note'])
    return ' · '.join(parts)

class RuleError(ValueError):  # ข้อผิดพลาดตามกฎร้านที่แสดงเป็นข้อความให้ผู้ใช้เข้าใจได้
    pass


def to_int(value,message):  # แปลงเป็นจำนวนเต็มอย่างเข้มงวดและแจ้งข้อความเมื่อข้อมูลไม่ถูกต้อง
    if type(value) is int: return value
    if isinstance(value,str) and re.fullmatch(r'[+-]?[0-9]+',value.strip()):
        try: return int(value.strip())
        except ValueError: pass
    raise RuleError(message)

def inclusive_totals(total):  # ราคาเมนูรวม VAT แล้ว แยกภาษีครั้งเดียวต่อบิลด้วยจำนวนเต็มสตางค์
    if type(total) is not int or total < 0:
        raise ValueError('Total must be nonnegative integer satang')
    vat=(total*7+53)//107
    return total-vat,vat,total


class ClosingConnection(sqlite3.Connection):  # connection ที่ปิดทรัพยากรหลังออกจาก with
    """Commit/rollback and release the file handle when a with block ends."""
    def __exit__(self, exc_type, exc_value, traceback):  # commit หรือ rollback ตามผลการทำงาน แล้วปิด connection เพื่อไม่ค้างไฟล์
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()

class Store:  # รวมกฎร้านและการอ่านเขียน SQLite แยกจากหน้าจอ
    def __init__(self, path=None):  # กำหนดตำแหน่งฐานข้อมูลและเตรียมโครงสร้างที่ต้องใช้
        self.path = Path(path) if path else DATA / 'dek_steak.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):  # เปิด SQLite พร้อม foreign keys และเวลารอเมื่อมีงานเขียนอื่น
        c = sqlite3.connect(self.path, timeout=15, factory=ClosingConnection)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA busy_timeout=15000')
        return c

    @contextmanager
    def tx(self):  # รวมคำสั่งเป็น transaction เดียว ล้มเหลวแล้ว rollback และปิด connection เสมอ
        c = self.connect()
        try:
            c.execute('BEGIN IMMEDIATE')  # ล็อกงานเขียนก่อนตรวจและบันทึก ป้องกันคำขอแย่งโต๊ะพร้อมกัน
            yield c
            c.commit()  # ยืนยันการเปลี่ยนข้อมูลทุกคำสั่งใน transaction นี้
        except Exception:
            c.rollback()  # ย้อนการเปลี่ยนทั้งหมดเมื่อเกิดข้อผิดพลาด
            raise
        finally:
            c.close()  # คืนทรัพยากรและไม่ปล่อย connection ค้าง

    def query(self, sql, args=()):  # อ่าน SQL ด้วยพารามิเตอร์และคืนแต่ละแถวเป็น dictionary
        with self.connect() as c:
            return [dict(r) for r in c.execute(sql, args).fetchall()]

    def initialize(self):  # สร้างตาราง เพิ่มโครงสร้างที่ขาดและเตรียมข้อมูลเริ่มต้น
        with self.connect() as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.executescript('''
            CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL,
              name TEXT NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('customer','owner')),
              active INTEGER NOT NULL DEFAULT 1, auth_version INTEGER NOT NULL DEFAULT 1, created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS login_attempts(email TEXT PRIMARY KEY, failures INTEGER NOT NULL, locked_until INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS dining_tables(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, seats INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS menu(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
              description TEXT NOT NULL, price INTEGER NOT NULL CHECK(price>0), available INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assets(key TEXT PRIMARY KEY, data BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
              table_id INTEGER REFERENCES dining_tables(id), guests INTEGER NOT NULL,
              subtotal INTEGER NOT NULL, vat INTEGER NOT NULL, total INTEGER NOT NULL,
              status TEXT NOT NULL DEFAULT 'awaiting_payment', payment_method TEXT,
              created INTEGER NOT NULL, paid_at INTEGER, completed_at INTEGER,
              request_key TEXT UNIQUE NOT NULL, note TEXT NOT NULL DEFAULT '', payment_snapshot TEXT NOT NULL DEFAULT '',
              cancel_reason TEXT NOT NULL DEFAULT '', payment_feedback TEXT NOT NULL DEFAULT '', awaiting_since INTEGER NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_table ON orders(table_id)
              WHERE status IN ('awaiting_payment','submitted','paid','preparing','served');
            CREATE INDEX IF NOT EXISTS awaiting_expiry ON orders(status,awaiting_since);
            CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
              menu_id INTEGER NOT NULL REFERENCES menu(id), name TEXT NOT NULL, price INTEGER NOT NULL,
              quantity INTEGER NOT NULL CHECK(quantity>0), doneness TEXT NOT NULL, sauce TEXT NOT NULL, note TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS slips(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
              data BLOB NOT NULL, digest TEXT UNIQUE NOT NULL, created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor INTEGER REFERENCES users(id),
              order_id INTEGER REFERENCES orders(id), action TEXT NOT NULL, detail TEXT NOT NULL, created INTEGER NOT NULL);
            ''')
            self.migrate_fulfillment(c)
            if 'parent_order_id' not in {row['name'] for row in c.execute('PRAGMA table_info(orders)')}:
                c.execute('ALTER TABLE orders ADD COLUMN parent_order_id INTEGER REFERENCES orders(id)')
            c.execute('CREATE INDEX IF NOT EXISTS order_parent ON orders(parent_order_id)')
            if 'vat_included' not in {row['name'] for row in c.execute('PRAGMA table_info(orders)')}:
                # บิลเดิมคงยอดและวิธีคิดเดิม บิลใหม่ระบุรวม VAT ตอน INSERT เท่านั้น
                c.execute('ALTER TABLE orders ADD COLUMN vat_included INTEGER NOT NULL DEFAULT 0 CHECK(vat_included IN (0,1))')
            if 'drink_option' not in {row['name'] for row in c.execute('PRAGMA table_info(order_items)')}:
                c.execute("ALTER TABLE order_items ADD COLUMN drink_option TEXT NOT NULL DEFAULT ''")
            if not c.execute('SELECT 1 FROM menu').fetchone():
                items = [
                    ('Ribeye Steak','สเต๊กเนื้อ','ริบอายย่าง เสิร์ฟพร้อมเฟรนช์ฟรายส์และสลัด',28900),
                    ('Pork Chop','สเต๊กหมู','พอร์กชอปย่างซอสพริกไทยดำ',14900),
                    ('Chicken Steak','สเต๊กไก่','อกไก่ย่างพร้อมผักและมันฝรั่ง',11900),
                    ('Salmon Steak','สเต๊กปลา','แซลมอนย่างพร้อมสลัด',24900),
                    ('Spaghetti Carbonara','พาสต้า','คาโบนาราซอสครีม',13900),
                    ('French Fries','ของทานเล่น','เฟรนช์ฟรายส์ทอดใหม่',5900),
                    ('Caesar Salad','สลัด','ซีซาร์สลัด',8900),
                    ('น้ำเปล่า','เครื่องดื่ม','น้ำดื่มขวด',1500),
                    ('ชาเย็น','เครื่องดื่ม','ชาไทยเย็น',4500),
                ]
                c.executemany('INSERT INTO menu(name,category,description,price) VALUES(?,?,?,?)', items)
            if not c.execute('SELECT 1 FROM dining_tables').fetchone():
                c.executemany('INSERT INTO dining_tables(name,seats) VALUES(?,?)', [(f'T{i:02}', 2 if i<=4 else 4 if i<=8 else 6) for i in range(1,11)])
            c.executemany('INSERT OR IGNORE INTO settings VALUES(?,?)', [('shop_name','dek steak'),('bank_details',''),('accepting_orders','1'),('payment_minutes','30')])

    def migrate_fulfillment(self,c):  # ปรับฐานข้อมูลรุ่นเก่าให้รองรับกลับบ้านโดยรักษาความสัมพันธ์ของข้อมูล
        columns={row['name']:row for row in c.execute('PRAGMA table_info(orders)')}
        rebuild=bool(columns['table_id']['notnull'])
        missing=[name for name in ('fulfillment','pickup_name','pickup_phone') if name not in columns]
        if not rebuild and not missing: return
        if rebuild:
            # Keep a private recoverable snapshot before changing the legacy table layout.
            snapshot=self.path.with_name(self.path.stem+'.before-takeaway.sqlite3')
            if not snapshot.exists():
                target=sqlite3.connect(snapshot)
                try: c.backup(target)
                finally: target.close()
        c.commit()  # ยืนยันการเปลี่ยนข้อมูลทุกคำสั่งใน transaction นี้
        c.execute('PRAGMA foreign_keys=OFF')
        try:
            c.execute('BEGIN IMMEDIATE')  # ล็อกงานเขียนก่อนตรวจและบันทึก ป้องกันคำขอแย่งโต๊ะพร้อมกัน
            columns={row['name']:row for row in c.execute('PRAGMA table_info(orders)')}
            rebuild=bool(columns['table_id']['notnull'])
            missing=[name for name in ('fulfillment','pickup_name','pickup_phone') if name not in columns]
            if rebuild:
                schema=c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='orders'").fetchone()[0]
                indexes=[r['sql'] for r in c.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='orders' AND sql IS NOT NULL")]
                schema=re.sub(r'^CREATE TABLE ["]?orders["]?', 'CREATE TABLE orders_upgrade',schema,flags=re.I)
                schema=re.sub(r'table_id INTEGER NOT NULL', 'table_id INTEGER',schema,flags=re.I)
                c.execute(schema)
                fields=','.join('"'+name+'"' for name in columns)
                c.execute(f'INSERT INTO orders_upgrade({fields}) SELECT {fields} FROM orders')
                c.execute('DROP TABLE orders')
                c.execute('ALTER TABLE orders_upgrade RENAME TO orders')
                for sql in indexes:c.execute(sql)
            for name in missing:
                default='dine_in' if name=='fulfillment' else ''
                c.execute(f"ALTER TABLE orders ADD COLUMN {name} TEXT NOT NULL DEFAULT '{default}'")
            if c.execute('PRAGMA foreign_key_check').fetchone(): raise RuleError('ตรวจฐานข้อมูลหลังอัปเดตไม่ผ่าน')
            c.commit()  # ยืนยันการเปลี่ยนข้อมูลทุกคำสั่งใน transaction นี้
        except Exception:
            c.rollback();raise
        finally:c.execute('PRAGMA foreign_keys=ON')

    @staticmethod
    def hash_password(password):  # สร้าง salt และ hash รหัสด้วย PBKDF2 ไม่เก็บรหัสผ่านเดิม
        if not isinstance(password,str) or not 10 <= len(password) <= 128:
            raise RuleError('รหัสผ่านต้องมีความยาว 10–128 ตัวอักษร')
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()
        return f'310000${salt}${digest}'

    @staticmethod
    def verify_password(password, encoded):  # คำนวณ hash จากรหัสที่กรอกแล้วเปรียบเทียบอย่างเหมาะสม
        try:
            iterations, salt, digest = encoded.split('$')
            candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations)).hex()
            return hmac.compare_digest(candidate, digest)
        except (ValueError, AttributeError, TypeError):
            return False

    @staticmethod
    def email(value):  # ตัดช่องว่าง แปลงอีเมลเป็นตัวเล็กและตรวจรูปแบบ
        value = value.strip().lower()
        if len(value)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):
            raise RuleError('กรุณากรอกอีเมลให้ถูกต้อง')
        return value

    @staticmethod
    def gmail_email(value):  # บังคับโดเมน Gmail สำหรับสมัครและเข้าสู่ระบบ โดยไม่เปลี่ยนกฎอีเมล SMTP
        email = Store.email(value)
        if email.rsplit('@', 1)[1] != 'gmail.com':
            raise RuleError('กรุณาใช้อีเมลที่ลงท้ายด้วย @gmail.com เท่านั้น')
        return email

    def register(self,email,name,password,role='customer',local=False):  # ตรวจชื่อ อีเมลและรหัส แล้วสร้างบัญชีโดยจำกัดสิทธิ์เจ้าของ
        if role != 'customer' and not local:
            raise RuleError('ไม่สามารถสมัครบัญชีเจ้าของร้านผ่านหน้าเว็บ')
        email = self.gmail_email(email)
        name = name.strip()
        if not 1 <= len(name) <= 80:
            raise RuleError('ชื่อควรมีความยาว 1–80 ตัวอักษร')
        encoded = self.hash_password(password)
        try:
            with self.tx() as c:
                if role == 'owner' and c.execute("SELECT 1 FROM users WHERE role='owner'").fetchone():
                    raise RuleError('มีบัญชีเจ้าของร้านแล้ว ใช้คำสั่ง reset-owner หากลืมรหัสผ่าน')
                cur = c.execute('INSERT INTO users(email,name,password,role,created) VALUES(?,?,?,?,?)',(email,name,encoded,role,int(time.time())))
                return cur.lastrowid
        except sqlite3.IntegrityError:
            raise RuleError('อีเมลนี้ถูกใช้แล้ว') from None

    def authenticate(self,email,password):  # ตรวจรหัสและสถานะบัญชี พร้อมจำกัดการลองผิด
        try:
            email = self.email(email)
        except (RuleError,AttributeError,TypeError):
            raise RuleError(LOGIN_FAIL) from None
        email = self.gmail_email(email)  # ตรวจโดเมนก่อนค้นบัญชีหรือเทียบรหัส ไม่ยกเว้นบัญชีเดิม
        if not isinstance(password,str): raise RuleError(LOGIN_FAIL)
        now = int(time.time())
        with self.tx() as c:
            a = c.execute('SELECT * FROM login_attempts WHERE email=?',(email,)).fetchone()
            if a and a['locked_until']>now:
                raise RuleError('ลองเข้าสู่ระบบหลายครั้ง กรุณารอ 15 นาที')
            user = c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            encoded = user['password'] if user else '310000$'+'00'*16+'$'+'00'*32
            valid = self.verify_password(password,encoded)
            if not user or not valid or not user['active']:
                failures = (a['failures'] if a and a['locked_until']==0 else 0)+1
                c.execute('INSERT OR REPLACE INTO login_attempts VALUES(?,?,?)',(email,failures,now+900 if failures>=5 else 0))
                result = None
            else:
                c.execute('DELETE FROM login_attempts WHERE email=?',(email,))
                result = {k:user[k] for k in ('id','email','name','role','auth_version')}
        if result is None:
            raise RuleError(LOGIN_FAIL)
        return result

    def user(self,uid):  # อ่านเฉพาะข้อมูลบัญชีที่จำเป็นโดยไม่คืน hash รหัสผ่าน
        rows = self.query('SELECT id,email,name,role,active,auth_version FROM users WHERE id=?',(uid,))
        return rows[0] if rows else None

    def require(self,c,uid,owner=False):  # ตรวจบัญชีที่ใช้งานได้และสิทธิ์เจ้าของเมื่องานนั้นกำหนด
        u = c.execute('SELECT * FROM users WHERE id=? AND active=1',(uid,)).fetchone()
        if not u or (owner and u['role']!='owner'):
            raise RuleError('ไม่มีสิทธิ์ดำเนินการ')
        return u

    def require_order(self,c,uid,oid,owner=False):  # ตรวจว่ามีสิทธิ์ดูหรือดำเนินการกับออเดอร์นี้
        u = self.require(c,uid,owner)
        o = c.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
        if not o or (u['role']!='owner' and o['user_id']!=uid):
            raise RuleError('ไม่พบรายการหรือไม่มีสิทธิ์')
        return o

    @staticmethod
    def log(c,uid,oid,action,detail=''):  # บันทึกผู้ดำเนินการ เวลา ออเดอร์และเหตุการณ์ใน audit
        c.execute('INSERT INTO audit(actor,order_id,action,detail,created) VALUES(?,?,?,?,?)',(uid,oid,action,detail,int(time.time())))

    def settings(self):  # อ่านค่าตั้งร้านเป็น dictionary
        return {r['key']:r['value'] for r in self.query('SELECT * FROM settings')}

    def featured_ids(self):  # อ่านรหัสเมนูแนะนำที่ยังใช้แสดงได้
        saved=self.settings().get('featured_menu')
        if saved is not None:
            return json.loads(saved)
        priority={'Ribeye Steak':0,'Pork Chop':1,'Chicken Steak':2,'Salmon Steak':3,'Spaghetti Carbonara':4}
        items=sorted(self.menu(),key=lambda item:priority.get(item['name'],99))
        photo_keys={row['key'] for row in self.query('SELECT key FROM assets WHERE key LIKE ?',('menu_photo_%',))}
        return [item['id'] for item in items if item['available'] and item['category']!='เครื่องดื่ม' and f'menu_photo_{item["id"]}' in photo_keys][:5]

    def save_featured_menu(self,uid,ids):  # ตรวจสิทธิ์และความถูกต้องก่อนบันทึกเมนูแนะนำ
        with self.tx() as c:
            self.require(c,uid,True)
            if not isinstance(ids,list) or len(ids)>5 or any(type(mid) is not int for mid in ids) or len(set(ids))!=len(ids):
                raise RuleError('เลือกเมนูแนะนำไม่เกิน 5 เมนู และห้ามเลือกซ้ำ')
            for mid in ids:
                if not c.execute('SELECT 1 FROM menu WHERE id=?',(mid,)).fetchone() or not c.execute('SELECT 1 FROM assets WHERE key=?',(f'menu_photo_{mid}',)).fetchone():
                    raise RuleError('เมนูแนะนำต้องเป็นเมนูที่มีรูปอาหารแล้ว')
            encoded=json.dumps(ids)
            c.execute('INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)',('featured_menu',encoded))
            self.log(c,uid,None,'featured_menu_updated',encoded)

    def asset(self,key):  # อ่านรูปหนึ่งรายการจากฐานข้อมูลตาม key
        rows=self.query('SELECT data FROM assets WHERE key=?',(key,))
        return rows[0]['data'] if rows else None

    def assets(self,keys):  # อ่านรูปหลายรายการแบบกลุ่มเพื่อลดจำนวนคำสั่งฐานข้อมูล
        keys=list(dict.fromkeys(keys))
        result={}
        for offset in range(0,len(keys),500):
            batch=keys[offset:offset+500]
            marks=','.join('?' for _ in batch)
            result.update({row['key']:row['data'] for row in self.query(f'SELECT key,data FROM assets WHERE key IN ({marks})',batch)})
        return result

    def save_media(self,uid,key,data):  # ตรวจสิทธิ์ ชนิดรูปและปลายทางก่อนบันทึกภาพ
        if not re.fullmatch(r'menu_photo_[1-9][0-9]*|shop_photo_[1-4]',key):
            raise RuleError('ประเภทภาพไม่ถูกต้อง')
        clean=self.normalize_image(data) if data is not None else None
        with self.tx() as c:
            self.require(c,uid,True)
            if key.startswith('menu_photo_') and not c.execute('SELECT 1 FROM menu WHERE id=?',(int(key.removeprefix('menu_photo_')),)).fetchone():
                raise RuleError('ไม่พบเมนูที่ต้องการใส่รูป')
            if clean is None:
                c.execute('DELETE FROM assets WHERE key=?',(key,))
            else:
                c.execute('INSERT OR REPLACE INTO assets VALUES(?,?)',(key,clean))
            self.log(c,uid,None,'media_updated',key)

    def receipt_data(self,uid,oid):  # รวบรวมข้อมูลใบเสร็จเฉพาะบิลรับเงินแล้วและผู้ใช้มีสิทธิ์
        with self.connect() as c:
            order=self.require_order(c,uid,oid)
            if order['paid_at'] is None:
                raise RuleError('ยังไม่ได้รับการยืนยันชำระเงิน')
            result=dict(order)
            result['table_name']='สั่งกลับบ้าน' if order['fulfillment']=='takeaway' else c.execute('SELECT name FROM dining_tables WHERE id=?',(self.effective_table(c,order),)).fetchone()[0]
            result['customer']=c.execute('SELECT name FROM users WHERE id=?',(order['user_id'],)).fetchone()[0]
            result['shop_name']=c.execute("SELECT value FROM settings WHERE key='shop_name'").fetchone()[0]
            result['items']=[dict(r) for r in c.execute('SELECT * FROM order_items WHERE order_id=?',(oid,))]
            return result

    @staticmethod
    def normalize_image(data):  # ตรวจ JPEG/PNG ขนาดและจำนวนพิกเซล แล้วปรับรูปให้อยู่ในขอบเขต
        if not data or len(data)>5*1024*1024:
            raise RuleError('รูปต้องไม่เกิน 5 MB')
        try:
            with Image.open(io.BytesIO(data)) as im:
                if im.format not in ('JPEG','PNG') or im.width*im.height>16000000:
                    raise RuleError('รับเฉพาะรูป JPEG/PNG ขนาดไม่เกิน 16 ล้านพิกเซล')
                im.load()
                clean = ImageOps.exif_transpose(im).convert('RGB')
                clean.thumbnail((2000,2000))
                out = io.BytesIO()
                clean.save(out,format='PNG')
                return out.getvalue()
        except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning):
            raise RuleError('ไฟล์รูปภาพไม่ถูกต้อง') from None

    def save_settings(self,uid,name,bank,accepting,minutes,qr=None):  # บันทึกชื่อร้าน รายละเอียดรับเงิน การเปิดรับและเวลาชำระ
        minutes=to_int(minutes,'เวลาแจ้งชำระเงินต้องเป็นจำนวนเต็ม 5–120 นาที')
        if not name.strip() or len(name)>80 or len(bank)>1500 or not 5<=minutes<=120:
            raise RuleError('ข้อมูลร้านไม่ถูกต้อง')
        clean = self.normalize_image(qr) if qr is not None else None
        with self.tx() as c:
            self.require(c,uid,True)
            c.executemany('INSERT OR REPLACE INTO settings VALUES(?,?)',[('shop_name',name.strip()),('bank_details',bank.strip()),('accepting_orders',str(int(accepting))),('payment_minutes',str(int(minutes)))])
            if clean is not None:
                c.execute('INSERT OR REPLACE INTO assets VALUES(?,?)',('payment_qr',clean))
            self.log(c,uid,None,'settings_updated')

    def expire(self):  # ยกเลิกรายการรอชำระที่เกินเวลาเมื่อระบบเรียกตรวจ
        minutes = int(self.settings()['payment_minutes'])
        cutoff=int(time.time())-minutes*60
        if not self.query("SELECT 1 FROM orders WHERE status='awaiting_payment' AND awaiting_since<? LIMIT 1",(cutoff,)):
            return
        with self.tx() as c:
            minutes=int(c.execute("SELECT value FROM settings WHERE key='payment_minutes'").fetchone()[0])
            cutoff=int(time.time())-minutes*60
            rows=c.execute("SELECT id FROM orders WHERE status='awaiting_payment' AND awaiting_since<?",(cutoff,)).fetchall()
            for o in rows:
                c.execute("UPDATE orders SET status='cancelled',cancel_reason='หมดเวลาชำระเงิน' WHERE id=?",(o['id'],))
                self.log(c,None,o['id'],'expired')

    def tables(self):  # อ่านโต๊ะพร้อมสถานะจากทุกออเดอร์ที่ยังใช้งานรวมบิลสั่งเพิ่ม
        self.expire()
        return self.query("SELECT t.*,MIN(a.id) AS order_id FROM dining_tables t LEFT JOIN (SELECT o.id,COALESCE(o.table_id,p.table_id) AS table_id FROM orders o LEFT JOIN orders p ON p.id=o.parent_order_id WHERE o.status IN ('awaiting_payment','submitted','paid','preparing','served')) a ON a.table_id=t.id GROUP BY t.id ORDER BY t.id")

    def orderable_tables(self,uid):  # ระบุโต๊ะว่างและโต๊ะเดิมของลูกค้าที่จ่ายแล้วซึ่งสั่งเพิ่มได้
        """Free tables plus this customer's already-paid active dining table."""
        with self.connect() as c:
            self.require(c,uid)
            own={row[0] for row in c.execute("SELECT DISTINCT COALESCE(o.table_id,p.table_id) FROM orders o LEFT JOIN orders p ON p.id=o.parent_order_id WHERE o.user_id=? AND o.status IN ('paid','preparing','served') AND o.fulfillment='dine_in'",(uid,))}
        result=self.tables()
        for table in result:
            table['can_add']=table['id'] in own
        return result

    @staticmethod
    def effective_table(c,order):  # หาโต๊ะจริงจากบิลปัจจุบันหรือบิลหลักที่เชื่อมอยู่
        if order['table_id'] is not None:return order['table_id']
        if order['parent_order_id']:
            return c.execute('SELECT table_id FROM orders WHERE id=?',(order['parent_order_id'],)).fetchone()[0]
        return None

    def menu(self):  # อ่านรายการเมนูเรียงตามหมวดและรหัส
        return self.query('SELECT * FROM menu ORDER BY category,id')

    def create_order(self,uid,table_id,guests,cart,request_key,note='',*,fulfillment='dine_in',pickup_name='',pickup_phone=''):  # ตรวจทุกกฎแล้วบันทึกหัวบิล อาหารและประวัติใน transaction เดียว
        self.expire()
        if not isinstance(cart,(list,tuple)) or not cart or len(cart)>50 or not isinstance(request_key,str) or not request_key or len(request_key)>100 or not isinstance(note,str) or len(note)>500:
            raise RuleError('ตะกร้าหรือข้อมูลรายการไม่ถูกต้อง')
        with self.tx() as c:
            self.require(c,uid)
            existing=c.execute('SELECT id,user_id FROM orders WHERE request_key=?',(request_key,)).fetchone()
            if existing:
                if existing['user_id']!=uid: raise RuleError('ข้อมูลรายการไม่ถูกต้อง')
                return existing['id']
            if c.execute("SELECT value FROM settings WHERE key='accepting_orders'").fetchone()[0]!='1':
                raise RuleError('ร้านหยุดรับออเดอร์ชั่วคราว')
            if c.execute("SELECT 1 FROM orders WHERE user_id=? AND status IN ('awaiting_payment','submitted')",(uid,)).fetchone():
                raise RuleError('คุณมีออเดอร์ที่รอชำระหรือรอตรวจเงิน กรุณาดำเนินการรายการนั้นก่อนสั่งเพิ่ม')
            parent_order_id=None
            if fulfillment not in ('dine_in','takeaway'): raise RuleError('รูปแบบรับอาหารไม่ถูกต้อง')
            if fulfillment=='takeaway':
                if not isinstance(pickup_name,str) or not 1<=len(pickup_name.strip())<=80 or not isinstance(pickup_phone,str):
                    raise RuleError('กรุณากรอกชื่อผู้รับและเบอร์โทร')
                pickup_phone=re.sub(r'[ -]','',pickup_phone.strip())
                if not re.fullmatch(r'0[0-9]{9}',pickup_phone):raise RuleError('กรุณากรอกเบอร์โทรไทย 10 หลัก')
                pickup_name=pickup_name.strip();table_id=None;guests=0
            else:
                pickup_name=pickup_phone=''
                t=c.execute('SELECT * FROM dining_tables WHERE id=? AND enabled=1',(table_id,)).fetchone()
                if not t or type(guests) is not int or not 1<=guests<=t['seats']:
                    raise RuleError('จำนวนคนเกินความจุโต๊ะ หรือโต๊ะปิดใช้งาน')
                occupied=c.execute("SELECT o.*,COALESCE(o.parent_order_id,o.id) AS root_id FROM orders o LEFT JOIN orders p ON p.id=o.parent_order_id WHERE COALESCE(o.table_id,p.table_id)=? AND o.status IN ('awaiting_payment','submitted','paid','preparing','served')",(table_id,)).fetchall()
                if occupied:
                    if any(row['user_id']!=uid for row in occupied):
                        raise RuleError('โต๊ะนี้มีลูกค้าเลือกแล้ว กรุณาเลือกโต๊ะอื่น')
                    parent=c.execute('SELECT * FROM orders WHERE id=?',(occupied[0]['root_id'],)).fetchone()
                    if parent['paid_at'] is None:
                        raise RuleError('ต้องยืนยันรับเงินออเดอร์ก่อนหน้าก่อนสั่งเพิ่มที่โต๊ะนี้')
                    parent_order_id=parent['id']
                    table_id=None
            lines=[]
            for item in cart:
                if not isinstance(item,dict) or type(item.get('menu_id')) is not int:
                    raise RuleError('ข้อมูลเมนูไม่ถูกต้อง กรุณาตรวจตะกร้า')
                m=c.execute('SELECT * FROM menu WHERE id=? AND available=1',(item['menu_id'],)).fetchone()
                q=item.get('quantity')
                if m and item.get('price',m['price'])!=m['price']:
                    raise RuleError('ราคาเมนูเปลี่ยน กรุณานำเมนูออกแล้วเพิ่มใหม่เพื่อยืนยันราคาปัจจุบัน')
                if not m or not isinstance(q,int) or isinstance(q,bool) or not 1<=q<=20:
                    raise RuleError('เมนูหมดหรือจำนวนไม่ถูกต้อง กรุณาตรวจตะกร้า')
                if item.get('doneness') not in DONENESS or item.get('sauce') not in SAUCES or not isinstance(item.get('note',''),str) or len(item.get('note',''))>200:
                    raise RuleError('ตัวเลือกอาหารไม่ถูกต้อง')
                if m['category']!='สเต๊กเนื้อ' and item['doneness']!='ไม่ระบุ':
                    raise RuleError('เลือกระดับความสุกได้เฉพาะสเต๊กเนื้อ')
                option=item.get('drink_option','')
                allowed=DRINK_OPTIONS.get(m['name'],()) if m['category']=='เครื่องดื่ม' else ()
                if not isinstance(option,str) or (option and option not in allowed):
                    raise RuleError('ตัวเลือกเครื่องดื่มไม่ถูกต้อง')
                lines.append((m,q,item))
            subtotal=sum(m['price']*q for m,q,_ in lines)
            subtotal,vat,total=inclusive_totals(subtotal)
            now=int(time.time())
            oid=c.execute('INSERT INTO orders(user_id,table_id,guests,subtotal,vat,total,created,request_key,note,awaiting_since,fulfillment,pickup_name,pickup_phone,parent_order_id,vat_included) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)',(uid,table_id,guests,subtotal,vat,total,now,request_key,note.strip(),now,fulfillment,pickup_name,pickup_phone,parent_order_id)).lastrowid
            for m,q,i in lines:
                c.execute('INSERT INTO order_items(order_id,menu_id,name,price,quantity,doneness,sauce,note,drink_option) VALUES(?,?,?,?,?,?,?,?,?)',(oid,m['id'],m['name'],m['price'],q,i['doneness'],i['sauce'],i.get('note','').strip(),i.get('drink_option','')))
            self.log(c,uid,oid,'created')
            return oid

    def orders(self,uid,all_orders=False):  # อ่านออเดอร์ตามสิทธิ์พร้อมชื่อโต๊ะจริงหรือกลับบ้าน
        self.expire()
        with self.connect() as c:
            self.require(c,uid,all_orders)
            sql='SELECT o.*,COALESCE(o.table_id,p.table_id) AS effective_table_id,COALESCE(t.name,\'สั่งกลับบ้าน\') AS table_name,u.name AS customer,u.email FROM orders o LEFT JOIN orders p ON p.id=o.parent_order_id LEFT JOIN dining_tables t ON t.id=COALESCE(o.table_id,p.table_id) JOIN users u ON u.id=o.user_id'
            return [dict(r) for r in c.execute(sql+('' if all_orders else ' WHERE o.user_id=?')+' ORDER BY o.id DESC',() if all_orders else (uid,)).fetchall()]

    def details(self,uid,oid):  # อ่านอาหารและหลักฐานของบิลหลังตรวจสิทธิ์
        with self.connect() as c:
            self.require_order(c,uid,oid)
            items=[dict(r) for r in c.execute('SELECT * FROM order_items WHERE order_id=?',(oid,))]
            slips=[dict(r) for r in c.execute('SELECT id,created,data FROM slips WHERE order_id=? ORDER BY id DESC',(oid,))]
            return items,slips

    def items_for_orders(self,uid,order_ids):  # อ่านอาหารของหลายบิลแบบกลุ่มสำหรับหน้าคิวของเจ้าของ
        """Items for many orders in one query (kitchen board). Owner only; skips slip images."""
        ids=list(dict.fromkeys(to_int(value,'ไม่พบรายการ') for value in order_ids))
        with self.connect() as c:
            self.require(c,uid,True)
            result={oid:[] for oid in ids}
            for start in range(0,len(ids),500):
                batch=ids[start:start+500]
                marks=','.join('?' for _ in batch)
                for row in c.execute(f'SELECT * FROM order_items WHERE order_id IN ({marks}) ORDER BY id',batch):
                    result[row['order_id']].append(dict(row))
            return result

    def submit_payment(self,uid,oid,method,slip=None):  # รับแจ้งเงินสดหรือสลิป QR เป็นรอตรวจ ยังไม่ถือว่ารับเงินจริง
        self.expire()
        if method not in ('cash','qr'): raise RuleError('ช่องทางชำระเงินไม่ถูกต้อง')
        if method=='qr' and not slip: raise RuleError('กรุณาแนบสลิป')
        clean=self.normalize_image(slip) if method=='qr' else None
        digest=hashlib.sha256(clean).hexdigest() if clean else None
        with self.tx() as c:
            o=self.require_order(c,uid,oid)
            if o['status']!='awaiting_payment': raise RuleError('รายการนี้ไม่อยู่ในสถานะรอชำระเงิน')
            bank=c.execute("SELECT value FROM settings WHERE key='bank_details'").fetchone()[0]
            if method=='qr' and (not bank or not c.execute("SELECT 1 FROM assets WHERE key='payment_qr'").fetchone()):
                raise RuleError('ร้านยังไม่ได้ตั้งค่า QR รับเงิน กรุณาเลือกเงินสด')
            if clean:
                duplicate=c.execute('SELECT order_id FROM slips WHERE digest=?',(digest,)).fetchone()
                if duplicate and duplicate['order_id']!=oid: raise RuleError('สลิปนี้ถูกใช้กับรายการอื่นแล้ว')
                if duplicate and o['payment_feedback']:
                    raise RuleError('สลิปนี้เคยถูกปฏิเสธแล้ว กรุณาตรวจเหตุผลของร้านและแนบสลิปที่ถูกต้อง')
                if not duplicate:
                    c.execute('INSERT INTO slips(order_id,data,digest,created) VALUES(?,?,?,?)',(oid,clean,digest,int(time.time())))
            c.execute("UPDATE orders SET status='submitted',payment_method=?,payment_snapshot=? WHERE id=?",(method,bank if method=='qr' else 'เงินสดที่เคาน์เตอร์',oid))
            self.log(c,uid,oid,'payment_submitted',method)

    def cancel(self,uid,oid,reason):  # ยกเลิกได้เฉพาะขั้นที่อนุญาตและต้องมีเหตุผล
        if not reason.strip() or len(reason)>300: raise RuleError('กรุณาระบุเหตุผลไม่เกิน 300 ตัวอักษร')
        with self.tx() as c:
            o=self.require_order(c,uid,oid)
            if o['status']!='awaiting_payment':
                raise RuleError('ยกเลิกได้เฉพาะรายการที่ยังไม่แจ้งชำระเงิน หากโอนแล้วให้ติดต่อร้าน')
            c.execute("UPDATE orders SET status='cancelled',cancel_reason=? WHERE id=?",(reason.strip(),oid))
            self.log(c,uid,oid,'cancelled',reason.strip())

    def transition(self,uid,oid,target,reason=''):  # ให้เจ้าของเปลี่ยนสถานะตามลำดับ พร้อมบันทึกเวลารับเงินและประวัติ
        allowed={'submitted':('paid','awaiting_payment'),'paid':('preparing',),'preparing':('served',),'served':('completed',)}
        with self.tx() as c:
            o=self.require_order(c,uid,oid,True)
            if target not in allowed.get(o['status'],()): raise RuleError('สถานะรายการเปลี่ยนแล้ว กรุณารีเฟรช')
            if target=='awaiting_payment' and not reason.strip(): raise RuleError('กรุณาระบุเหตุผลที่ไม่อนุมัติ')
            if len(reason)>300: raise RuleError('เหตุผลยาวเกิน 300 ตัวอักษร')
            if target=='paid':
                c.execute('UPDATE orders SET status=?,paid_at=? WHERE id=?',(target,int(time.time()),oid))
            elif target=='completed':
                c.execute('UPDATE orders SET status=?,completed_at=? WHERE id=?',(target,int(time.time()),oid))
            elif target=='awaiting_payment':
                c.execute('UPDATE orders SET status=?,awaiting_since=?,payment_method=NULL,payment_feedback=? WHERE id=?',(target,int(time.time()),reason.strip(),oid))
            else:
                c.execute('UPDATE orders SET status=? WHERE id=?',(target,oid))
            self.log(c,uid,oid,target,reason.strip())

    def save_menu(self,uid,mid,name,category,description,price,available):  # สร้างหรือแก้เมนูโดยไม่แก้ราคาและชื่อที่บันทึกในบิลเก่า
        if not name.strip() or len(name)>100 or not category.strip() or len(category)>60 or len(description)>500 or type(price) is not int or not 1<=price<=10000000:
            raise RuleError('ข้อมูลเมนูไม่ถูกต้อง')
        with self.tx() as c:
            self.require(c,uid,True)
            args=(name.strip(),category.strip(),description.strip(),price,int(available))
            if mid: c.execute('UPDATE menu SET name=?,category=?,description=?,price=?,available=? WHERE id=?',args+(mid,))
            else: c.execute('INSERT INTO menu(name,category,description,price,available) VALUES(?,?,?,?,?)',args)
            self.log(c,uid,None,'menu_updated',name.strip())

    def set_menu_available(self,uid,mid,available):  # ปรับเปิดขายหรือหยุดขายโดยตรวจสิทธิ์เจ้าของ
        if not isinstance(available,bool):
            raise RuleError('สถานะเปิดขายไม่ถูกต้อง')
        with self.tx() as c:
            self.require(c,uid,True)
            if not c.execute('SELECT id FROM menu WHERE id=?',(mid,)).fetchone():
                raise RuleError('ไม่พบเมนู')
            c.execute('UPDATE menu SET available=? WHERE id=?',(int(available),mid))
            self.log(c,uid,None,'menu_availability',f'{mid}:{int(available)}')

    def save_table(self,uid,tid,name,seats,enabled):  # แก้โต๊ะได้เมื่อไม่ติดออเดอร์ที่ยังใช้งานรวมบิลสั่งเพิ่ม
        seats=to_int(seats,'จำนวนที่นั่งต้องเป็นจำนวนเต็ม 1–30')
        if not name.strip() or len(name)>30 or not 1<=seats<=30: raise RuleError('ข้อมูลโต๊ะไม่ถูกต้อง')
        try:
            with self.tx() as c:
                self.require(c,uid,True)
                if tid:
                    if c.execute("SELECT 1 FROM orders o LEFT JOIN orders p ON p.id=o.parent_order_id WHERE COALESCE(o.table_id,p.table_id)=? AND o.status IN ('awaiting_payment','submitted','paid','preparing','served')",(tid,)).fetchone():
                        raise RuleError('แก้โต๊ะได้เมื่อโต๊ะว่างเท่านั้น')
                    c.execute('UPDATE dining_tables SET name=?,seats=?,enabled=? WHERE id=?',(name.strip(),int(seats),int(enabled),tid))
                else: c.execute('INSERT INTO dining_tables(name,seats,enabled) VALUES(?,?,?)',(name.strip(),int(seats),int(enabled)))
                self.log(c,uid,None,'table_updated',name.strip())
        except sqlite3.IntegrityError:
            raise RuleError('ชื่อโต๊ะนี้ถูกใช้แล้ว') from None

    def change_password(self,uid,old,new):  # ตรวจรหัสเดิมและตั้ง hash ใหม่ พร้อมทำให้ session รุ่นเก่าหมดสิทธิ์
        encoded=self.hash_password(new)
        with self.tx() as c:
            u=self.require(c,uid)
            if not self.verify_password(old,u['password']): raise RuleError('รหัสผ่านเดิมไม่ถูกต้อง')
            c.execute('UPDATE users SET password=?,auth_version=auth_version+1 WHERE id=?',(encoded,uid))
            self.log(c,uid,None,'password_changed')

    def reset_customer(self,uid,target,new):  # ให้เจ้าของช่วยตั้งรหัสลูกค้าตามขอบเขตสิทธิ์ของระบบ
        encoded=self.hash_password(new)
        with self.tx() as c:
            self.require(c,uid,True)
            t=c.execute("SELECT * FROM users WHERE id=? AND role='customer'",(target,)).fetchone()
            if not t: raise RuleError('ไม่พบบัญชีลูกค้า')
            c.execute('UPDATE users SET password=?,auth_version=auth_version+1 WHERE id=?',(encoded,target))
            c.execute('DELETE FROM login_attempts WHERE email=?',(t['email'],))
            self.log(c,uid,None,'customer_password_reset',str(target))

    def menu_sales_report(self,uid,start,end):  # รวมจำนวนและยอดอาหารจากบิลรับเงินแล้ว โดยคงเมนูยอดศูนย์ไว้
        """Rank paid menu quantities, retaining current unsold/paused menus and historical item prices."""
        with self.connect() as c:
            self.require(c,uid,True)
            start=to_int(start,'ช่วงวันที่ไม่ถูกต้อง')
            end=to_int(end,'ช่วงวันที่ไม่ถูกต้อง')
            if end<=start: raise RuleError('ช่วงวันที่ไม่ถูกต้อง')
            result={r['id']:dict(r,quantity=0,revenue=0,order_count=0) for r in c.execute('SELECT id,name,category,available FROM menu')}
            # อ่านรายการที่รับเงินแล้วครั้งเดียว ลดการยิง SQL ทีละบิลและใช้ snapshot เดียวกัน
            paid_lines=c.execute('SELECT i.menu_id,i.price,i.quantity,i.id,i.order_id,o.subtotal FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.paid_at>=? AND o.paid_at<? ORDER BY i.order_id,i.id',(start,end)).fetchall()
            for _,group in groupby(paid_lines,key=lambda r:r['order_id']):
                lines=list(group)
                bill=lines[0]
                weights=[r['price']*r['quantity'] for r in lines]
                weight=sum(weights)
                if not weight: continue
                # กระจายยอดก่อน VAT ตามสัดส่วน และแจกเศษสตางค์ให้ยอดรวมตรงบิลทั้งเก่าและใหม่
                amounts=[bill['subtotal']*w//weight for w in weights]
                remainder=bill['subtotal']-sum(amounts)
                ranked=sorted(range(len(lines)),key=lambda i: (-(bill['subtotal']*weights[i]%weight),lines[i]['id']))
                for i in ranked[:remainder]: amounts[i]+=1
                counted=set()
                for line,amount in zip(lines,amounts):
                    entry=result[line['menu_id']]
                    entry['quantity']+=line['quantity']
                    entry['revenue']+=amount
                    if line['menu_id'] not in counted:
                        entry['order_count']+=1
                        counted.add(line['menu_id'])
            return sorted(result.values(),key=lambda r:(-r['quantity'],-r['revenue'],r['id']))

    def report(self,uid,start,end):  # อ่านยอดรับเงินตาม paid_at และช่วงเวลาที่กำหนด
        with self.connect() as c:
            self.require(c,uid,True)
            return [dict(r) for r in c.execute('SELECT o.id,COALESCE(t.name,\'สั่งกลับบ้าน\') AS table_name,u.name AS customer,o.subtotal,o.vat,o.total,o.payment_method,o.status,o.paid_at FROM orders o LEFT JOIN orders p ON p.id=o.parent_order_id LEFT JOIN dining_tables t ON t.id=COALESCE(o.table_id,p.table_id) JOIN users u ON u.id=o.user_id WHERE o.paid_at>=? AND o.paid_at<? ORDER BY o.paid_at',(start,end))]

    def audit(self,uid):  # อ่านประวัติการดำเนินการล่าสุดสำหรับเจ้าของ
        with self.connect() as c:
            self.require(c,uid,True)
            return [dict(r) for r in c.execute('SELECT a.*,u.name AS actor_name FROM audit a LEFT JOIN users u ON u.id=a.actor ORDER BY a.id DESC LIMIT 500')]

    def backup(self,uid):  # ใช้ SQLite backup API สร้างสำเนาข้อมูลที่สอดคล้องกัน
        with self.connect() as c:
            self.require(c,uid,True)
            target=sqlite3.connect(':memory:')
            try:
                c.backup(target)
                return target.serialize()
            finally: target.close()

    def receipt(self,uid,oid):  # สร้างใบเสร็จข้อความแบบเดิม ส่วนหน้าปัจจุบันใช้ receipt_design.py
        with self.connect() as c:
            o=self.require_order(c,uid,oid)
            if o['paid_at'] is None: raise RuleError('ยังไม่ได้รับการยืนยันชำระเงิน')
            t='สั่งกลับบ้าน' if o['fulfillment']=='takeaway' else c.execute('SELECT name FROM dining_tables WHERE id=?',(self.effective_table(c,o),)).fetchone()[0]
            shop=c.execute("SELECT value FROM settings WHERE key='shop_name'").fetchone()[0]
            lines=[shop,f'หลักฐานการรับเงิน #{oid:06}',f'โต๊ะ {t}',f'รับเงิน {local_time(o["paid_at"])}','-'*32]
            for i in c.execute('SELECT * FROM order_items WHERE order_id=?',(oid,)):
                lines.append(f'{i["name"]} x {i["quantity"]}: {money(i["price"]*i["quantity"])} บาท')
            lines += ['-'*32,f'ก่อน VAT: {money(o["subtotal"])} บาท',f'VAT 7%: {money(o["vat"])} บาท',f'รวม: {money(o["total"])} บาท',f'ช่องทาง: {"เงินสด" if o["payment_method"]=="cash" else "QR / โอน"}','เอกสารนี้เป็นหลักฐานรับเงิน ไม่ใช่ใบกำกับภาษีเต็มรูป']
            return '\n'.join(lines).encode('utf-8-sig')

def money(satang):  # แปลงจำนวนเต็มหน่วยสตางค์เป็นข้อความบาทสำหรับแสดงผล
    return f'{satang/100:,.2f}'

def local_time(epoch):  # แปลงเวลาเป็นข้อความตามเขตเวลาประเทศไทย
    return datetime.fromtimestamp(epoch,BANGKOK).strftime('%d/%m/%Y %H:%M') if epoch else '-'

def csv_bytes(rows):  # สร้าง CSV ภาษาไทยและลดความเสี่ยงข้อความถูกเปิดเป็นสูตร
    if not rows: return b''
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=list(rows[0]))
    writer.writeheader()
    for row in rows:
        writer.writerow({k:("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v) for k,v in row.items()})
    return out.getvalue().encode('utf-8-sig')
