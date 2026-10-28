"""Python application with a branded HTML/CSS presentation layer."""
import io
import os
import secrets
import time
from pathlib import Path
from html import escape
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
import streamlit as st
from i18n import t as tr, markup, display_option, menu_name, menu_description, translated_item_options, localized_selectbox
from core import DATA, Store, RuleError, STATUSES, ACTIVE, PENDING_PAYMENT, DONENESS, SAUCES, DRINK_OPTIONS, item_options as original_item_options, BANGKOK, inclusive_totals, money, local_time, csv_bytes
from brand_ui import apply_style, hero, featured_menu_html, banner, steps, table_card, food_image, menu_info, menu_catalog, admin_table, sales_chart_spec, contact_footer, section_header, status_badge, order_tracker, payment_deadline, price_summary, empty_state, kitchen_ticket, stock_card_html, ASSETS
from password_reset import SMTPMailer, ResetService, load_mail_config
from receipt_design import receipt_fragment, receipt_html
from receipt_png import receipt_png_download
from theme_clock import scheduled_dark, scheduled_period

#หน้าจอและเส้นทางการใช้งาน

item_options=translated_item_options

st.set_page_config(page_title='dek steak • สั่งอาหาร',page_icon=str(ASSETS/'logo.png'),layout='wide',initial_sidebar_state='expanded')
st.session_state.setdefault('language','th')
with st.container(key='language_toolbar'):
    _,language_control=st.columns([4,1])
    language_control.selectbox('🌐 Language',['th','en','zh'],format_func=lambda code:{'th':'ไทย','en':'English','zh':'中文'}[code],key='language')


@st.cache_resource(show_spinner=False, max_entries=16)
def open_store(path,core_revision):  # สร้างและ cache ตัวจัดการฐานข้อมูล โดยเปลี่ยน cache เมื่อ core.py เปลี่ยนรุ่น
    # Store keeps only its path. Each operation opens/closes its own connection.
    return Store(path)


# A domain update must invalidate the cached Store class and run migrations.
store=open_store(str(DATA / 'dek_steak.sqlite3'),Path(__file__).with_name('core.py').stat().st_mtime_ns)
def sync_theme():  # ตั้งธีมตามรอบเช้าหรือเย็นของเวลาไทย
    period=scheduled_period()
    if st.session_state.get('theme_period')!=period:
        st.session_state['dark_theme']=scheduled_dark()
        st.session_state['theme_period']=period


sync_theme()
st.session_state.pop('auto_theme',None)
applied_dark=st.session_state['dark_theme']
apply_style(dark=applied_dark)
mailconfig_error=''
try:
    mailconfig=load_mail_config(ASSETS.parent/'secrets.toml')
except RuleError as error:
    mailconfig=dict(os.environ)
    mailconfig_error=str(error)
mailer=SMTPMailer(mailconfig)
reset_service=ResetService(store,mailer)
def manual_theme():  # จำว่าผู้ใช้ปรับธีมเองในรอบเวลานี้
    st.session_state['theme_period']=scheduled_period()


@st.fragment(run_every='30s')
def appearance_controls():  # แสดงปุ่มโทนเข้มและตรวจรอบเวลาอัตโนมัติทุก 30 วินาที
    if st.session_state.get('theme_period')!=scheduled_period():
        sync_theme()
        st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
    with st.container(key='appearance_toolbar'):
        _,tone=st.columns([5,1])
        tone.toggle(tr('โทนเข้ม'), key='dark_theme', on_change=manual_theme)
    if st.session_state['dark_theme']!=applied_dark:
        st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด


appearance_controls()


def clear_user_session():  # ล้างข้อมูลเข้าสู่ระบบและตะกร้า แต่เก็บภาษาและธีมไว้
    for key in list(st.session_state):
        if key not in ('dark_theme','theme_period','language'):
            del st.session_state[key]


def toast_action(fn,message='บันทึกเรียบร้อย'):  # เรียกงานที่แก้ข้อมูล แสดงผลสำเร็จ และจัดการข้อผิดพลาดตามกฎร้าน
    try:
        fn()
        st.session_state['flash']=message
        st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
    except RuleError as e:
        st.error(tr(str(e)))



def add_to_cart(menu,quantity,doneness,sauce,note,drink_option=''):  # เพิ่มอาหารใน session และรวมจำนวนเฉพาะรายการที่มีตัวเลือกเหมือนกัน
    cart=st.session_state.setdefault('cart',[])
    note=note.strip()
    for item in cart:
        same=(item['menu_id']==menu['id'] and item['price']==menu['price'] and item['doneness']==doneness and item['sauce']==sauce and item['note'].strip()==note and item.get('drink_option','')==drink_option)
        if same and item['quantity']+quantity<=20:
            item['quantity']+=quantity
            item['name']=menu['name']
            item['cart_id']=secrets.token_hex(8)
            return
    if len(cart)>=50:
        raise RuleError('ตะกร้ารับได้ไม่เกิน 50 รายการ')
    cart.append({'menu_id':menu['id'],'name':menu['name'],'price':menu['price'],'quantity':quantity,'doneness':doneness,'sauce':sauce,'note':note,'drink_option':drink_option,'cart_id':secrets.token_hex(8)})


def submit_menu_item(uid, menu):  # รับการส่งฟอร์มอาหารผ่าน callback เพื่อลดการรันหน้าจอซ้ำ
    # Streamlit applies the form values before invoking the callback.
    check_live_session(uid)
    mid=menu['id']
    try:
        add_to_cart(menu,st.session_state[f'q{mid}'],
                    st.session_state.get(f'd{mid}','ไม่ระบุ'),
                    st.session_state.get(f's{mid}','ไม่ใส่ซอส'),
                    st.session_state.get(f'n{mid}',''),
                    st.session_state.get(f'drink{mid}',''))
        st.session_state['cart_flash']=tr('เพิ่ม ')+menu_name(menu['name'])+tr(' ลงตะกร้าแล้ว')
    except RuleError as error:
        st.session_state['cart_error']=str(error)


@st.dialog('ตะกร้าของคุณ',width='large')
def quick_cart(uid):  # เปิดตะกร้าแบบหน้าต่างย่อโดยยังอยู่ในหน้าเดิม
    check_live_session(uid)
    cart=st.session_state.get('cart',[])
    if not cart:
        st.info(tr('ตะกร้ายังว่าง เลือกจานโปรดจากหน้าเมนูได้เลย'))
        return
    menu={item['id']:item for item in store.menu()}
    photos=store.assets(f'menu_photo_{item["menu_id"]}' for item in cart)
    subtotal=0
    for item in cart:
        current=menu.get(item['menu_id'])
        price=current['price'] if current else item['price']
        subtotal+=price*item['quantity']
        picture,description,amount=st.columns([.8,3,1.2])
        image=photos.get(f'menu_photo_{item["menu_id"]}')
        if image: picture.image(image,width=65)
        description.write(f"{menu_name(item['name'])}{tr(' × ')}{item['quantity']}")
        if item_options(item): description.caption(item_options(item))
        amount.write(f"{tr('฿')}{money(price * item['quantity'])}")
        if not current or not current['available']:
            st.warning(tr('มีเมนูที่หยุดขาย กรุณานำออกในหน้าตะกร้า'))
        elif price!=item['price']:
            st.warning(tr('มีราคาเปลี่ยน กรุณานำเมนูออกแล้วเพิ่มใหม่ในราคาปัจจุบัน'))
    subtotal,vat,total=inclusive_totals(subtotal)  # แยก VAT จากราคาเมนูรวมภาษีแล้ว
    price_summary(subtotal,vat,total)
    if st.button(tr('ตรวจตะกร้าและยืนยัน'), type='primary', key='quick_cart_checkout', width='stretch', on_click=request_checkout_page):
        st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด


def request_checkout_page():  # เตรียมเปลี่ยนไปหน้าตะกร้าเพื่อตรวจและยืนยันรายการ
    st.session_state['customer_page']='ตะกร้า / ยืนยัน'
    st.session_state['next_customer_page']='ตะกร้า / ยืนยัน'


def remember_order_mode():  # จำรูปแบบรับอาหารแยกจากสถานะของ widget
    st.session_state['order_mode']=st.session_state['fulfillment_choice']
    st.session_state.pop('order_key',None)


def fulfillment_choice():  # ให้เลือกทานที่ร้านหรือกลับบ้าน โดยเก็บค่าภายในเดิมแม้เปลี่ยนภาษา
    mode=st.radio(tr('รับอาหารแบบไหน'), ['dine_in', 'takeaway'], index=0 if st.session_state.get('order_mode', 'dine_in') == 'dine_in' else 1, format_func=display_option(lambda value: 'ทานที่ร้าน' if value == 'dine_in' else 'สั่งกลับบ้าน'), horizontal=True, key='fulfillment_choice', on_change=remember_order_mode)
    st.session_state['order_mode']=mode
    return mode


def order_status(order):  # เลือกข้อความสถานะให้ตรงกับการทานที่ร้านหรือรับกลับบ้าน
    if order.get('fulfillment')=='takeaway':
        return tr({'served':'พร้อมรับอาหาร','completed':'รับอาหารแล้ว'}.get(order['status'],STATUSES[order['status']]))
    return tr(STATUSES[order['status']])


def pickup_fields(uid):  # แสดงช่องชื่อและเบอร์โทรผู้รับอาหารกลับบ้าน
    a,b=st.columns(2)
    a.text_input(tr('ชื่อผู้รับอาหาร'), value=store.user(uid)['name'], key='pickup_name', max_chars=80)
    b.text_input(tr('เบอร์โทรผู้รับ (10 หลัก)'), key='pickup_phone', max_chars=12, placeholder=tr('08xxxxxxxx'))
    st.caption(tr('มารับอาหารที่ร้าน · ร้านเริ่มทำเมื่อยืนยันรับเงิน · ไม่มีบริการจัดส่ง'))


def customer_checkout(uid):  # ตรวจตะกร้า รูปแบบรับอาหารและโต๊ะก่อนเปิดขั้นยืนยัน
    check_live_session(uid)
    section_header(tr('ตรวจตะกร้าและยืนยัน'), tr(''), tr('CHECKOUT'))
    steps(1,st.session_state.get('order_mode','dine_in'))
    if not st.session_state.get('cart'):
        st.info(tr('ยังไม่มีอาหารในตะกร้า เลือกอาหารก่อนเริ่มรายการ'))
        return
    active=[order for order in store.orders(uid) if order['status'] in PENDING_PAYMENT]
    if active:
        st.info(tr('คุณมีออเดอร์ที่รอชำระหรือรอตรวจเงิน กรุณาดำเนินการรายการนั้นก่อนสั่งเพิ่ม'))
        return
    if fulfillment_choice()=='takeaway':
        pickup_fields(uid)
        basket(uid,None,0)
        return
    free=[table for table in store.orderable_tables(uid) if table['enabled'] and (not table['order_id'] or table['can_add'])]
    if not free:
        st.warning(tr('ยังไม่มีโต๊ะว่าง กรุณาติดต่อร้านหรือกลับมาเลือกใหม่'))
        return
    tmap={table['id']:table for table in free}
    options=list(tmap)
    previous=st.session_state.get('selected_table')
    index=options.index(previous) if previous in tmap else 0
    a,b=st.columns(2)
    tid=localized_selectbox(a,tr('โต๊ะสำหรับรายการนี้'), options, index=index, key='checkout_table', format_func=display_option(lambda value: f"{tmap[value]['name']} ({tmap[value]['seats']} ที่นั่ง)"))
    default=min(int(st.session_state.get(f'guests_{tid}',1)),tmap[tid]['seats'])
    guests=localized_selectbox(b,tr('จำนวนผู้ใช้บริการ'), list(range(1, tmap[tid]['seats'] + 1)), index=default - 1, key=f'checkout_guests_{tid}', format_func=display_option())
    st.caption(tr('ตรวจโต๊ะ จำนวนคน และราคาอาหารก่อนยืนยัน ร้านจะกันโต๊ะเมื่อสร้างออเดอร์สำเร็จ'))
    basket(uid,tid,int(guests))


def quick_inventory(uid):  # เปิดเครื่องมือให้เจ้าของปรับสถานะขายอาหารอย่างรวดเร็ว
    menu=store.menu()
    photos=store.assets(f'menu_photo_{item["id"]}' for item in menu)
    st.caption(tr('เปลี่ยนเฉพาะสถานะขาย ราคาและรายละเอียดเมนูคงเดิม'))
    for row in range(0,len(menu),3):
        columns=st.columns(3)
        for column,item in zip(columns,menu[row:row+3]):
            with column:
                with st.container(border=True,key=f'stock_card_{item["id"]}',height='stretch',vertical_alignment='distribute'):
                    photo=photos.get(f'menu_photo_{item["id"]}')
                    st.html(stock_card_html(item,photo))  # ภาพสี่เหลี่ยมขนาดเดียวกันและข้อมูลสูงสม่ำเสมอทุกการ์ด
                    label='หยุดขายเมนูนี้' if item['available'] else 'เปิดขายเมนูนี้'
                    if st.button(tr(label), key=f"quick_stock_{item['id']}", width='stretch'):
                        toast_action(lambda mid=item['id'],value=not bool(item['available']):store.set_menu_available(uid,mid,value),'อัปเดตสถานะเมนูแล้ว')


def move_featured(delta,count):  # เลื่อนตำแหน่งเมนูแนะนำและวนเมื่อถึงรายการสุดท้าย
    elapsed=max(0,time.monotonic()-st.session_state.get('featured_epoch',time.monotonic()))
    st.session_state['featured_offset']=(st.session_state.get('featured_offset',0)+int(elapsed//8)+delta)%count
    st.session_state['featured_epoch']=time.monotonic()


@st.fragment
def featured_showcase(recommendations):  # แสดงเมนูแนะนำพร้อมปุ่มเลื่อน
    if not recommendations: return
    count=len(recommendations)
    offset=st.session_state.get('featured_offset',0)%count
    st.session_state['featured_epoch']=time.monotonic()
    ordered=recommendations[offset:]+recommendations[:offset]
    with st.container(key='featured_showcase'):
        st.html(featured_menu_html(ordered))
        if count>1:
            with st.container(key='featured_controls'):
                previous,_,following=st.columns([1,8,1])
                previous.button(tr('‹'), key='featured_previous', help=tr('เมนูก่อนหน้า'), on_click=move_featured, args=(-1, count))
                following.button(tr('›'), key='featured_next', help=tr('เมนูถัดไป'), on_click=move_featured, args=(1, count))


def auth_page():  # แสดงเข้าสู่ระบบและสมัครสมาชิก สมัครสำเร็จแล้วพาเข้าร้านพร้อมต้อนรับ
    visual,middle=st.columns([1.15,1],gap='large')
    with visual:
        recommendations=[]
        mmap={item['id']:item for item in store.menu()}
        featured_ids=store.featured_ids()
        photos=store.assets(f'menu_photo_{mid}' for mid in featured_ids)
        for mid in featured_ids:
            menu=mmap.get(mid)
            if not menu or not menu['available']: continue
            photo=photos.get(f'menu_photo_{menu["id"]}')
            if photo: recommendations.append((menu,photo))
            if len(recommendations)==5: break
        hero()
        featured_showcase(recommendations)
    with middle:
        with st.container(key='login_card'):
            st.caption(tr('ยินดีต้อนรับ'))
            st.title(tr('DEK STEAK'))
            st.subheader(tr('เข้าสู่ระบบ'))
            st.caption(tr('สมัครและเข้าสู่ระบบด้วยอีเมล @gmail.com เท่านั้น'))
            if not store.query("SELECT id FROM users WHERE role='owner' AND active=1"):
                st.warning(tr('ยังไม่ได้ตั้งค่าบัญชีเจ้าของร้าน ให้ผู้ดูแลรัน python manage.py setup-owner ในโฟลเดอร์โปรเจกต์ก่อนเปิดบริการ'))
            login,signup=st.tabs([tr('เข้าสู่ระบบ'), tr('สมัครสมาชิก')])
            with login:
                with st.form('login'):
                    email=st.text_input(tr('อีเมล'), max_chars=254, placeholder='yourname@gmail.com', key='ui_265_26')
                    password=st.text_input(tr('รหัสผ่าน'), type='password', max_chars=128, key='ui_266_29')
                    ok=st.form_submit_button(tr('เข้าสู่ระบบ'), type='primary', width='stretch', key='ui_267_23')
                if ok:
                    try:
                        user=store.authenticate(email,password)
                        clear_user_session()
                        st.session_state['uid']=user['id']
                        st.session_state['login_time']=time.time()
                        st.session_state['auth_version']=user['auth_version']
                        st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
                    except RuleError as e: st.error(tr(str(e)))
                if st.button(tr('ลืมรหัสผ่าน?'), key='forgot_password', type='tertiary'):
                    st.session_state['recovery_open']=True
                    st.session_state.setdefault('recovery_step','email')
                if st.session_state.get('recovery_open'):
                    password_recovery()
            with signup:
                with st.form('signup'):
                    name=st.text_input(tr('ชื่อที่ใช้เรียก'), max_chars=80, key='ui_284_25')
                    email2=st.text_input(tr('อีเมลสำหรับสมัคร'), max_chars=254, placeholder='yourname@gmail.com', key='ui_285_27')
                    password2=st.text_input(tr('ตั้งรหัสผ่าน (10–128 ตัวอักษร)'), type='password', max_chars=128, key='ui_286_30')
                    confirm=st.text_input(tr('ยืนยันรหัสผ่าน'), type='password', max_chars=128, key='ui_287_28')
                    consent=st.checkbox(tr('รับทราบว่าร้านจัดเก็บบัญชี รายการอาหาร และสลิปเพื่อดำเนินรายการ'), key='ui_288_28')
                    ok2=st.form_submit_button(tr('สร้างบัญชี'), type='primary', width='stretch', key='ui_289_24')
                if ok2:
                    if not consent: st.error(tr('กรุณารับทราบการจัดเก็บข้อมูล'))
                    elif password2!=confirm: st.error(tr('รหัสผ่านไม่ตรงกัน'))
                    else:
                        try:
                            uid=store.register(email2,name,password2)
                            user=store.user(uid)
                            clear_user_session()
                            st.session_state['uid']=uid
                            st.session_state['login_time']=time.time()
                            st.session_state['auth_version']=user['auth_version']
                            st.session_state['customer_page']='เลือกโต๊ะ / สั่งอาหาร'
                            st.session_state['flash']=tr('สมัครเรียบร้อย ยินดีต้อนรับ ')+user['name']+tr(' สู่ Dek Steak')
                            st.session_state['personal_flash']=True
                            st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
                        except RuleError as e: st.error(tr(str(e)))
    contact_footer(store.settings()['shop_name'],dark=st.session_state['dark_theme'])


def close_recovery():  # ปิดขั้นตอนลืมรหัสผ่านและล้างสถานะที่เกี่ยวข้อง
    st.session_state['recovery_open']=False


@st.dialog('ลืมรหัสผ่าน',width='small',on_dismiss=close_recovery)
def password_recovery():  # เปิดหน้าต่างลืมรหัสผ่าน
    with st.container(key='password_recovery_panel'):
        recovery_content()


def recovery_stage(stage):  # สลับขั้นตอนขอ OTP กรอกรหัส หรือแสดงผลสำเร็จ
    st.session_state['recovery_step']=stage
    st.session_state.pop('recovery_error',None)


def current_reset_service():  # อ่านค่าผู้ส่งอีเมลล่าสุดแม้รันเฉพาะหน้าต่างลืมรหัส
    # Dialog interactions rerun only the dialog; read sender settings again here.
    return ResetService(store,SMTPMailer(load_mail_config(ASSETS.parent/'secrets.toml')))


def request_recovery_code():  # ส่งคำขอ OTP และแสดงข้อความตอบที่ไม่เปิดเผยว่ามีบัญชีหรือไม่
    try:
        st.session_state['recovery_message']=current_reset_service().request(st.session_state.get('reset_email',''))
        recovery_stage('code')
    except RuleError as error:
        st.session_state['recovery_error']=str(error)


def complete_recovery():  # ตรวจรหัสยืนยันและส่งคำขอตั้งรหัสผ่านใหม่
    if st.session_state.get('reset_new')!=st.session_state.get('reset_confirm'):
        st.session_state['recovery_error']='รหัสผ่านไม่ตรงกัน'
        return
    try:
        current_reset_service().complete(st.session_state.get('reset_complete_email',''),st.session_state.get('reset_code',''),st.session_state.get('reset_new',''))
        recovery_stage('done')
        for key in ('reset_new','reset_confirm','reset_code'):
            st.session_state.pop(key,None)
    except RuleError as error:
        st.session_state['recovery_error']=str(error)


def recovery_content():  # สร้างฟอร์มลืมรหัสผ่านตามขั้นตอนปัจจุบัน
    stage=st.session_state.get('recovery_step','email')
    if stage=='done':
        st.success(tr('ตั้งรหัสใหม่สำเร็จ เข้าสู่ระบบด้วยรหัสใหม่ได้เลย'))
        if st.button(tr('กลับไปเข้าสู่ระบบ'), type='primary', width='stretch', key='ui_354_11'):
            close_recovery()
            for key in ('recovery_step','recovery_message','recovery_error','reset_email','reset_new','reset_confirm','reset_code','reset_complete_email'):
                st.session_state.pop(key,None)
            st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
        return
    try:
        sender_ready=current_reset_service().mailer.configured
    except RuleError:
        sender_ready=False
    if not sender_ready:
        st.info(tr('ร้านยังไม่ได้ตั้งค่าอีเมลผู้ส่ง กรุณาติดต่อร้านเพื่อเปิดบริการรับรหัสยืนยัน'))
    if st.session_state.get('recovery_error'):
        st.error(tr(st.session_state['recovery_error']))
    if stage=='email':
        st.caption(tr('กรอกอีเมลที่สมัครไว้ เพื่อรับรหัสสำหรับตั้งรหัสผ่านใหม่'))
        with st.form('request_reset'):
            st.text_input(tr('อีเมลที่สมัครไว้'), max_chars=254, key='reset_email', placeholder=tr('you@example.com'))
            st.form_submit_button(tr('ส่งรหัสยืนยัน'), type='primary', width='stretch', on_click=request_recovery_code, key='ui_372_12')
        st.button(tr('มีรหัสยืนยันแล้ว'), type='tertiary', on_click=recovery_stage, args=('code',), key='ui_373_8')
        return
    if st.session_state.get('recovery_message'):
        st.info(tr(st.session_state['recovery_message']))
    st.caption(tr('ใช้รหัสล่าสุด 8 หลักที่ได้รับทางอีเมล • รหัสมีอายุ 10 นาที'))
    with st.form('complete_reset'):
        st.text_input(tr('อีเมลสำหรับตั้งรหัสใหม่'), value=st.session_state.get('reset_email', ''), max_chars=254, key='reset_complete_email')
        st.text_input(tr('รหัสยืนยัน 8 หลัก'), max_chars=8, key='reset_code')
        st.text_input(tr('รหัสผ่านใหม่ (10–128 ตัวอักษร)'), type='password', max_chars=128, key='reset_new')
        st.text_input(tr('ยืนยันรหัสใหม่'), type='password', max_chars=128, key='reset_confirm')
        st.form_submit_button(tr('ตั้งรหัสผ่านใหม่'), type='primary', width='stretch', disabled=not sender_ready, on_click=complete_recovery, key='ui_383_8')
    st.button(tr('กลับไปกรอกอีเมล / ส่งรหัสอีกครั้ง'), type='tertiary', on_click=recovery_stage, args=('email',), key='ui_384_4')


def account(uid):  # แสดงข้อมูลบัญชีและฟอร์มเปลี่ยนรหัสผ่าน
    st.header(tr('บัญชีของฉัน'))
    user=store.user(uid)
    with st.container(border=True,key='account_profile'):
        st.subheader(user['name'])
        st.caption(user['email'])
        st.caption(tr('เจ้าของร้าน') if user['role'] == 'owner' else tr('สมาชิก'))
    st.subheader(tr('เปลี่ยนรหัสผ่าน'))
    with st.form('password'):
        old=st.text_input(tr('รหัสผ่านเดิม'), type='password', key='ui_411_12')
        new=st.text_input(tr('รหัสผ่านใหม่'), type='password', max_chars=128, key='ui_412_12')
        confirm=st.text_input(tr('ยืนยันรหัสผ่านใหม่'), type='password', max_chars=128, key='ui_413_16')
        ok=st.form_submit_button(tr('เปลี่ยนรหัสผ่าน'), type='primary', width='stretch', key='ui_414_11')
    if ok:
        if new!=confirm: st.error(tr('รหัสผ่านไม่ตรงกัน'))
        else: toast_action(lambda:store.change_password(uid,old,new))


def select_table(tid):  # จำโต๊ะที่ลูกค้าเลือกใน session
    st.session_state['selected_table']=tid


def table_gallery(tables):  # แสดงรูปโต๊ะ จำนวนที่นั่งและสถานะที่เลือกได้
    with st.expander(tr('ดูรูปโต๊ะและสถานะทั้งหมด')):
        with st.container(key='table_gallery'):
            for row in range(0,len(tables),5):
                columns=st.columns(5)
                for column,t in zip(columns,tables[row:row+5]):
                    with column:
                        selected=st.session_state.get('selected_table')==t['id']
                        table_card(t,selected)
                        st.button(tr('เลือกโต๊ะนี้'), key=f"table_pick_{t['id']}", type='primary' if selected else 'secondary', disabled=not t['enabled'] or (bool(t['order_id']) and not t.get('can_add')), width='stretch', on_click=select_table, args=(t['id'],))


def customer_order(uid):  # หน้าลูกค้าเลือกประเภทรับอาหาร โต๊ะ หมวด เมนูและตัวเลือก
    section_header(tr('เลือกอาหาร'), tr('เลือกจานโปรดในแบบของคุณ'), tr('MENU'))
    if st.button(tr('รีเฟรชโต๊ะว่าง'), key='ui_438_7'):
        st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
    active=[o for o in store.orders(uid) if o['status'] in PENDING_PAYMENT]
    if active:
        st.info(tr('คุณมีออเดอร์ที่รอชำระหรือรอตรวจเงิน กรุณาดำเนินการรายการนั้นก่อนสั่งเพิ่ม'))
        return
    if store.settings()['accepting_orders']!='1':
        st.warning(tr('ร้านหยุดรับออเดอร์ชั่วคราว'))
        return
    mode=fulfillment_choice()
    if any(o['status'] in ('paid','preparing','served') for o in store.orders(uid)):
        st.info(tr('สั่งเพิ่มได้แล้ว เลือกทานที่โต๊ะเดิมหรือสั่งกลับบ้าน รายการใหม่ชำระแยกจากรายการก่อนหน้า'))
    tables=store.orderable_tables(uid)
    free=[t for t in tables if t['enabled'] and (not t['order_id'] or t['can_add'])]
    if st.session_state.get('selected_table') not in [t['id'] for t in free]:
        st.session_state.pop('selected_table',None)
    if not free and mode=='dine_in':
        st.warning(tr('ยังไม่มีโต๊ะว่าง กรุณารีเฟรชหรือติดต่อร้าน'))
        table_gallery(tables)
        return
    tmap={t['id']:t for t in free}
    menu=[m for m in store.menu() if m['available']]
    if not menu: st.warning(tr('ไม่มีเมนูที่เปิดขาย')); return
    with st.container(key='order_context'):
        if mode=='dine_in':
            a,b=st.columns([2,1])
            table_id=localized_selectbox(a,tr('โต๊ะที่เลือก'), list(tmap), format_func=display_option(lambda v: f"{tmap[v]['name']} ({tmap[v]['seats']} ที่นั่ง)"), key='selected_table')
            guests=localized_selectbox(b,tr('จำนวนคน'), list(range(1, tmap[table_id]['seats'] + 1)), key=f'guests_{table_id}', format_func=display_option())
        else:
            table_id=None;guests=0
            st.caption(tr('สั่งกลับบ้าน · ไม่ต้องเลือกโต๊ะ · กรอกข้อมูลผู้รับในหน้าตะกร้า'))
        categories=['ทั้งหมด']+sorted({m['category'] for m in menu})
        if st.session_state.get('menu_category') not in categories:
            st.session_state['menu_category']='ทั้งหมด'
        category=st.radio(tr('หมวดอาหาร'), categories, horizontal=True, key='menu_category', label_visibility='collapsed', format_func=display_option())
    st.caption(tr('ราคาหน้าเมนูรวม VAT 7% แล้ว • มารับอาหารที่ร้าน') if mode == 'takeaway' else tr('ราคาหน้าเมนูรวม VAT 7% แล้ว • โต๊ะจะถูกกันเมื่อยืนยันออเดอร์'))
    if mode=='dine_in': table_gallery(tables)
    search=st.text_input(tr('ค้นหาเมนู'), placeholder=tr('เช่น Ribeye, ไก่, ชา'), key='ui_473_11')
    visible=[m for m in menu if (category=='ทั้งหมด' or m['category']==category) and search.lower() in (m['name']+' '+m['description']+' '+menu_name(m['name'])+' '+menu_description(m['description'])).lower()]
    photos=store.assets(f'menu_photo_{m["id"]}' for m in visible)
    st.session_state.setdefault('cart',[])
    for row in range(0,len(visible),3):
        columns=st.columns(3)
        for column,m in zip(columns,visible[row:row+3]):
            with column:
                with st.container(border=True,key=f'menu_card_{m["id"]}',height="stretch"):
                    food_image(photos.get(f'menu_photo_{m["id"]}'),m['category'])
                    menu_info(m)
                    with st.form(f'item_{m["id"]}',height="stretch"):  # ให้แบบฟอร์มขยายตามการ์ดและวางปุ่มไว้ด้านล่าง
                        q=localized_selectbox(st,tr('จำนวน'), list(range(1, 21)), key=f"q{m['id']}", format_func=display_option())
                        d=st.radio(tr('ความสุก'), DONENESS, horizontal=True, key=f"d{m['id']}", format_func=display_option()) if m['category']=='สเต๊กเนื้อ' else 'ไม่ระบุ'
                        sauce=st.radio(tr('ซอส'), SAUCES, horizontal=True, key=f"s{m['id']}", format_func=display_option()) if m['category'].startswith('สเต๊ก') else 'ไม่ใส่ซอส'
                        drink_option=''
                        if m['category']=='เครื่องดื่ม' and m['name'] in DRINK_OPTIONS:
                            label='ระดับความหวาน' if m['name']=='ชาเย็น' else 'อุณหภูมิน้ำ'
                            default=3 if m['name']=='ชาเย็น' else 0
                            with st.container(key=f'drink_choices_{m["id"]}'):
                                drink_option=st.radio(tr(label), DRINK_OPTIONS[m['name']], index=default, horizontal=True, key=f"drink{m['id']}", format_func=display_option())
                        with st.expander(tr('หมายเหตุ / แจ้งแพ้อาหาร (ถ้ามี)')):
                            note=st.text_input(tr('หมายเหตุ / แจ้งแพ้อาหาร'), max_chars=200, key=f"n{m['id']}")
                        st.form_submit_button(tr('＋ เพิ่มในตะกร้า'), width='stretch', on_click=submit_menu_item, args=(uid, m), key=f'item_submit_{m["id"]}')
    # รายละเอียดตะกร้าแสดงเฉพาะหน้า CHECKOUT; หน้าเลือกอาหารใช้แถบสรุปเพื่อเปิดตะกร้า
    if mode=='takeaway':
        st.caption(tr('เพิ่มอาหารแล้วเปิดตะกร้าเพื่อกรอกชื่อและเบอร์โทรผู้รับ'))


def sticky_basket(uid):  # แสดงแถบตะกร้าติดด้านล่างพร้อมจำนวนและยอดรวม VAT
    cart=st.session_state.get('cart',[])
    if not cart: return
    menu={item['id']:item for item in store.menu()}
    count=sum(item['quantity'] for item in cart)
    subtotal=sum(menu.get(item['menu_id'],item)['price']*item['quantity'] for item in cart)
    subtotal,vat,total=inclusive_totals(subtotal)  # แยก VAT จากราคาเมนูรวมภาษีแล้ว
    table_id=st.session_state.get('checkout_table') if st.session_state.get('customer_page')=='ตะกร้า / ยืนยัน' else st.session_state.get('selected_table')
    table=next((t for t in store.tables() if t['id']==table_id),None)
    table_name=tr('สั่งกลับบ้าน') if st.session_state.get('order_mode')=='takeaway' else tr('โต๊ะ ')+table['name'] if table else 'เลือกโต๊ะก่อนยืนยัน'
    with st.container(key='sticky_basket'):
        detail,total_column,action=st.columns([2.5,2,2])
        with detail:
            st.html(f"""{markup('<div class="dek-sticky-copy"><strong>ตะกร้า · ')}{count}{markup(' รายการ</strong><span>')}{escape(table_name)}{markup('</span></div>')}""")
        with total_column:
            st.html(f"""{markup('<div class="dek-sticky-copy dek-sticky-amount"><strong>฿')}{money(total)}{markup('</strong><span>รวม VAT 7% แล้ว</span></div>')}""")
        if action.button(tr('ตรวจตะกร้า'), key='sticky_checkout', type='primary', width='stretch', on_click=request_checkout_page):
            st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด


def basket(uid,table_id,guests):  # แก้จำนวน ตรวจราคาและการเปิดขาย คำนวณยอด แล้วส่งคำขอยืนยันออเดอร์
    menu=[m for m in store.menu() if m['available']]
    st.html(markup('<div id="dek-cart"></div>'))
    st.subheader(tr('🛒 ตะกร้าของคุณ'))
    cart=st.session_state.cart
    mmap={m['id']:m for m in menu}
    if not cart: empty_state(tr('🛒'), tr('ตะกร้ายังว่าง'), tr('เลือกอาหารจากหน้าเมนูเพื่อเริ่มออเดอร์')); return
    valid=True
    subtotal=0
    for i,item in enumerate(cart):
        m=mmap.get(item['menu_id'])
        if not m: valid=False
        price=m['price'] if m else item['price']
        left,right=st.columns([6,1])
        item.setdefault('cart_id',secrets.token_hex(8))
        quantity_key=f'cart_quantity_{item["cart_id"]}'
        quantity=localized_selectbox(left,tr('จำนวนในตะกร้า'), list(range(1, 21)), index=item['quantity'] - 1, key=quantity_key, format_func=display_option())
        if quantity is None:
            valid=False
            left.error(tr('กรุณากรอกจำนวนอาหารก่อนยืนยัน'))
        else:
            item['quantity']=int(quantity)
        subtotal+=price*item['quantity']
        left.write(f"{menu_name(item['name'])}{tr(' × ')}{item['quantity']}{tr(' — ฿')}{money(price * item['quantity'])}")
        if item_options(item): left.caption(item_options(item))
        if not m: left.error(tr('เมนูนี้หยุดขาย กรุณานำออกจากตะกร้า'))
        elif price!=item['price']:
            valid=False
            left.warning(tr('ราคาเมนูเปลี่ยน กรุณานำรายการนี้ออกแล้วเพิ่มใหม่เพื่อยืนยันราคา'))
        if right.button(tr('นำออก'), key=f'delete_{i}'):
            cart.pop(i); st.rerun()
    subtotal,vat,total=inclusive_totals(subtotal)  # แยก VAT จากราคาเมนูรวมภาษีแล้ว
    price_summary(subtotal,vat,total)
    note=st.text_area(tr('หมายเหตุรวมถึงร้าน'), max_chars=500, key='ui_557_9')
    st.caption(tr('ตรวจสอบราคาอีกครั้งเมื่อยืนยัน หากราคาเปลี่ยนต้องนำเมนูออกแล้วเพิ่มใหม่ก่อนสั่ง'))
    if st.button(tr('ยืนยันออเดอร์และไปชำระเงิน'), type='primary', disabled=not valid, width='stretch', key='ui_559_7'):
        key=st.session_state.setdefault('order_key',secrets.token_urlsafe(24))
        try:
            oid=store.create_order(uid,table_id,int(guests),cart,key,note,fulfillment=st.session_state.get('order_mode','dine_in'),pickup_name=st.session_state.get('pickup_name',''),pickup_phone=st.session_state.get('pickup_phone',''))
            st.session_state.cart=[]
            st.session_state.pop('order_key',None)
            st.session_state['next_customer_page']='รายการของฉัน / ชำระเงิน'
            st.session_state['flash']=f'สร้างออเดอร์ #{oid:06} แล้ว'
            st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
        except RuleError as e: st.error(tr(str(e)))


def order_contents(uid,o,admin=False):  # แสดงรายการอาหาร ตัวเลือก หลักฐานชำระและใบเสร็จตามสิทธิ์
    items,slips=store.details(uid,o['id'])
    status_badge(o['status'],o.get('fulfillment','dine_in'))
    if not admin: order_tracker(o['status'],o.get('fulfillment','dine_in'))
    if o.get('fulfillment')=='takeaway':
        st.info(f"{tr('สั่งกลับบ้าน · ผู้รับ ')}{o['pickup_name']}{tr(' · โทร ')}{o['pickup_phone']}")
        st.caption(tr('รับอาหารที่ร้านด้วยหมายเลขออเดอร์นี้'))
    else:
        st.write(f"{tr('โต๊ะ **')}{o['table_name']}{tr('** • ')}{o['guests']}{tr(' คน • ')}{local_time(o['created'])}")
    if admin: st.write(f"{tr('ลูกค้า: ')}{o['customer']}{tr(' (')}{o['email']}{tr(')')}")
    admin_table([{'เมนู':i['name'],'จำนวน':i['quantity'],'ตัวเลือก':item_options(i) or '—','รวม (บาท)':money(i['price']*i['quantity'])} for i in items],label='รายการอาหารในออเดอร์')
    if o['note']: st.info(tr(o['note']))
    price_summary(o['subtotal'],o['vat'],o['total'])
    if o['payment_method']:
        st.write(tr('ช่องทาง: ') + (tr('เงินสด') if o['payment_method'] == 'cash' else tr('QR / โอน')))
        if admin and o['payment_snapshot']: st.caption(tr('ข้อมูลรับเงินขณะแจ้งชำระ: ') + o['payment_snapshot'])
    if o['cancel_reason']: st.warning(tr(o['cancel_reason']))
    if o['payment_feedback']: st.warning(tr('ร้านแจ้ง: ' + o['payment_feedback']))
    if slips:
        with st.expander(tr('หลักฐานสลิปที่ส่ง')):
            for s in slips:
                st.caption(local_time(s['created']))
                st.image(s['data'],width=320)
    if o['paid_at']:
        receipt=store.receipt_data(uid,o['id'])
        with st.expander(tr('ดูใบเสร็จรับเงิน')):
            st.html(receipt_fragment(receipt))
            st.download_button(tr('ดาวน์โหลดใบเสร็จสำหรับพิมพ์ / PDF'), receipt_html(receipt), f"dek_steak_receipt_{o['id']:06}.html", mime='text/html', key=f"receipt_{admin}_{o['id']}")
            st.iframe(receipt_png_download(receipt, dark=st.session_state.get('dark_theme', False)), height='content', width='stretch')  # สร้าง PNG เมื่อผู้ใช้กด โดยไม่รันแปลงภาพทุกครั้งที่อัปเดตสถานะ


def check_live_session(uid):  # ตรวจบัญชี อายุ session และเวอร์ชันรหัสผ่านก่อนแสดงข้อมูลส่วนตัว
    user=store.user(uid)
    if not user or not user['active'] or user['auth_version']!=st.session_state.get('auth_version') or time.time()-st.session_state.get('login_time',0)>4*3600:
        clear_user_session()
        st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด


@st.fragment(run_every='8s')
def customer_payments(uid):  # อัปเดตออเดอร์ลูกค้าเป็นช่วง แสดงชำระเงิน สถานะและการสั่งเพิ่ม
    check_live_session(uid)
    section_header(tr('ออเดอร์และชำระเงิน'), tr('สถานะอัปเดตอัตโนมัติทุก 8 วินาที'), tr('ORDERS'))
    steps(2,st.session_state.get('order_mode','dine_in'))
    if st.button(tr('รีเฟรชสถานะ'), key='ui_613_7'): st.rerun()
    orders=store.orders(uid)
    if any(o['paid_at'] is not None for o in orders) and not any(o['status'] in PENDING_PAYMENT for o in orders):
        if st.button(tr('สั่งอาหารเพิ่ม / สั่งกลับบ้าน'),key='order_more',type='primary',width='stretch'):
            st.session_state['next_customer_page']='เลือกโต๊ะ / สั่งอาหาร'
            st.rerun()  # รันหน้าใหม่เพื่อแสดงผลจากสถานะล่าสุด
    if not orders: empty_state(tr('🍽'), tr('ยังไม่มีออเดอร์'), tr('เลือกโต๊ะและอาหารเพื่อเริ่มมื้อนี้')); return
    for o in orders[:50]:
        with st.expander(f"{tr('#')}{o['id']:06}{tr(' • ')}{order_status(o)}{tr(' • ฿')}{money(o['total'])}", expanded=o['status'] in ACTIVE):
            order_contents(uid,o)
            if o['status']=='awaiting_payment':
                settings=store.settings()
                due=o['awaiting_since']+int(settings['payment_minutes'])*60
                payment_deadline(o['awaiting_since'],int(settings['payment_minutes']))
                bank=settings['bank_details']
                qr=store.asset('payment_qr')
                options=['สแกน QR / โอนเงิน','เงินสดที่เคาน์เตอร์'] if bank and qr else ['เงินสดที่เคาน์เตอร์']
                method=st.radio(tr('ช่องทางชำระเงิน'), options, key=f"paymethod{o['id']}", format_func=display_option())
                slip=None
                if method=='สแกน QR / โอนเงิน':
                    qr_column,details_column=st.columns([1,1.3])
                    with qr_column:
                        st.image(qr,width=300)
                        st.download_button(tr('บันทึก QR ของร้าน'), qr, f'dek_steak_payment_qr.png', mime='image/png', key=f"qr_download{o['id']}")
                    with details_column:
                        st.subheader(tr('สแกนจ่ายมื้อนี้'))
                        st.write(bank)
                        st.metric(tr('ยอดที่ต้องโอน'), f"฿{money(o['total'])}")
                    st.info(f"{tr('ตรวจชื่อผู้รับก่อนโอน และกรอกยอด ฿')}{money(o['total'])}{tr(' ให้ตรงกัน')}")
                    slip=st.file_uploader(tr('แนบสลิป JPEG/PNG ไม่เกิน 5 MB'), type=['jpg', 'jpeg', 'png'], key=f"slip{o['id']}")
                else: st.info(tr('นำยอดรวมไปจ่ายที่เคาน์เตอร์ เจ้าของร้านจะกดยืนยันเมื่อรับเงินแล้ว'))
                if method=='สแกน QR / โอนเงิน' and slip is None:
                    st.caption(tr('โอนแล้วแนบสลิป เพื่อให้ร้านตรวจสอบและยืนยันรับเงิน'))
                if st.button(tr('แจ้งชำระเงิน'), type='primary', key=f"pay{o['id']}", disabled=method == 'สแกน QR / โอนเงิน' and slip is None):
                    toast_action(lambda:store.submit_payment(uid,o['id'],'cash' if method=='เงินสดที่เคาน์เตอร์' else 'qr',slip.getvalue() if slip else None),'ส่งแจ้งชำระแล้ว รอร้านตรวจสอบ')
                with st.expander(tr('ยกเลิกรายการ')):
                    reason=st.text_input(tr('เหตุผลยกเลิก'), key=f"cancel_reason{o['id']}", max_chars=300)
                    confirm=st.checkbox(tr('ยืนยันว่าไม่ได้โอนเงินสำหรับรายการนี้'), key=f"cancel_confirm{o['id']}")
                    if st.button(tr('ยกเลิกและคืนโต๊ะ'), key=f"cancel{o['id']}", disabled=not confirm):
                        toast_action(lambda:store.cancel(uid,o['id'],reason))
            elif o['status']=='submitted': st.info(tr('ร้านกำลังตรวจสอบการชำระเงิน กรุณารอการยืนยัน หากชำระเงินจริงแล้ว อย่าโอนซ้ำ'))


@st.fragment(run_every='8s')
def owner_orders(uid):  # หน้าตรวจรับเงินและจัดคิวครัวของเจ้าของร้าน
    check_live_session(uid)
    section_header(tr('จัดการออเดอร์ / คิวครัว'), tr('คิวอัปเดตอัตโนมัติทุก 8 วินาที'), tr('KITCHEN & ORDERS'))
    if st.button(tr('รีเฟรชคิว'), key='ui_656_7'): st.rerun()
    orders=store.orders(uid,True)
    active=[o for o in orders if o['status'] in ACTIVE]
    midnight=datetime.now(BANGKOK).replace(hour=0,minute=0,second=0,microsecond=0)
    today=store.report(uid,int(midnight.timestamp()),int((midnight+timedelta(days=1)).timestamp()))
    a,b,c,d=st.columns(4)
    a.metric(tr('รับเงินวันนี้'), f"฿{money(sum((order['total'] for order in today)))}")
    b.metric(tr('รอตรวจเงิน'), sum((o['status'] == 'submitted' for o in active)))
    c.metric(tr('กำลังปรุง'), sum((o['status'] == 'preparing' for o in active)))
    d.metric(tr('โต๊ะที่มีลูกค้า'), len({o.get('effective_table_id') for o in active if o.get('fulfillment','dine_in')=='dine_in'}))
    view=st.radio(tr('มุมมอง'), ['จัดการออเดอร์', 'คิวครัว'], horizontal=True, key='owner_order_view', label_visibility='collapsed', format_func=display_option())
    if view=='คิวครัว':
        kitchen=[o for o in active if o['status'] in ('paid','preparing','served')]
        kitchen.sort(key=lambda o:(o['paid_at'] or o['created'],o['id']))
        if not kitchen:
            empty_state(tr('🍳'), tr('คิวครัวยังว่าง'), tr('ออเดอร์ที่ยืนยันรับเงินแล้วจะแสดงที่นี่'))
            return
        grouped=store.items_for_orders(uid,[o['id'] for o in kitchen])
        st.caption(tr('เรียงคิวตามเวลารับเงิน · สีเตือนเมื่อรอเกิน 15 และ 25 นาที นับจากรับเงิน'))
        for offset in range(0,len(kitchen),2):
            columns=st.columns(2)
            for column,o in zip(columns,kitchen[offset:offset+2]):
                with column:
                    kitchen_ticket(o,grouped[o['id']])
                    target,label={'paid':('preparing','เริ่มปรุง'),'preparing':('served','พร้อมรับอาหาร' if o.get('fulfillment')=='takeaway' else 'เสิร์ฟแล้ว'),'served':('completed','รับอาหารแล้ว' if o.get('fulfillment')=='takeaway' else 'จบรายการและคืนโต๊ะ')}[o['status']]
                    if target=='completed' and o.get('fulfillment')=='dine_in' and sum(other.get('effective_table_id')==o.get('effective_table_id') for other in active)>1:
                        label='จบรายการ (โต๊ะยังมีออเดอร์อื่น)'
                    if st.button(tr(label), key=f"kitchen_next{o['id']}", type='primary', width='stretch'):
                        toast_action(lambda oid=o['id'],state=target:store.transition(uid,oid,state))
        return
    with st.container(key='queue_filters'):
        status=localized_selectbox(st,tr('แสดงสถานะ'), ['กำลังดำเนินการ', 'ทั้งหมด'] + list(STATUSES.values()), key='ui_685_15', format_func=display_option())
    visible=[o for o in orders if status=='ทั้งหมด' or (status=='กำลังดำเนินการ' and o['status'] in ACTIVE) or STATUSES[o['status']]==status]
    if not visible: empty_state(tr('📋'), tr('ไม่มีออเดอร์ในสถานะนี้'), tr('เลือกสถานะอื่นเพื่อดูรายการ'))
    for o in visible[:100]:
        with st.expander(f"{tr('#')}{o['id']:06}{tr(' • ')}{o['table_name']}{tr(' • ')}{order_status(o)}{tr(' • ฿')}{money(o['total'])}", expanded=o['status'] == 'submitted'):
            order_contents(uid,o,True)
            if o['status']=='submitted':
                st.warning(tr('ตรวจเงินสดที่รับจริง หรือยอดเข้าบัญชี/ชื่อผู้รับ/วันเวลา/เลขอ้างอิงให้ตรงกับออเดอร์ก่อนอนุมัติ สลิปอาจปลอมได้'))
                check=st.checkbox(tr('ตรวจแล้วว่าได้รับเงินครบจริง'), key=f"verify{o['id']}")
                if st.button(tr('ยืนยันรับเงิน'), key=f"approve{o['id']}", type='primary', disabled=not check):
                    toast_action(lambda:store.transition(uid,o['id'],'paid'))
                with st.expander(tr('ขอให้ลูกค้าแก้หลักฐาน')):
                    reason=st.text_input(tr('เหตุผล'), key=f"reject_reason{o['id']}", max_chars=300)
                    if st.button(tr('คืนรายการให้แจ้งชำระใหม่'), key=f"reject{o['id']}"):
                        toast_action(lambda:store.transition(uid,o['id'],'awaiting_payment',reason))
            transitions={'paid':('preparing','เริ่มปรุง'),'preparing':('served','เสิร์ฟแล้ว'),'served':('completed','จบรายการและคืนโต๊ะ')}
            if o['status'] in transitions:
                target,label=transitions[o['status']]
                if o.get('fulfillment')=='takeaway': label={'served':'พร้อมรับอาหาร','completed':'รับอาหารแล้ว'}.get(target,label)
                elif target=='completed' and sum(other.get('effective_table_id')==o.get('effective_table_id') for other in active)>1:label='จบรายการ (โต๊ะยังมีออเดอร์อื่น)'
                if st.button(tr(label), key=f"next{o['id']}", type='primary'):
                    toast_action(lambda:store.transition(uid,o['id'],target))
            if o['status']=='awaiting_payment':
                st.caption(tr('หากลูกค้าโอนแล้วแต่ยังไม่ได้แจ้ง ให้ลูกค้าแนบสลิปก่อน ห้ามยกเลิกจนกว่าจะตรวจเงิน'))
                reason=st.text_input(tr('เหตุผลยกเลิกโดยร้าน'), key=f"owner_cancel_reason{o['id']}", max_chars=300)
                check=st.checkbox(tr('ตรวจแล้วว่ายังไม่ได้รับเงิน'), key=f"owner_cancel_check{o['id']}")
                if st.button(tr('ยกเลิกรายการ'), key=f"owner_cancel{o['id']}", disabled=not check):
                    toast_action(lambda:store.cancel(uid,o['id'],reason))
    if len(visible)>100: st.caption(tr('แสดงล่าสุด 100 รายการ รายงานยอดขายดูได้ในหน้ารายงาน'))


def reports(uid):  # แสดงช่วงวันที่ ยอดรับเงิน VAT กราฟและข้อมูลส่งออก
    st.header(tr('รายงานยอดขาย'))
    st.caption(tr('นับเฉพาะยอดที่ร้านยืนยันรับเงินแล้ว ตามวันรับเงินในประเทศไทย ไม่ใช่วันสร้างออเดอร์'))
    with st.container(key='report_filters'):
        period_col,date_col=st.columns([2,1],gap='large')
        with period_col:
            period=st.radio(tr('ช่วงเวลา'), ['วัน', 'สัปดาห์', 'เดือน', 'ปี', 'กำหนดเอง'], horizontal=True, key='report_period', format_func=display_option())
        with date_col:
            ref=st.date_input(tr('วันที่อ้างอิง'), value=datetime.now(BANGKOK).date(), format='DD/MM/YYYY', key='report_reference')
    if period=='วัน': start=ref; end=start+timedelta(days=1)
    elif period=='สัปดาห์': start=ref-timedelta(days=ref.weekday()); end=start+timedelta(days=7)
    elif period=='เดือน':
        start=ref.replace(day=1); end=date(ref.year+1,1,1) if ref.month==12 else date(ref.year,ref.month+1,1)
    elif period=='ปี': start=date(ref.year,1,1); end=date(ref.year+1,1,1)
    else:
        a,b=st.columns(2)
        start=a.date_input(tr('ตั้งแต่'), ref.replace(day=1), format='DD/MM/YYYY', key='ui_731_14')
        last=b.date_input(tr('ถึง (รวมวันนี้)'), ref, format='DD/MM/YYYY', key='ui_732_13')
        end=last+timedelta(days=1)
        if end<=start: st.error(tr('ช่วงวันที่ไม่ถูกต้อง')); return
    st.caption(f"{start:%d/%m/%Y}{tr(' – ')}{end - timedelta(days=1):%d/%m/%Y}")
    ts=lambda d:int(datetime.combine(d,datetime.min.time(),BANGKOK).timestamp())
    rows=store.report(uid,ts(start),ts(end))
    total=sum(r['total'] for r in rows)
    a,b,c,d=st.columns(4)
    a.metric(tr('รับเงินรวม'), f'฿{money(total)}')
    b.metric(tr('ก่อน VAT'), f"฿{money(sum((r['subtotal'] for r in rows)))}")
    c.metric(tr('VAT 7%'), f"฿{money(sum((r['vat'] for r in rows)))}")
    d.metric(tr('จำนวนออเดอร์'), len(rows))
    a,b=st.columns(2)
    a.metric(tr('เงินสด'), f"฿{money(sum((r['total'] for r in rows if r['payment_method'] == 'cash')))}")
    b.metric(tr('QR / โอน'), f"฿{money(sum((r['total'] for r in rows if r['payment_method'] == 'qr')))}")
    if rows:
        with st.container(key='sales_chart'):
            st.subheader(tr('ยอดรับเงินรายวัน'))
            st.caption(tr('ยอดยืนยันรับเงินรวม VAT 7% · ชี้ที่แท่งกราฟเพื่อดูยอดและจำนวนออเดอร์'))
            st.vega_lite_chart(sales_chart_spec(rows,dark=st.session_state['dark_theme']),width='stretch',theme=None)
        display=[{'ออเดอร์':r['id'],'โต๊ะ / รับอาหาร':r['table_name'],'ลูกค้า':r['customer'],'ก่อน VAT':money(r['subtotal']),'VAT':money(r['vat']),'รวม':money(r['total']),'ช่องทาง':'เงินสด' if r['payment_method']=='cash' else 'QR / โอน','รับเงินเมื่อ':local_time(r['paid_at'])} for r in rows]
        admin_table(display,label='รายละเอียดรายรับ')
        st.download_button(tr('ดาวน์โหลดรายงาน CSV (เปิดด้วย Excel ได้)'), csv_bytes(display), f'dek_steak_sales_{start}_{end}.csv', 'text/csv', key='ui_754_8')
    else: st.info(tr('ไม่มีรายการรับเงินในช่วงเวลานี้'))
    st.divider()
    menu_sales_summary(uid,start,end)


def menu_sales_summary(uid,start,end):  # แสดงอันดับเมนูขายดีและเมนูยอดศูนย์ในช่วงที่เลือก
    summary=store.menu_sales_report(uid,int(datetime.combine(start,datetime.min.time(),BANGKOK).timestamp()),int(datetime.combine(end,datetime.min.time(),BANGKOK).timestamp()))
    sold=[item for item in summary if item['quantity']>0]
    unsold=[item for item in summary if item['quantity']==0]
    unit_total=sum(item['quantity'] for item in summary)
    st.subheader(tr('เมนูขายดีและเมนูที่ยังไม่มียอดขาย'))
    st.caption(f"{start:%d/%m/%Y}{tr(' – ')}{end - timedelta(days=1):%d/%m/%Y}{tr(' · เรียงตามจำนวนที่ขายจากออเดอร์ยืนยันรับเงินแล้ว')}")
    ranking,zero=st.tabs([f"{tr('อันดับขายดี (')}{len(sold)}{tr(')')}", f"{tr('ยังไม่มียอดขาย (')}{len(unsold)}{tr(')')}"])
    with ranking:
        if sold:
            photos=store.assets(f'menu_photo_{item["id"]}' for item in sold[:3])
            cols=st.columns(min(3,len(sold)))
            for index,(column,item) in enumerate(zip(cols,sold[:3]),1):
                with column:
                    with st.container(border=True,key=f'best_seller_{index}'):
                        st.caption(f"{tr('อันดับ ')}{index}")
                        photo=photos.get(f'menu_photo_{item["id"]}')
                        if photo: food_image(photo,item['category'])
                        st.metric(item['name'], f"{item['quantity']} หน่วย")
                        st.caption(f"{tr('ยอดขาย ฿')}{money(item['revenue'])}{tr(' ก่อน VAT · ')}{item['order_count']}{tr(' ออเดอร์')}")
            admin_table([{'อันดับ':i,'เมนู':item['name'],'จำนวนที่ขาย (หน่วย)':item['quantity'],'ยอดขายก่อน VAT (บาท)':money(item['revenue']),'ออเดอร์':item['order_count'],'สัดส่วนจำนวนขาย':f'{item["quantity"]/unit_total:.1%}'} for i,item in enumerate(sold,1)],label='อันดับเมนูขายดี')
        else:
            st.info(tr('ยังไม่มียอดยืนยันรับเงินในช่วงนี้ จึงยังจัดอันดับขายดีไม่ได้'))
    with zero:
        st.caption(tr('เมนูเปิดขายที่มียอด 0 แยกจากเมนูหยุดขาย สถานะขายเป็นสถานะปัจจุบันของร้าน'))
        if unsold:
            admin_table([{'เมนู':item['name'],'หมวด':item['category'],'จำนวนที่ขาย (หน่วย)':0,'สถานะ':'เปิดขาย' if item['available'] else 'หยุดขาย'} for item in unsold],label='เมนูที่ยังไม่มียอดขาย')
        else: st.success(tr('ทุกเมนูมียอดขายในช่วงนี้'))
    export=[{'เมนู':item['name'],'หมวด':item['category'],'จำนวนที่ขาย (หน่วย)':item['quantity'],'ยอดขายก่อน VAT (บาท)':money(item['revenue']),'ออเดอร์':item['order_count'],'สถานะปัจจุบัน':'เปิดขาย' if item['available'] else 'หยุดขาย'} for item in summary]
    st.download_button(tr('ดาวน์โหลดสรุปยอดขายแต่ละเมนู CSV'), csv_bytes(export), f'dek_steak_menu_sales_{start}_{end}.csv', 'text/csv', key='menu_sales_csv')


def featured_admin(uid):  # ให้เจ้าของเลือกเมนูมีรูปสำหรับแนะนำหน้าร้าน
    st.subheader(tr('เมนูแนะนำหน้าเข้าสู่ระบบ'))
    st.caption(tr('เลือกได้ไม่เกิน 5 เมนู เรียงจากตำแหน่ง 1 ไป 5 เมนูที่หยุดขายจะซ่อนจากหน้าลูกค้าอัตโนมัติ'))
    menus={item['id']:item for item in store.menu()}
    photos=store.assets(f'menu_photo_{mid}' for mid in menus)
    eligible=[mid for mid in menus if f'menu_photo_{mid}' in photos]
    if not eligible:
        st.info(tr('อัปโหลดรูปอาหารในแท็บแก้ไขเมนูก่อน แล้วกลับมาเลือกเมนูแนะนำ'))
        return
    current=store.featured_ids()
    options=[0]+eligible
    with st.form('featured_menu_form'):
        selected=[]
        for slot in range(5):
            mid=current[slot] if slot<len(current) and current[slot] in eligible else 0
            chosen=localized_selectbox(st,f"{tr('ตำแหน่ง ')}{slot + 1}", options, index=options.index(mid), key=f'featured_slot_{slot}', format_func=display_option(lambda value: 'ไม่แสดงเมนู' if value == 0 else menus[value]['name'] + (' · หยุดขาย' if not menus[value]['available'] else '')))
            if chosen: selected.append(chosen)
        save=st.form_submit_button(tr('บันทึกเมนูแนะนำ'), type='primary', key='ui_809_13')
    if save:
        toast_action(lambda:store.save_featured_menu(uid,selected),'บันทึกลำดับเมนูแนะนำแล้ว')
    if current:
        st.caption(tr('ลำดับที่บันทึกไว้'))
        columns=st.columns(len(current))
        for column,mid in zip(columns,current):
            if mid in menus:
                with column:
                    photo=photos.get(f'menu_photo_{mid}')
                    if photo: st.image(photo,width=90)
                    st.caption(menus[mid]['name'])


def menu_admin(uid):  # จัดการชื่อ หมวด ราคา รูปและสถานะขายอาหาร
    st.header(tr('จัดการเมนู'))
    edit,availability,featured=st.tabs([tr('แก้ไขเมนู'), tr('เปิด / หยุดขาย'), tr('เมนูแนะนำ')])
    with featured:
        featured_admin(uid)
    with availability:
        quick_inventory(uid)
    with edit:
        menu=store.menu()
        ids=[0]+[m['id'] for m in menu]
        mmap={m['id']:m for m in menu}
        mid=localized_selectbox(st,tr('เลือกเมนูเพื่อแก้ไข หรือเพิ่มใหม่'), ids, format_func=display_option(lambda v: '＋ เพิ่มเมนูใหม่' if not v else mmap[v]['name']), key='ui_834_12')
        m=mmap.get(mid,{'name':'','category':'สเต๊กเนื้อ','description':'','price':10000,'available':1})
        with st.container(key='menu_editor'):
            with st.form(f'editmenu{mid}'):
                st.subheader('เพิ่มเมนูใหม่' if not mid else 'แก้ไขข้อมูลเมนู')
                left,right=st.columns([2,1])
                name=left.text_input(tr('ชื่อเมนู'), m['name'], max_chars=100, placeholder=tr('เช่น Ribeye Steak'), key='ui_840_21')
                categories=list(dict.fromkeys(['สเต๊กเนื้อ','สเต๊กหมู','สเต๊กไก่','สเต๊กปลา','พาสต้า','สลัด','ของทานเล่น','เครื่องดื่ม']+[item['category'] for item in menu]+[m['category']]))
                category=localized_selectbox(right,tr('หมวดอาหาร'), categories, index=categories.index(m['category']), help=tr('สเต๊กเนื้อจะแสดงตัวเลือกระดับความสุกให้ลูกค้า'), key='ui_842_25', format_func=display_option())
                description=st.text_area(tr('รายละเอียด'), m['description'], max_chars=500, placeholder=tr('วัตถุดิบ รสชาติ หรือเครื่องเคียงของเมนูนี้'), height=100, key='ui_843_28')
                pricing,status=st.columns([2,1])
                price=pricing.number_input(tr('ราคารวม VAT (บาท)'), min_value=0.01, max_value=100000.0, value=m['price'] / 100, step=1.0, format='%.2f', key='ui_845_22')
                pricing.caption(tr('ราคานี้รวม VAT 7% แล้ว ไม่มีบวกเพิ่มตอนชำระ'))
                with status:
                    st.markdown(tr('สถานะขาย'))
                    available=st.toggle(tr('เปิดขาย'), value=bool(m['available']), key='ui_849_30')
                    st.caption(tr('ปิดเพื่อซ่อนจากเมนูสั่งอาหาร'))
                ok=st.form_submit_button(tr('บันทึกเมนู'), type='primary', width='stretch', key='ui_851_19')
        if ok:
            satang=int((Decimal(str(price))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
            toast_action(lambda:store.save_menu(uid,mid,name,category,description,satang,available))
        if mid:
            st.subheader(tr('รูปอาหารของเมนูนี้'))
            current_photo=store.asset(f'menu_photo_{mid}')
            if current_photo:
                st.image(current_photo,width=320)
            with st.form(f'menu_photo_form_{mid}'):
                photo=st.file_uploader(tr('อัปโหลดภาพอาหารจริง JPEG/PNG ไม่เกิน 5 MB'), type=['jpg', 'jpeg', 'png'], key=f'menu_photo_upload_{mid}')
                upload=st.form_submit_button(tr('บันทึกรูปอาหาร'), key='ui_862_23')
            if upload:
                if not photo:
                    st.error(tr('กรุณาเลือกภาพก่อนบันทึก'))
                else:
                    toast_action(lambda:store.save_media(uid,f'menu_photo_{mid}',photo.getvalue()))
            if current_photo and st.button(tr('นำรูปเมนูออก'), key=f'remove_menu_photo_{mid}'):
                toast_action(lambda:store.save_media(uid,f'menu_photo_{mid}',None))
        else:
            st.caption(tr('บันทึกเมนูใหม่ก่อน จากนั้นเลือกเมนูเพื่ออัปโหลดรูปอาหาร'))
        st.subheader(tr('รายการอาหารทั้งหมด'))
        st.caption(f"{len(menu)}{tr(' เมนู · เปิดขาย ')}{sum((bool(item['available']) for item in menu))}{tr(' เมนู')}")
        menu_catalog(menu,store.assets(f'menu_photo_{item["id"]}' for item in menu))


def choose_admin_table(tid):  # จำโต๊ะที่เจ้าของเลือกแก้ไข
    st.session_state['admin_table_id']=tid


def tables_admin(uid):  # แสดงฟอร์มแก้ไขโต๊ะและภาพรวมการใช้งาน
    st.header(tr('จัดการโต๊ะ'))
    tables=store.tables(); tmap={t['id']:t for t in tables}
    free=sum(bool(t['enabled']) and not t['order_id'] for t in tables)
    a,b,c=st.columns(3)
    a.metric(tr('โต๊ะพร้อมรับลูกค้า'), free)
    b.metric(tr('มีลูกค้า'), sum((bool(t['order_id']) for t in tables)))
    c.metric(tr('ปิดใช้งาน'), sum((not t['enabled'] for t in tables)))
    edit,overview=st.tabs([tr('แก้ไขโต๊ะ'), tr('ภาพรวมที่นั่ง')])
    with edit:
        tid=localized_selectbox(st,tr('เลือกโต๊ะ'), [0] + list(tmap), format_func=display_option(lambda v: '＋ เพิ่มโต๊ะใหม่' if not v else tmap[v]['name']), key='admin_table_id')
        t=tmap.get(tid,{'name':'','seats':4,'enabled':1})
        with st.form(f'edittable{tid}'):
            st.subheader('เพิ่มโต๊ะใหม่' if not tid else 'แก้ไขข้อมูลโต๊ะ')
            left,right=st.columns([2,1])
            name=left.text_input(tr('ชื่อโต๊ะ'), t['name'], max_chars=30, placeholder=tr('เช่น T01'), key='ui_896_17')
            seats=right.number_input(tr('จำนวนที่นั่ง'), 1, 30, t['seats'], key='ui_897_18')
            enabled=st.toggle(tr('เปิดใช้งาน'), value=bool(t['enabled']), key='ui_898_20')
            ok=st.form_submit_button(tr('บันทึกโต๊ะ'), type='primary', width='stretch', key='ui_899_15')
        if ok: toast_action(lambda:store.save_table(uid,tid,name,seats,enabled))
        admin_table([{'โต๊ะ':t['name'],'ที่นั่ง':t['seats'],'สถานะ':'ปิด' if not t['enabled'] else 'มีลูกค้า' if t['order_id'] else 'ว่าง'} for t in tables],label='รายการโต๊ะ')
    with overview:
        for row in range(0,len(tables),3):
            cols=st.columns(3)
            for col,t in zip(cols,tables[row:row+3]):
                with col:
                    table_card(t,selected=t['id']==tid)
                    st.button(tr('แก้ไข ') + t['name'], key=f"edit_table_card_{t['id']}", on_click=choose_admin_table, args=(t['id'],), width='stretch')
        st.caption(tr('กดแก้ไขโต๊ะ แล้วเปิดแท็บแก้ไขโต๊ะเพื่อปรับข้อมูล'))


def shop_admin(uid):  # รวมการตั้งค่าร้าน รับเงิน OTP สำรองข้อมูลและช่วยดูแลบัญชี
    st.header(tr('ตั้งค่าร้าน'))
    s=store.settings()
    general,email_tab,backup,security=st.tabs([tr('ข้อมูลและรับเงิน'), tr('อีเมล OTP'), tr('สำรองข้อมูล'), tr('ดูแลบัญชี')])
    with general:
        with st.form('shopsettings'):
            name=st.text_input(tr('ชื่อร้าน'), s['shop_name'], max_chars=80, key='ui_918_17')
            bank=st.text_area(tr('ชื่อผู้รับเงิน / ธนาคาร / เลขบัญชีหรือพร้อมเพย์'), s['bank_details'], max_chars=1500, key='ui_919_17')
            qr=st.file_uploader(tr('QR รับเงินของร้าน JPEG/PNG (ไม่เกิน 5 MB)'), type=['jpg', 'jpeg', 'png'], key='ui_920_15')
            accepting=st.toggle(tr('เปิดรับออเดอร์ใหม่'), value=s['accepting_orders'] == '1', key='ui_921_22')
            minutes=st.number_input(tr('เวลาแจ้งชำระเงิน (นาที)'), 5, 120, int(s['payment_minutes']), key='ui_922_20')
            ok=st.form_submit_button(tr('บันทึกการตั้งค่า'), type='primary', width='stretch', key='ui_923_15')
        if ok: toast_action(lambda:store.save_settings(uid,name,bank,accepting,minutes,qr.getvalue() if qr else None))
        current=store.asset('payment_qr')
        if current: st.image(current,width=220,caption='QR ปัจจุบันของร้าน')
        st.caption(tr('QR นี้เป็น QR ของร้าน ยอดเงินไม่ได้ถูกฝังโดยแอป ลูกค้าต้องกรอกยอดตามออเดอร์'))
    with email_tab:
        st.subheader(tr('บริการรีเซ็ตรหัสผ่านทางอีเมล'))
        if mailconfig_error: st.error(tr(mailconfig_error))
        if mailer.configured:
            st.success(tr('ตั้งค่าผู้ส่งครบแล้ว • ลูกค้าขอ OTP ที่หน้าเข้าสู่ระบบได้'))
            if st.button(tr('ตรวจการเชื่อมต่ออีเมล'), key='ui_952_15'):
                try:
                    mailer.check_connection()
                    st.success(tr('ผู้ให้บริการยอมรับการเชื่อมต่อแล้ว กรุณาทดลองรับ OTP จากหน้าเข้าสู่ระบบ'))
                except RuleError as error: st.error(tr(str(error)))
        else:
            st.info(tr('ตั้งค่า Gmail ในเครื่องด้วย python configure_email.py แล้วรีเฟรชหน้าเว็บ • ดูคู่มือ EMAIL_SETUP_TH.md'))
    with backup:
        st.subheader(tr('สำรองข้อมูล'))
        st.warning(tr('ไฟล์สำรองรวมรหัสผ่านที่แฮชและสลิปลูกค้า เก็บเฉพาะในที่ที่เจ้าของร้านเข้าถึงได้'))
        if st.button(tr('เตรียมไฟล์สำรอง'), key='ui_962_11'):
            st.session_state['backup_bytes']=store.backup(uid)
        if 'backup_bytes' in st.session_state:
            st.download_button(tr('ดาวน์โหลดฐานข้อมูลสำรอง'), st.session_state.backup_bytes, f'dek_steak_backup_{datetime.now(BANGKOK):%Y%m%d_%H%M}.sqlite3', 'application/octet-stream', key='ui_965_12')
    with security:
        st.subheader(tr('ช่วยลูกค้าตั้งรหัสผ่านใหม่'))
        st.caption(tr('ตรวจยืนยันตัวตนลูกค้าก่อน ตั้งรหัสผ่านชั่วคราวและแจ้งให้เปลี่ยนทันที ห้ามเผยแพร่รหัสผ่าน'))
        with st.form('reset_customer'):
            email=st.text_input(tr('อีเมลลูกค้า'), max_chars=254, key='ui_970_18')
            new=st.text_input(tr('รหัสผ่านชั่วคราว 10–128 ตัวอักษร'), type='password', max_chars=128, key='ui_971_16')
            checked=st.checkbox(tr('ตรวจยืนยันตัวตนลูกค้าแล้ว'), key='ui_972_20')
            ok=st.form_submit_button(tr('ตั้งรหัสผ่านใหม่'), key='ui_973_15')
        if ok:
            if not checked: st.error(tr('กรุณายืนยันตัวตนก่อน'))
            else:
                try:
                    matches=store.query("SELECT id FROM users WHERE email=? AND role='customer'",(store.email(email),))
                    if not matches: raise RuleError('ไม่พบบัญชีลูกค้า')
                    toast_action(lambda:store.reset_customer(uid,matches[0]['id'],new))
                except RuleError as e: st.error(tr(str(e)))
        with st.expander(tr('ประวัติการดำเนินการ (ล่าสุด 500 รายการ)')):
            rows=[{'เวลา':local_time(r['created']),'ผู้ดำเนินการ':r['actor_name'] or 'ระบบ','ออเดอร์':r['order_id'],'การกระทำ':r['action'],'รายละเอียด':r['detail']} for r in store.audit(uid)]
            admin_table(rows,label='ประวัติการดำเนินการ')


def main():  # ตรวจ session สร้างแถบข้างตามสิทธิ์และเปิดหน้าที่เลือก
    uid=st.session_state.get('uid')
    if uid and time.time()-st.session_state.get('login_time',0)>4*3600:
        clear_user_session(); uid=None
    user=store.user(uid) if uid else None
    if user and st.session_state.get('auth_version')!=user['auth_version']:
        clear_user_session(); user=None
    if not user or not user['active']:
        auth_page(); return
    if 'next_customer_page' in st.session_state:
        st.session_state['customer_page']=st.session_state.pop('next_customer_page')
    if st.session_state.get('customer_page')=='บรรยากาศร้าน':
        st.session_state['customer_page']='เลือกโต๊ะ / สั่งอาหาร'
    with st.sidebar:
        if (ASSETS/'logo.png').exists():
            st.image(str(ASSETS/'logo.png'),width=90 if user['role']=='owner' else 130)
        st.title(store.settings()['shop_name'])
        if user['role']=='owner':
            st.caption(user['name'] + tr(' · เจ้าของร้าน'))
        else:
            st.write(tr('สวัสดี ') + user['name'])
            st.caption(tr('สมาชิก'))
        with st.container(key='sidebar_navigation'):
            if user['role']=='owner':
                owner_labels={'ออเดอร์ / คิวครัว':'รับออเดอร์','รายงานยอดขาย':'รายงานยอดขาย','เมนูอาหาร':'เมนูอาหาร','โต๊ะ':'จัดการโต๊ะ','ตั้งค่าร้าน':'ตั้งค่าร้าน','บัญชี':'บัญชีของฉัน'}
                page=st.radio(tr('จัดการร้าน'), list(owner_labels), format_func=display_option(lambda value: owner_labels[value]), key='owner_page')
            else:
                labels={'เลือกโต๊ะ / สั่งอาหาร':'เลือกอาหาร','ตะกร้า / ยืนยัน':'ตะกร้า','รายการของฉัน / ชำระเงิน':'ออเดอร์และชำระเงิน','บัญชี':'บัญชีของฉัน'}
                page=st.radio(tr('เมนูของคุณ'), list(labels), format_func=display_option(lambda value: labels[value]), key='customer_page')
        st.divider()
        if st.button(tr('ออกจากระบบ'), width='stretch', key='ui_1017_11'):
            clear_user_session(); st.rerun()
        st.caption(tr('ข้อมูลเวลาประเทศไทย • VAT 7%'))
    flash_slot=st.empty()
    if 'flash' in st.session_state:
        message=st.session_state.pop('flash')
        flash_slot.success(message if st.session_state.pop('personal_flash',False) else tr(message))
    if 'cart_flash' in st.session_state: st.toast(st.session_state.pop('cart_flash'), icon='✅')
    if 'cart_error' in st.session_state: st.error(tr(st.session_state.pop('cart_error')))
    if user['role']=='customer':
        banner(store.settings()['shop_name'], tr('เลือกจานโปรด แล้วให้เราดูแลมื้อนี้'))
    else:
        st.caption(store.settings()['shop_name'] + tr(' · พื้นที่จัดการร้าน'))
    if user['role']=='owner':
        routes={'ออเดอร์ / คิวครัว':owner_orders,'รายงานยอดขาย':reports,'เมนูอาหาร':menu_admin,'โต๊ะ':tables_admin,'ตั้งค่าร้าน':shop_admin,'บัญชี':account}
    else: routes={'เลือกโต๊ะ / สั่งอาหาร':customer_order,'ตะกร้า / ยืนยัน':customer_checkout,'รายการของฉัน / ชำระเงิน':customer_payments,'บัญชี':account}
    if user['role']=='customer':
        with st.container(key='customer_toolbar'):
            label,action=st.columns([3,1.5])
            count=sum(item['quantity'] for item in st.session_state.get('cart',[]))
            label.caption(tr('สั่งกลับบ้าน · ข้อมูลผู้รับ · ตรวจยอดรวม VAT ก่อนยืนยัน') if st.session_state.get('order_mode') == 'takeaway' else tr('เลือกโต๊ะ · เลือกจานโปรด · ตรวจยอดรวม VAT ก่อนยืนยัน'))
            if action.button(f"{tr('ดูตะกร้า (')}{count}{tr(')')}", key='open_quick_cart', width='stretch'):
                quick_cart(uid)
    if user['role']=='owner':
        with st.container(key='admin_workspace'):
            routes[page](uid)  # เรียกฟังก์ชันหน้าที่เลือกพร้อมรหัสผู้ใช้
    else:
        routes[page](uid)  # เรียกฟังก์ชันหน้าที่เลือกพร้อมรหัสผู้ใช้
    if user['role']=='customer' and page in ('เลือกโต๊ะ / สั่งอาหาร','ตะกร้า / ยืนยัน'):
        sticky_basket(uid)
    contact_footer(store.settings()['shop_name'],dark=st.session_state['dark_theme'])

try:
    main()
except RuleError as e:
    st.error(tr(str(e)))
