"""Brand presentation; escape dynamic content before rendering HTML."""
import base64
import io
from functools import lru_cache
from PIL import Image, ImageOps, ImageFilter
from html import escape
from pathlib import Path
import streamlit as st
from i18n import t as tr, markup, display_option, menu_name, menu_description, translated_item_options

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / '.streamlit' / 'assets'
if not ASSETS.exists():
    ASSETS = ROOT.parent / 'assets'  # Prepared-file preview.


@lru_cache(maxsize=64)
def display_uri(data, size=640, background=False):  # ย่อและ cache ภาพแสดงผลเพื่อลดข้อมูล โดยไม่แก้ไฟล์ต้นฉบับ
    """Small presentation copy only; originals and payment QR stay unchanged."""
    with Image.open(io.BytesIO(data)) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        if background:
            image = image.convert('RGB').filter(ImageFilter.GaussianBlur(7))
        output = io.BytesIO()
        transparent = image.mode in ('RGBA', 'LA') or 'transparency' in image.info
        if transparent:
            image.save(output, format='PNG', optimize=True)
            mime = 'image/png'
        else:
            image.convert('RGB').save(output, format='JPEG', quality=82, optimize=True)
            mime = 'image/jpeg'
    return 'data:' + mime + ';base64,' + base64.b64encode(output.getvalue()).decode()


def image_uri(path):  # อ่านภาพจากไฟล์แล้วเลือกขนาดแสดงตามประเภท
    file = Path(path)
    if not file.exists(): return ''
    background = file.name == 'welcome.png'
    size = 1280 if background else 320 if file.name == 'logo.png' else 640
    return display_uri(file.read_bytes(), size, background)


ALIGNMENT_CSS="""
.stApp .dek-menu-chinese{font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif;font-size:16px!important;line-height:1.65!important;letter-spacing:0!important;margin:0 0 10px!important;color:var(--dek-muted)!important;min-height:27px}

.dek-section{display:block;margin:18px 0 22px;text-align:left}
.dek-section h2{margin:8px 0!important;padding:0!important;line-height:1.5!important;letter-spacing:0!important}
.dek-section p{margin:0!important;padding:0!important;line-height:1.7!important}
.dek-section .eyebrow{margin:0!important;line-height:1.5}
.st-key-fulfillment_choice [role="radiogroup"],.st-key-menu_category [role="radiogroup"]{display:flex;align-items:stretch;gap:10px!important;flex-wrap:wrap}
.st-key-fulfillment_choice [role="radiogroup"] label,.st-key-menu_category [role="radiogroup"] label{display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important;box-sizing:border-box;min-height:44px}
.st-key-fulfillment_choice [role="radiogroup"] label{min-width:120px;min-height:48px}
.st-key-fulfillment_choice [role="radiogroup"] label p,.st-key-menu_category [role="radiogroup"] label p{margin:0!important;line-height:1.5!important;letter-spacing:0!important;text-align:center}
.st-key-order_context [data-testid="stCaptionContainer"] p{margin:0 0 10px!important}
.st-key-customer_toolbar [data-testid="stHorizontalBlock"]{align-items:center!important}
.st-key-customer_toolbar [data-testid="stCaptionContainer"]{padding-top:0!important}
.st-key-customer_toolbar [data-testid="stCaptionContainer"] p{margin:0!important;line-height:1.65!important}
.dek-step-row{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));align-items:stretch}
.dek-step{display:flex!important;align-items:center;justify-content:center;gap:8px;min-height:52px;min-width:0!important;line-height:1.5!important;box-sizing:border-box}
.dek-step b{margin:0!important;flex-shrink:0}
@media(max-width:640px){.dek-step{padding:10px 6px!important;gap:5px;flex-wrap:wrap}.dek-section{margin:14px 0 18px}}
"""


def apply_style(dark=False):  # ใช้สีและ CSS ร่วมของเว็บตามธีมสว่างหรือมืด
    st.html('<style>\n    .stApp{isolation:isolate;background:#faf6ef!important}\n    .stApp::before,.stApp::after{content:none!important;display:none!important;background-image:none!important}\n    section[data-testid="stMain"] h1#dek-steak{display:flex;align-items:center;gap:18px}\n    section[data-testid="stMain"] h1#dek-steak::before{content:"";display:inline-block;flex:0 0 86px;\n      height:92px;background:url(\'__LOGO__\') center/contain no-repeat}\n    .st-key-login_card{background:rgba(255,253,249,.9);padding:30px;border:1px solid #ffffffb3;\n      border-radius:28px;box-shadow:0 18px 55px #4227191c;backdrop-filter:blur(16px)}\n    @media(max-width:640px){.st-key-login_card{padding:20px}section[data-testid="stMain"] h1#dek-steak{gap:12px}\n      section[data-testid="stMain"] h1#dek-steak::before{flex-basis:68px;height:74px}}\n    </style>'.replace('__LOGO__', image_uri(ASSETS / 'logo.png')))
    st.html(markup('<style>\n    :root{--dek-ink:#30251f;--dek-orange:#f07128;--dek-cream:#faf6ef}\n    .stApp{background:radial-gradient(ellipse at 90% 0%,#ffe9cb 0,transparent 45%),#faf6ef;color:var(--dek-ink)}\n    [data-testid="stMainBlockContainer"]{max-width:1420px;padding-top:2.4rem;padding-bottom:3rem}\n    h1,h2,h3{letter-spacing:-.025em;color:#30251f}\n    h1{font-weight:850!important;font-size:clamp(28px,3vw,42px)!important}h2{font-weight:750!important}\n    [data-testid="stHeader"]{background:transparent}\n    [data-testid="stAppDeployButton"],[data-testid="stMainMenu"]{display:none}\n    [data-testid="stSidebarCollapsedControl"]{display:flex!important;visibility:visible!important;opacity:1!important;position:fixed!important;top:10px;left:10px;z-index:1000;border-radius:12px;background:#fffaf2!important;color:#693f23!important;box-shadow:0 3px 14px #4d2a1926}\n    [data-testid="stSidebarCollapsedControl"] button,[data-testid="stSidebarCollapseButton"] button{color:#693f23!important;min-width:42px;min-height:42px}\n    [data-testid="stSidebarCollapseButton"]{visibility:visible!important;opacity:1!important}\n    [data-testid="stSidebarCollapsedControl"] [data-testid="stIconMaterial"],[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]{color:#693f23!important}\n    [data-testid="stSidebarCollapsedControl"] svg,[data-testid="stSidebarCollapseButton"] svg{fill:currentColor!important}\n    [data-testid="stSidebar"]{background:#f0e8dc;border-right:1px solid #e2d5c5}\n    [data-testid="stForm"],[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:22px!important}\n    [data-testid="stForm"]{background:#fffdf9;border:1px solid #e7dccf;padding:1.3rem!important;box-shadow:0 8px 25px #54341a06}\n    button[kind="primary"],button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#ed6d25,#ca4a11)!important;border:0!important;color:white!important;box-shadow:0 6px 18px #ce5b2430}\n    .stButton button,.stDownloadButton button{border-radius:12px;min-height:44px;transition:transform .16s,box-shadow .16s}\n    .stButton button:hover,.stDownloadButton button:hover{transform:translateY(-2px);box-shadow:0 6px 18px #6e421619}\n    input,textarea,[data-baseweb="select"]>div{border-radius:10px!important}\n    [data-testid="stMetric"]{background:#fffdf9;border:1px solid #eaddca;border-radius:18px;padding:16px 20px;box-shadow:0 5px 16px #6e421608}\n    [data-testid="stMetricLabel"]{color:#887363}\n    [data-testid="stMetricValue"]{font-weight:800;color:#ac4b1d}\n    [data-testid="stTabs"] [role="tablist"]{gap:14px;border-bottom:1px solid #e5d8c8}\n    [data-testid="stTabs"] [role="tab"]{height:48px;font-weight:700}\n    [data-testid="stImage"] img{border-radius:16px}\n    [data-testid="stExpander"]{background:#fffdf9;border:1px solid #e5d8c8;border-radius:18px;overflow:hidden}\n    .dek-eyebrow{color:#b45722;font-size:11px;letter-spacing:.22em;font-weight:800;text-transform:uppercase}\n    .dek-hero{position:relative;min-height:530px;padding:55px 28px;color:#30251f}\n    .dek-hero-logo{width:120px;filter:drop-shadow(0 4px 10px #0006)}\n    .dek-hero h2{color:#30251f;font-size:clamp(34px,4vw,58px);line-height:1.25;max-width:380px;margin:24px 0 18px;font-weight:850}\n    .dek-hero p{color:#68503d;max-width:350px;font-size:17px;line-height:1.8}\n    .dek-hero .dek-eyebrow{color:#a85120;margin-top:22px}\n    .dek-hero-bottom{position:absolute;bottom:28px;left:28px;background:#fff8eaa6;border:1px solid #ddc7ad;padding:10px 16px;border-radius:999px;font-size:12px;color:#79593e;backdrop-filter:blur(8px)}\n    .dek-banner{display:flex;align-items:center;gap:24px;padding:22px 30px;background:linear-gradient(115deg,#3a251b,#654127);border-radius:24px;color:#fff6e6;box-shadow:0 10px 25px #54341a15;margin-bottom:24px}\n    .dek-banner img{width:86px}.dek-banner h2{color:#fff5e6;margin:5px 0;font-size:26px}.dek-banner p{margin:0;color:#d8bea7;font-size:14px}\n    .dek-step-row{display:flex;gap:10px;margin:15px 0 25px;flex-wrap:wrap}\n    .dek-step{flex:1;min-width:120px;padding:12px 16px;border:1px solid #e7d7c3;border-radius:12px;color:#9b8675;background:#fff9f0;font-size:13px}\n    .dek-step.current{background:#fff0de;border-color:#eea56c;color:#ac4c19;font-weight:750}\n    .dek-step b{margin-right:8px}\n    .dek-table{border:1px solid #e4d7c6;background:#fffdf9;border-radius:16px;padding:15px;text-align:center;min-height:130px;transition:transform .18s;box-shadow:0 6px 16px #42271908}\n    .dek-table.free{border-color:#bfceb7}.dek-table.busy{opacity:.65;background:#f4ece3}.dek-table strong{display:block;font-size:20px;margin:6px 0}.dek-table span{font-size:12px;color:#887363}\n    .dek-table .state{display:inline-block;margin-top:8px;background:#e9f1e2;color:#4c6d3d;border-radius:99px;padding:4px 12px;font-size:11px}.dek-table.busy .state{background:#e8dfd4;color:#887363}\n    .dek-food-placeholder{height:170px;display:flex;flex-direction:column;justify-content:center;align-items:center;background:radial-gradient(circle,#f6dec3,#efe3d3);border-radius:16px;margin-bottom:12px;color:#94714c;font-size:12px;gap:8px}\n    .dek-food-placeholder div{font-size:50px;filter:drop-shadow(0 7px 4px #6b432225)}\n    .dek-food-photo{height:180px;width:100%;object-fit:cover;border-radius:16px;margin-bottom:12px}\n    .dek-empty{padding:22px;border:1px dashed #ccb99e;border-radius:18px;background:#f6eee1;color:#89745f;font-size:14px}\n    .dek-footer{text-align:center;font-size:11px;color:#aa9480;border-top:1px solid #e6d9c7;padding-top:20px;margin-top:35px;letter-spacing:.08em}\n    @media(max-width:800px){[data-testid="stMainBlockContainer"]{padding-top:1.2rem}.dek-hero{min-height:500px;padding:24px 12px}.dek-hero h2{font-size:34px;margin-top:18px}.dek-hero p{font-size:14px;max-width:230px}.dek-banner{padding:18px;gap:16px}.dek-banner img{width:65px}.dek-banner h2{font-size:22px}.dek-step{min-width:90px;padding:9px;font-size:11px}}\n    @media(max-width:640px){.dek-hero{min-height:170px;padding:10px 8px}.dek-hero h2{font-size:32px;margin:12px 0}.dek-hero .dek-eyebrow{margin-top:0}.dek-hero p,.dek-hero-bottom{display:none}}\n    @media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}\n    </style>'))
    st.html(markup('<style>\n    [data-testid="stMainBlockContainer"]{max-width:1280px;padding:3rem 2.4rem}\n    .stApp::after{background:linear-gradient(105deg,rgba(250,246,239,.9),rgba(250,246,239,.72))}\n    h1,h2,h3{font-weight:750;line-height:1.35!important}\n    .st-key-login_card{position:relative;padding:32px 34px;border-radius:30px;border:1px solid #fffc;background:#fffdf9eb;box-shadow:0 28px 80px #4832231a;max-width:500px;margin-left:auto}\n    .st-key-login_card:before{content:"";height:4px;width:52px;background:#e76b28;border-radius:10px;position:absolute;top:0;left:34px}\n    .st-key-login_card [data-testid="stForm"]{background:transparent;border:0;padding:0!important;box-shadow:none}\n    .st-key-login_card h1{font-size:30px!important;letter-spacing:-.035em}\n    .st-key-login_card h3{font-size:20px!important;margin-top:4px}\n    section[data-testid="stMain"] h1#dek-steak{gap:14px}\n    section[data-testid="stMain"] h1#dek-steak::before{flex-basis:76px;height:82px}\n    .st-key-login_card [data-testid="stTabs"] [role="tablist"]{background:#eee6dc;border:0;border-radius:12px;padding:4px;gap:4px;margin:12px 0}\n    .st-key-login_card [data-testid="stTabs"] [role="tab"]{flex:1;justify-content:center;border-radius:9px;height:40px;font-size:13px}\n    .st-key-login_card [data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:#fffdf9;color:#aa491b;box-shadow:0 2px 8px #5b371212}\n    .st-key-login_card [data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none}\n    .st-key-login_card [data-testid="stExpander"]{background:transparent;border:0;border-top:1px solid #e8dfd4;border-radius:0;padding-top:8px;margin-top:8px}\n    .stTextInput input,.stTextArea textarea{min-height:46px;color:#332820}\n    button[kind="primary"],button[kind="primaryFormSubmit"]{min-height:48px;font-weight:700;letter-spacing:.015em}\n    button:focus-visible,.stTextInput input:focus-visible,.stTextArea textarea:focus-visible{outline:2px solid #b45423!important;outline-offset:3px}\n    [data-baseweb="select"] input:focus-visible{outline:none!important;box-shadow:none!important}\n    [data-baseweb="select"]:focus-within>div{outline:2px solid #b45423;outline-offset:2px}\n    .dek-hero{padding:65px 16px 30px;min-height:590px}\n    .dek-hero .dek-eyebrow{display:inline-flex;padding:8px 13px;border:1px solid #cdb8a0;border-radius:99px;font-size:10px;letter-spacing:.17em;background:#fff8ed70;margin:0}\n    .dek-hero h2{font-size:clamp(38px,4vw,56px);line-height:1.25!important;letter-spacing:-.055em;max-width:440px;margin:28px 0 20px}\n    .dek-hero h2 span{color:#b55325}.dek-hero p{font-size:16px;line-height:1.85;max-width:340px;color:#786151}\n    .dek-intro-steps{display:flex;gap:12px;margin:32px 0 0;max-width:420px}\n    .dek-intro-step{flex:1;border-top:1px solid #c9b59d;padding-top:13px}\n    .dek-intro-step b{display:block;font-size:10px;letter-spacing:.12em;color:#a6552c;margin-bottom:6px}\n    .dek-intro-step span{font-size:13px;font-weight:650;color:#4f3b2e}\n    .dek-hero-bottom{position:static;display:inline-block;margin-top:38px;background:transparent;border:0;padding:0;color:#9e826b;font-size:10px;letter-spacing:.12em}\n    .dek-auth-note{font-size:11px;color:#998574;line-height:1.8;text-align:center;padding-top:10px}\n    [data-testid="stSidebar"]{background:#f6f0e6ed;backdrop-filter:none;border-right:1px solid #fff9}\n    [data-testid="stSidebar"] [role="radiogroup"]{gap:6px}\n    [data-testid="stSidebar"] [role="radiogroup"] label{padding:9px 12px;border-radius:12px;transition:background .15s}\n    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#f8dfc9;color:#974016}\n    .dek-banner{background:#fffaf0e6;border:1px solid #fff;color:#35261b;border-radius:24px;box-shadow:0 8px 28px #54341a0a;padding:18px 24px}\n    .dek-banner img{width:70px}.dek-banner h2{color:#33271f;font-size:25px}.dek-banner p{color:#8b715d}\n    .dek-step-row{gap:0;border:1px solid #e5d5c1;border-radius:16px;background:#fffaf2bd;overflow:hidden}\n    .dek-step{border:0;border-radius:0;background:transparent;margin:0;padding:15px 20px;min-width:105px;text-align:center}\n    .dek-step.current{background:#f7dfc7;border:0;color:#a2491d}\n    .dek-step b{display:inline-flex;align-items:center;justify-content:center;width:23px;height:23px;border-radius:50%;background:#e9dfd1;color:#8c7462;font-size:10px}\n    .dek-step.current b{background:#b55524;color:white}\n    [class*="st-key-menu_card_"]{background:#fffdf9;border:1px solid #ece2d6;border-radius:22px;box-shadow:0 8px 25px #50371d08;overflow:hidden;transition:transform .18s,box-shadow .18s}\n    [class*="st-key-menu_card_"]:hover{transform:translateY(-3px);box-shadow:0 16px 30px #50371d12}\n    [class*="st-key-menu_card_"] [data-testid="stForm"]{border:0;padding:0!important;background:transparent;box-shadow:none}\n    [class*="st-key-menu_card_"] [data-testid="stExpander"]{border:0;background:#f8f3eb;border-radius:10px}\n    .dek-menu-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:4px 0 9px}\n    .dek-menu-category{font-size:10px;letter-spacing:.03em;background:#f4e5d3;color:#a36d40;padding:4px 9px;border-radius:99px}\n    .dek-menu-price{font-size:20px;font-weight:800;color:#aa4c1d;white-space:nowrap}\n    .dek-menu-title{font-size:19px!important;line-height:1.3;margin:7px 0;color:#35291f;min-height:25px}\n    .dek-menu-description{font-size:12px;color:#9b8471;line-height:1.7;min-height:41px;margin:8px 0 14px}\n    .dek-food-placeholder{height:155px;background:radial-gradient(ellipse at 50% 25%,#fcf6ed,#eee0ce);gap:0;position:relative;overflow:hidden}\n    .dek-food-placeholder:before{content:"";position:absolute;width:100px;height:100px;border-radius:50%;border:11px solid #fff9;box-shadow:0 9px 20px #83634619,inset 0 0 0 1px #dac6ab}\n    .dek-food-placeholder div{font-size:35px;z-index:1;filter:none;margin-top:2px}.dek-food-placeholder span{position:absolute;bottom:10px;font-size:9px;color:#aa9279;letter-spacing:.035em}\n    .dek-food-photo{height:175px;transition:transform .2s}.dek-table{min-height:115px;padding:12px;background:#fffaf3e8}\n    .dek-table.selected{border:2px solid #c26731;background:#fff1df;box-shadow:0 6px 16px #b6541a15}\n    .dek-table-photo{display:block;width:100%;height:110px;object-fit:cover;object-position:center 55%;border-radius:10px;margin-bottom:10px}\n    .dek-table strong{font-size:18px}.dek-table .state{font-size:10px}\n    .dek-footer{font-size:10px;color:#9e8a78;border-color:#cfbda6}\n    @media(max-width:800px){[data-testid="stMainBlockContainer"]{padding:1.5rem 1.1rem}.st-key-login_card{padding:24px}.dek-hero{padding:45px 8px 20px}.dek-hero h2{font-size:38px}.dek-intro-steps{gap:8px}.dek-intro-step span{font-size:11px}.dek-banner{padding:16px}.dek-step{padding:11px 9px;min-width:100px}}\n    @media(max-width:640px){.dek-hero{min-height:0;padding:12px 4px 20px}.dek-hero h2{font-size:36px;margin:18px 0 12px}.dek-hero p{display:block;font-size:13px;margin:0}.dek-intro-steps,.dek-hero-bottom{display:none}.st-key-login_card{max-width:none;margin:0;padding:24px 20px}.st-key-login_card h1{font-size:27px!important}.dek-step{font-size:10px;min-width:70px;padding:10px 6px}.dek-step b{margin-right:4px;width:19px;height:19px}}\n    @media(prefers-reduced-motion:reduce){[class*="st-key-menu_card_"]:hover{transform:none}}\n    </style>'))
    st.html(markup('<style>\n    .st-key-customer_toolbar{border:1px solid #e8d9c5;border-radius:16px;padding:10px 16px;background:#fffaf0e6;margin-bottom:16px;box-shadow:0 6px 20px #4b321008}\n    .st-key-customer_toolbar [data-testid="stCaptionContainer"]{padding-top:7px}\n    .dek-cart-summary{display:flex;align-items:center;justify-content:space-between;gap:18px;border:1px solid #e4d4bd;border-radius:18px;padding:20px;margin:12px 0;background:#fff4e2}\n    .dek-cart-summary span{font-size:12px;color:#8d735d}.dek-cart-summary strong{display:block;font-size:28px;color:#a64e23;font-weight:800}\n    .dek-stock-badge{display:inline-flex;padding:4px 10px;border-radius:99px;font-size:11px;background:#e7efdf;color:#4d6c3e;margin-bottom:10px}\n    .dek-stock-badge.off{background:#f5e0d8;color:#a54931}\n    [data-testid="stSegmentedControl"] button{border-radius:10px!important;font-size:11px!important}\n    [data-testid="stFileUploaderDropzone"]{border:1px dashed #c3a381!important;border-radius:16px;background:#fffaf1;padding:20px}\n    [role="dialog"]{max-width:720px!important;width:calc(100vw - 32px)!important;border-radius:24px!important;background:#fffdf9!important;border:1px solid #e3d2bd;box-shadow:0 30px 100px #22150c30}\n    [role="dialog"]:has(.st-key-password_recovery_panel){max-width:440px!important}\n    [class*="st-key-stock_card_"]{background:#fffdf9;border:1px solid #e5d9c9;border-radius:18px;padding:14px;box-shadow:0 5px 20px #4d301008}\n    [data-testid="stDialog"] [data-testid="stVerticalBlock"]{gap:.9rem}\n    .st-key-appearance_toolbar{margin-bottom:8px}\n    div:has(>.st-key-order_context){position:sticky;top:0;z-index:12}\n    .st-key-order_context{background:#fffaf2f5;border:1px solid #e5d2bc;border-radius:18px;padding:12px 16px;backdrop-filter:none;box-shadow:0 6px 20px #54321a0d;margin:12px 0}\n    .st-key-menu_category [role="radiogroup"]{flex-wrap:nowrap!important;overflow-x:auto;gap:8px!important;padding:4px 2px 8px;scrollbar-width:thin}\n    .st-key-menu_category [role="radiogroup"] label{flex:0 0 auto;margin:0!important;padding:7px 12px;border:1px solid #d7c7b3;border-radius:99px;background:#fffdf8;cursor:pointer}\n    .st-key-menu_category [role="radiogroup"] label>div:first-child{display:none}\n    .st-key-menu_category [role="radiogroup"] label p{font-size:12px!important;color:#694c35!important;white-space:nowrap;margin:0}\n    .st-key-menu_category [role="radiogroup"] label:has(input:checked){background:#f7ddc5;border-color:#c8753e}\n    .st-key-menu_category [role="radiogroup"] label:has(input:checked) p{color:#973f17!important;font-weight:700}\n    .st-key-menu_category [role="radiogroup"] label:has(input:focus-visible){outline:2px solid #c8753e;outline-offset:1px}\n    .st-key-sticky_basket{position:fixed!important;bottom:16px;right:28px;width:calc(100vw - 380px)!important;max-width:960px;z-index:20;background:#fffaf5f5;padding:14px 20px;border:1px solid #e1c2a5;border-radius:20px;box-shadow:0 10px 40px #4a2b2326;backdrop-filter:none}\n    .stApp:has(.st-key-sticky_basket) [data-testid="stMainBlockContainer"]{padding-bottom:160px}\n    .st-key-sticky_basket [data-testid="stVerticalBlock"]{gap:2px}\n    .st-key-sticky_basket [data-testid="stMarkdownContainer"] p{margin:0;font-size:16px}\n    .st-key-sticky_basket [data-testid="stCaptionContainer"] p{font-size:11px!important;margin:2px 0}\n    .st-key-sticky_basket button{min-height:46px!important}\n    @media(max-width:800px){.st-key-sticky_basket{width:calc(100vw - 24px)!important;right:12px;bottom:10px;padding:12px}.st-key-order_context{padding:10px}.st-key-sticky_basket [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:8px}.st-key-sticky_basket [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important}.st-key-sticky_basket [data-testid="stMarkdownContainer"] p{font-size:13px}.st-key-sticky_basket button p{font-size:12px!important}}\n    @media(max-width:640px){.st-key-order_context [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:8px}.st-key-order_context [data-testid="stColumn"]{min-width:0!important;flex:2 1 0!important}.st-key-order_context [data-testid="stColumn"]:last-child{flex:1 1 0!important}.st-key-order_context [data-testid="stWidgetLabel"] p{font-size:12px!important}}\n    @media(max-width:640px){div:has(>.st-key-order_context){top:54px}.st-key-table_gallery [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:10px}.st-key-table_gallery [data-testid="stColumn"]{min-width:0!important;flex:0 0 calc(50% - 5px)!important}.st-key-table_gallery .dek-table{padding:10px}.st-key-table_gallery .dek-table-photo{height:90px}}\n    [class*="st-key-drink_choices_"]{min-height:145px}\n    [class*="st-key-drink_choices_"] [role="radiogroup"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px!important}\n    [class*="st-key-drink_choices_"] [role="radiogroup"] label{width:100%;height:48px;box-sizing:border-box;justify-content:center;padding:6px!important}\n    .dek-menu-title{margin:8px 0!important;line-height:1.4!important}\n    .dek-menu-description{min-height:44px;margin:8px 0 14px!important}\n    [class*="st-key-menu_card_"] [data-testid="stWidgetLabel"] p{font-size:13px!important;line-height:1.6!important}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label>div:last-child{margin:0!important;padding:0!important}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label p{margin:0!important;line-height:1.5!important;text-align:center;white-space:normal}\n    [class*="st-key-menu_card_"] [data-testid="stExpander"] summary{padding:10px 12px!important;align-items:center;min-height:44px}\n    [class*="st-key-menu_card_"] [data-testid="stExpander"] summary p{font-size:12px!important;line-height:1.55!important;margin:0!important}\n    [class*="st-key-menu_card_"] [data-testid="stForm"]{gap:14px}\n    [class*="st-key-menu_card_"] [role="radiogroup"]{gap:8px!important;flex-wrap:wrap}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label{margin:0!important;padding:8px 11px;border:1px solid #d6c3ae;border-radius:10px;background:#fffaf3;color:#5f4937!important;cursor:pointer;min-height:38px}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label>div:first-child{display:none}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label p{font-size:12px!important;color:#5f4937!important}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label:has(input:checked){background:#fbe1c9;border-color:#be682f}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label:has(input:checked) p{color:#873e19!important;font-weight:700}\n    [class*="st-key-menu_card_"] [role="radiogroup"] label:has(input:focus-visible){outline:2px solid #c27036;outline-offset:2px}\n    .stApp{color-scheme:light}\n    [data-testid="stMarkdownContainer"],[data-testid="stWidgetLabel"],label{color:#40352d}\n    [data-testid="stCaptionContainer"] p{color:#776656!important}\n    [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div,textarea{background:#fffdf9!important;color:#40352d!important;border-color:#cfc0ad!important}\n    input,textarea{color:#40352d!important}\n    input::placeholder,textarea::placeholder{color:#8c7a69!important;opacity:1}\n    button[kind="secondary"],button[kind="secondaryFormSubmit"]{background:#fffaf2!important;color:#594232!important;border-color:#d6c4b1!important}\n    button[kind="tertiary"]{color:#a34d21!important}\n    button[kind="primary"] [data-testid="stMarkdownContainer"],button[kind="primaryFormSubmit"] [data-testid="stMarkdownContainer"]{color:#fff!important}\n    button[kind="secondary"] [data-testid="stMarkdownContainer"],button[kind="tertiary"] [data-testid="stMarkdownContainer"]{color:inherit!important}\n    [data-testid="stSidebar"] h1{font-size:23px!important;letter-spacing:-.03em}\n    [data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:12px}\n    .st-key-sidebar_navigation{margin-top:16px}\n    .st-key-sidebar_navigation [data-testid="stWidgetLabel"] p{font-size:11px!important;letter-spacing:.04em;color:#7c6858!important;margin-bottom:8px}\n    .st-key-sidebar_navigation [role="radiogroup"]{gap:8px!important}\n    .st-key-sidebar_navigation [role="radiogroup"] label{position:relative;display:flex;align-items:center;gap:12px;min-height:50px;padding:12px 14px!important;margin:0!important;border:1px solid transparent;border-radius:14px!important;color:#574638!important;cursor:pointer;transition:background .16s,border-color .16s}\n    .st-key-sidebar_navigation [role="radiogroup"] label>div:first-child{display:none}\n    .st-key-sidebar_navigation [role="radiogroup"] label p{font-size:14px!important;font-weight:550!important;color:inherit!important;line-height:1.5}\n    .st-key-sidebar_navigation [role="radiogroup"] label::before{content:"";flex:0 0 19px;width:19px;height:19px;background:currentColor;mask:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cpath%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20d%3D%22M4%205h16v14H4zM4%2010h16M9%2010v9%22%2F%3E%3C%2Fsvg%3E\') center/contain no-repeat;opacity:.8}\n    .st-key-sidebar_navigation [role="radiogroup"] label:nth-child(2)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cpath%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20d%3D%22M3%204h2l3%2012h11l2-8H6M10%2020h.01M18%2020h.01%22%2F%3E%3C%2Fsvg%3E\')}\n    .st-key-sidebar_navigation [role="radiogroup"] label:nth-child(3)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cpath%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20d%3D%22M6%203h12v18l-3-2-3%202-3-2-3%202zM9%208h6M9%2012h6%22%2F%3E%3C%2Fsvg%3E\')}\n    .st-key-sidebar_navigation [role="radiogroup"] label:last-child::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Ccircle%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20cx%3D%2212%22%20cy%3D%228%22%20r%3D%224%22%2F%3E%3Cpath%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20d%3D%22M4%2021v-2a8%208%200%200%201%2016%200v2%22%2F%3E%3C%2Fsvg%3E\')}\n    .st-key-sidebar_navigation [role="radiogroup"] label:hover{background:#e9dfd2;border-color:#ddccba}\n    .st-key-sidebar_navigation [role="radiogroup"] label:has(input:checked){background:#fce7d6!important;border-color:#e8bc99;color:#9c431c!important;box-shadow:0 3px 12px #773a1409}\n    .st-key-sidebar_navigation [role="radiogroup"] label:has(input:checked)::after{content:"";position:absolute;left:0;top:14px;bottom:14px;width:3px;border-radius:4px;background:#c45624}\n    .st-key-sidebar_navigation [role="radiogroup"] label:has(input:focus-visible){outline:2px solid #bf5a27;outline-offset:2px}\n    </style>'))
    st.html(markup('<style>\n    .st-key-report_filters{padding:18px 20px;background:#fffdf9e8;border:1px solid #e4d5c4;border-radius:20px;box-shadow:0 8px 24px #5b35100a;margin-bottom:6px}\n    .st-key-report_period [role="radiogroup"]{display:flex;flex-wrap:wrap;gap:5px!important;background:#eee6dc;border:1px solid #e3d5c5;padding:5px;border-radius:13px;width:fit-content}\n    .st-key-report_period [role="radiogroup"] label{position:relative;margin:0!important;padding:9px 18px;border-radius:9px;cursor:pointer;transition:background .18s,box-shadow .18s}\n    .st-key-report_period [role="radiogroup"] label>div:first-child{display:none}\n    .st-key-report_period [role="radiogroup"] label p{color:#715b48!important;white-space:nowrap;margin:0;font-size:14px!important;font-weight:600}\n    .st-key-report_period [role="radiogroup"] label:hover{background:#ffffff80}\n    .st-key-report_period [role="radiogroup"] label:has(input:checked){background:#fffdf9;box-shadow:0 2px 8px #5b37121a}\n    .st-key-report_period [role="radiogroup"] label:has(input:checked) p{color:#b04b1d!important;font-weight:750}\n    .st-key-report_period [role="radiogroup"] label:has(input:focus-visible){outline:2px solid #c8753e;outline-offset:1px}\n    @media(max-width:640px){.st-key-report_filters{padding:14px}.st-key-report_period [role="radiogroup"] label{padding:9px 12px}}\n</style>'))
    if dark:
        st.html(markup('<style>\n        .st-key-report_filters{background:#171e29ed;border-color:#384456;box-shadow:0 8px 24px #0002}\n        .st-key-report_period [role="radiogroup"]{background:#101722;border-color:#344154}\n        .st-key-report_period [role="radiogroup"] label p{color:#c8d5e7!important}\n        .st-key-report_period [role="radiogroup"] label:hover{background:#263247}\n        .st-key-report_period [role="radiogroup"] label:has(input:checked){background:#46321c;box-shadow:inset 0 0 0 1px #ba8646}\n        .st-key-report_period [role="radiogroup"] label:has(input:checked) p{color:#ffd7a0!important}\n</style>'))
        st.html(markup('<style>\n        .stApp{background:#0b0d11!important;color:#e7e9ed}\n        .stApp::after{background:linear-gradient(105deg,rgba(11,13,17,.94),rgba(11,13,17,.84))}\n        .stApp::before{filter:saturate(.5)}\n        h1,h2,h3{color:#f3f0e8!important}\n        [data-testid="stMarkdownContainer"],[data-testid="stWidgetLabel"],label{color:#e0e3e8!important}\n        [data-testid="stCaptionContainer"] p{color:#9da3ae!important}\n        .st-key-login_card{background:#141820df;border:1px solid #ffffff16;box-shadow:0 25px 80px #0007}\n        .st-key-login_card:before{background:#f59e0b}\n        .dek-hero h2 span,.dek-menu-price{color:#f2b64b}\n        .dek-hero p{color:#aeb3bd}.dek-hero .dek-eyebrow{color:#e6b56d;border-color:#96723555;background:#f59e0b0a}\n        .dek-intro-step{border-color:#ffffff20}.dek-intro-step b{color:#c59552}.dek-intro-step span{color:#cfd3da}.dek-hero-bottom,.dek-auth-note{color:#8a909b}\n        .st-key-login_card [data-testid="stTabs"] [role="tablist"]{background:#090b0f;border:1px solid #ffffff0d}\n        .st-key-login_card [data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:#8f241b;color:#fff;box-shadow:0 3px 16px #a2222228}\n        .st-key-login_card [data-testid="stExpander"]{border-top-color:#ffffff14}\n        .stTextInput [data-baseweb="input"],.stNumberInput [data-baseweb="input"],.stTextArea textarea,[data-baseweb="select"]>div{background:#0d1016!important;border-color:#ffffff16!important;color:#e7e9ed!important}\n        input,textarea{color:#e7e9ed!important;background:transparent!important}\n        [data-baseweb="base-input"]{background:#0d1016!important;color:#e7e9ed!important}\n        [data-testid="stTextInput"] button{background:#0d1016!important;color:#a6afbe!important}\n        [data-testid="stTextInput"] button svg{fill:currentColor!important}\n        [data-testid="stAlertContainer"]{background:#17212c!important;border:1px solid #ffffff16!important;color:#d2dce9!important}\n        [data-baseweb="select"] span,[data-baseweb="select"] div{color:#e7e9ed}\n        [data-baseweb="select"] svg{fill:#b6bbc5}\n        .stNumberInput button{background:#1a202a!important;color:#ddd!important}\n        button[kind="primary"],button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#a63122,#731b16)!important;box-shadow:0 5px 18px #b91c1c25}\n        button[kind="secondary"],button[kind="secondaryFormSubmit"]{background:#171c25!important;color:#dedfe3!important;border-color:#ffffff19!important}\n        [data-testid="stSidebar"]{background:#101319ed;border-right-color:#ffffff0d}\n        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#f59e0b17;color:#efb54b!important}\n        .dek-banner{background:#141820dd;border-color:#ffffff12;box-shadow:0 8px 25px #0003}.dek-banner p{color:#9fa5af}.dek-banner .dek-eyebrow{color:#d5a35f!important}\n        .dek-step-row{background:#10141be6;border-color:#ffffff12}.dek-step{color:#8c94a1}.dek-step.current{background:#f59e0b15;color:#eab256}.dek-step b{background:#252c38;color:#9fa6b3}.dek-step.current b{background:#f59e0b;color:#17130e}\n        [class*="st-key-menu_card_"]{background:#141820;border-color:#ffffff12;box-shadow:0 8px 25px #0003}\n        .dek-menu-category{background:#f59e0b15;color:#d5aa69}.dek-menu-description{color:#929aa8}\n        [data-testid="stExpander"]{background:#141820;border-color:#ffffff12}\n        [data-testid="stForm"]{background:#141820;border-color:#ffffff14}\n        [class*="st-key-menu_card_"] [data-testid="stExpander"]{background:#0d1118}\n        .dek-table{background:#141820;border-color:#ffffff15;color:#f3f0e8}.dek-table span{color:#9ca4b0}.dek-table.free{border-color:#66835055}.dek-table.selected{border-color:#d69339;background:#f59e0b10}.dek-table.busy{background:#12151b}.dek-table .state{background:#65864c20;color:#a4c18f}.dek-table.busy .state{background:#ffffff09;color:#949ba6}\n        [data-testid="stMetric"]{background:#141820;border-color:#ffffff12;box-shadow:none}[data-testid="stMetricLabel"]{color:#a4aab5}[data-testid="stMetricValue"]{color:#efb756}\n        .st-key-customer_toolbar{background:#141820e8;border-color:#ffffff14;box-shadow:0 6px 20px #0002}\n        .dek-cart-summary{background:#f59e0b0e;border-color:#f59e0b33}.dek-cart-summary span{color:#a4a8b2}.dek-cart-summary strong{color:#edb34c}\n        .dek-empty{background:#151a22;border-color:#ffffff20;color:#afb5bf}.dek-empty a{color:#e4aa51!important}\n        [data-testid="stFileUploaderDropzone"]{background:#10141b;border-color:#9d763e!important;color:#b9bdc7}\n        [role="dialog"]{background:#141820!important;border-color:#ffffff19;box-shadow:0 30px 100px #0008}\n        [role="dialog"] button:not([kind]){color:#c9d0db!important}\n        [class*="st-key-stock_card_"]{background:#141820;border-color:#ffffff16;box-shadow:0 5px 20px #0002}\n        .dek-stock-badge{background:#607f3526;color:#b2c894}.dek-stock-badge.off{background:#b6312722;color:#e5a394}\n        .dek-food-placeholder{background:#1c2430;color:#9fa9b8}.dek-food-placeholder:before{border-color:#ffffff0a;box-shadow:0 9px 20px #0003}.dek-food-placeholder span{color:#828b99}\n        .dek-footer{color:#7f8999;border-color:#ffffff12}\n        [data-testid="stTabs"] [role="tab"]{color:#a6aebb}[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#e8b452}\n        .dek-receipt h2{color:#201a16!important}.dek-receipt,.dek-receipt h3{color:#222!important}\n        .stApp{color-scheme:dark}\n        [data-testid="stSidebarCollapsedControl"]{background:#243044!important;color:#f7d199!important;border:1px solid #53617a}\n        [data-testid="stSidebarCollapsedControl"] button,[data-testid="stSidebarCollapseButton"] button{color:#f7d199!important}\n        [data-testid="stSidebarCollapsedControl"] [data-testid="stIconMaterial"],[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]{color:#f7d199!important}\n        .st-key-order_context{background:#141d2bf5;border-color:#3e4b60;box-shadow:0 6px 20px #0003}\n        .st-key-menu_category [role="radiogroup"] label{background:#1a2636;border-color:#43536b}\n        .st-key-menu_category [role="radiogroup"] label p{color:#c8d5e7!important}\n        .st-key-menu_category [role="radiogroup"] label:has(input:checked){background:#46321c;border-color:#ba8646}\n        .st-key-menu_category [role="radiogroup"] label:has(input:checked) p{color:#ffd7a0!important}\n        .st-key-sticky_basket{background:#172131f5;border-color:#4b566a;box-shadow:0 10px 40px #0007}\n        .st-key-sidebar_navigation [data-testid="stWidgetLabel"] p{color:#a9b4c5!important}\n        .st-key-sidebar_navigation [role="radiogroup"] label{color:#c8d2df!important;background:transparent}\n        .st-key-sidebar_navigation [role="radiogroup"] label:hover{background:#1b2533!important;border-color:#344155}\n        .st-key-sidebar_navigation [role="radiogroup"] label:has(input:checked){background:#34291b!important;color:#ffd18a!important;border-color:#795a32;box-shadow:none}\n        .st-key-sidebar_navigation [role="radiogroup"] label:has(input:checked)::after{background:#ffb85b}\n        .st-key-sidebar_navigation [role="radiogroup"] label [data-testid="stMarkdownContainer"]{color:inherit!important}\n        .st-key-sidebar_navigation [role="radiogroup"] label p{color:#c8d2df!important}\n        .st-key-sidebar_navigation [role="radiogroup"] label:has(input:checked) p{color:#ffd18a!important}\n        [data-testid="stCaptionContainer"] p{color:#b0bac9!important}\n        input::placeholder,textarea::placeholder{color:#98a6ba!important;opacity:1}\n        button[kind="tertiary"],button[kind="tertiaryFormSubmit"]{color:#ffc477!important}\n        button:disabled{opacity:.65!important}\n        button[kind="primary"] [data-testid="stMarkdownContainer"],button[kind="primaryFormSubmit"] [data-testid="stMarkdownContainer"]{color:#fff!important}\n        [data-testid="stSegmentedControl"] button{background:#1b2432!important;color:#dbe4f0!important;border-color:#3c4a60!important}\n        [data-testid="stSegmentedControl"] button[aria-pressed="true"], [data-testid="stSegmentedControl"] button[aria-selected="true"]{background:#62411e!important;color:#ffe1b0!important;border-color:#c48a42!important}\n        [data-testid="stSegmentedControl"] button [data-testid="stMarkdownContainer"]{color:inherit!important}\n        [data-baseweb="popover"] [role="listbox"],[data-baseweb="menu"],ul[role="listbox"]{background:#192230!important;color:#e5edf8!important;border:1px solid #3a475a}\n        [role="option"]{color:#e5edf8!important;background:#192230!important}\n        [role="option"]:hover,[role="option"][aria-selected="true"]{background:#344154!important}\n        [data-testid="stExpander"] summary{color:#dce5f1!important}\n        [data-testid="stExpander"] summary svg{fill:#bac7d9!important}\n        [data-testid="stExpander"] summary,[class*="st-key-menu_card_"] [data-testid="stExpander"] summary{background:#192331!important;color:#e5edf8!important;border-radius:10px}\n        [data-testid="stExpander"] summary:hover{background:#263348!important}\n        [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"],[data-testid="stExpander"] summary p{color:#e5edf8!important}\n        [class*="st-key-menu_card_"] [role="radiogroup"] label{background:#192331!important;border-color:#46556b!important}\n        [class*="st-key-menu_card_"] [role="radiogroup"] label p{color:#dce6f4!important}\n        [class*="st-key-menu_card_"] [role="radiogroup"] label:has(input:checked){background:#47321b!important;border-color:#d6994b!important}\n        [class*="st-key-menu_card_"] [role="radiogroup"] label:has(input:checked) p{color:#ffdaa2!important}\n        [data-testid="stTabs"] [role="tablist"]{border-color:#354154}\n        [data-testid="stTabs"] [role="tab"] [data-testid="stMarkdownContainer"]{color:inherit!important}\n        [data-testid="stFileUploaderDropzone"] button{color:#e5edf8!important;background:#253144!important;border-color:#46566e!important}\n        [data-testid="stAlertContainer"] a,.stApp a{color:#ffc477}\n        .dek-menu-description,.dek-footer{color:#aeb9c8}\n        .dek-table.busy{opacity:1}.dek-table.busy .state{color:#bec8d6;background:#27313f}\n        .dek-step{color:#b0bccd}.dek-step b{color:#c3cede}\n        [data-testid="stSidebar"] svg{color:#c5d0df}\n        </style>'))

    st.html(markup('<style>\n    .st-key-owner_page [role="radiogroup"]{width:100%;gap:9px!important}\n    .st-key-owner_page [role="radiogroup"] label{width:100%!important;box-sizing:border-box;min-height:72px!important;padding:14px 32px 14px 17px!important;gap:14px!important;background:#fffdf98c;border:1px solid #e5d8c8!important;border-radius:16px!important;box-shadow:0 3px 10px #6e421605;transition:background .18s,border-color .18s,box-shadow .18s}\n    .st-key-owner_page [role="radiogroup"] label p{font-size:14px!important;font-weight:700!important;line-height:1.4;margin:0}\n    .st-key-owner_page [role="radiogroup"] label p::after{display:block;margin-top:4px;font-size:11px;font-weight:400;line-height:1.4;color:#887463;letter-spacing:0}\n    .st-key-owner_page [role="radiogroup"] label::before{flex-basis:22px;width:22px;height:22px;opacity:1;color:#a36b3e}\n    .st-key-owner_page [role="radiogroup"] label::after{content:"›"!important;position:absolute;right:14px;left:auto!important;top:50%!important;bottom:auto!important;transform:translateY(-50%);width:auto!important;height:auto;background:transparent!important;font-size:22px;color:#b59b84;border-radius:0}\n    .st-key-owner_page [role="radiogroup"] label:hover{background:#fffdf9!important;border-color:#d9ab83!important;box-shadow:0 5px 16px #6e421611}\n    .st-key-owner_page [role="radiogroup"] label:has(input:checked){background:linear-gradient(110deg,#ffe4cf,#fff5e9)!important;border-color:#e2a779!important;box-shadow:inset 3px 0 #d26427,0 5px 16px #9e4c1510}\n    .st-key-owner_page [role="radiogroup"] label:has(input:checked)::before{color:#bc521f}\n    .st-key-owner_page [role="radiogroup"] label:has(input:checked) p::after{color:#9a6846}\n.st-key-owner_page [role="radiogroup"] label:nth-child(1)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M9%205H5v16h14V5h-4M9%203h6v4H9zM8%2012h8M8%2016h5%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E\')}\n.st-key-owner_page [role="radiogroup"] label:nth-child(1) p::after{content:"คิวครัวและการชำระเงิน"}\n.st-key-owner_page [role="radiogroup"] label:nth-child(2)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%2020h16M7%2016v-5M12%2016V5M17%2016V8%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E\')}\n.st-key-owner_page [role="radiogroup"] label:nth-child(2) p::after{content:"ดูรายรับและสรุปยอดขาย"}\n.st-key-owner_page [role="radiogroup"] label:nth-child(3)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%203v6a2%202%200%200%200%204%200V3M6%203v18M18%203c-3%203-3%207%200%209h2V3zM20%2012v9%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E\')}\n.st-key-owner_page [role="radiogroup"] label:nth-child(3) p::after{content:"ราคา รูปภาพ และสถานะขาย"}\n.st-key-owner_page [role="radiogroup"] label:nth-child(4)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M3%209h18v5H3zM5%2014v7M19%2014v7M6%203v6M18%203v6M6%205h12%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E\')}\n.st-key-owner_page [role="radiogroup"] label:nth-child(4) p::after{content:"ที่นั่งและสถานะโต๊ะ"}\n.st-key-owner_page [role="radiogroup"] label:nth-child(5)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%206h16M4%2012h16M4%2018h16M8%203v6M16%209v6M10%2015v6%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E\')}\n.st-key-owner_page [role="radiogroup"] label:nth-child(5) p::after{content:"ข้อมูลร้านและอีเมล"}\n.st-key-owner_page [role="radiogroup"] label:nth-child(6)::before{mask-image:url(\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%227%22%20r%3D%224%22%2F%3E%3Cpath%20d%3D%22M4%2021v-2a8%208%200%200%201%2016%200v2%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E\')}\n.st-key-owner_page [role="radiogroup"] label:nth-child(6) p::after{content:"ข้อมูลส่วนตัวและรหัสผ่าน"}\n</style>'))
    if dark:
        st.html(markup('<style>\n    .st-key-owner_page [role="radiogroup"] label{background:#171f2b!important;border-color:#303d50!important;box-shadow:0 3px 10px #0001}\n    .st-key-owner_page [role="radiogroup"] label::before{color:#c4a279}\n    .st-key-owner_page [role="radiogroup"] label p::after{color:#a9b7c9}\n    .st-key-owner_page [role="radiogroup"] label:hover{background:#202d3e!important;border-color:#7b6247!important}\n    .st-key-owner_page [role="radiogroup"] label:has(input:checked){background:linear-gradient(110deg,#48331d,#302719)!important;border-color:#9b7445!important;box-shadow:inset 3px 0 #ffb85b,0 5px 16px #0002}\n    .st-key-owner_page [role="radiogroup"] label:has(input:checked)::before{color:#ffd18a}\n    .st-key-owner_page [role="radiogroup"] label:has(input:checked) p::after{color:#dfbd90}\n</style>'))

    st.html(markup('<style>\n    .dek-catalog{--catalog-bg:#fffdf9;--catalog-head:#f0e7db;--catalog-line:#e8ddcf;--catalog-ink:#3d3027;--catalog-muted:#8a7361;--catalog-hover:#fff3e6;background:var(--catalog-bg);color:var(--catalog-ink);border:1px solid var(--catalog-line);border-radius:20px;overflow:hidden;box-shadow:0 8px 28px #54341a09}\n    .dek-catalog table{width:100%;border-collapse:collapse;font-size:14px}\n    .dek-catalog th{text-align:left;background:var(--catalog-head);color:var(--catalog-muted);font-size:12px;font-weight:600;padding:15px 20px;border-bottom:1px solid var(--catalog-line)}\n    .dek-catalog td{padding:14px 20px;border-bottom:1px solid var(--catalog-line);vertical-align:middle}\n    .dek-catalog tr:last-child td{border-bottom:0}.dek-catalog tbody tr:hover{background:var(--catalog-hover)}\n    .dek-catalog .catalog-food{display:flex;align-items:center;gap:14px;font-weight:650}\n    .dek-catalog img{width:56px;height:56px;border-radius:13px;object-fit:cover;background:var(--catalog-head);flex-shrink:0}\n    .dek-catalog .catalog-placeholder{width:56px;height:56px;border-radius:13px;background:var(--catalog-head);display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0}\n    .dek-catalog .catalog-category{color:var(--catalog-muted);font-size:13px}\n    .dek-catalog .catalog-price{font-weight:750;white-space:nowrap;font-variant-numeric:tabular-nums}\n    .dek-catalog .catalog-state{display:inline-flex;align-items:center;gap:6px;background:#e7f2e6;color:#38683d;border:1px solid #c9dfc6;padding:5px 10px;border-radius:99px;font-size:12px;white-space:nowrap}\n    .dek-catalog .catalog-state::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}\n    .dek-catalog .catalog-state.closed{background:#eee6df;color:#8b7060;border-color:#dfd1c6}\n    .st-key-menu_editor [data-testid="stForm"]{padding:24px!important;border-radius:22px!important}\n    .st-key-menu_editor h3{font-size:20px!important;margin-bottom:12px}\n    .st-key-menu_editor [data-testid="stNumberInput"]>div{background:transparent!important}\n    @media(max-width:640px){.dek-catalog th,.dek-catalog td{padding:12px 10px}.dek-catalog table{font-size:12px}.dek-catalog img,.dek-catalog .catalog-placeholder{width:40px;height:40px}.dek-catalog .catalog-food{gap:8px}.dek-catalog .catalog-category{font-size:11px}.dek-catalog .catalog-state{font-size:10px;padding:4px 6px}.st-key-menu_editor [data-testid="stForm"]{padding:16px!important}}\n</style>'))
    if dark:
        st.html(markup('<style>\n    .dek-catalog{--catalog-bg:#171e29;--catalog-head:#202b3b;--catalog-line:#334054;--catalog-ink:#e6edf5;--catalog-muted:#aebdd0;--catalog-hover:#202d3e;box-shadow:0 8px 28px #0002}\n    .dek-catalog .catalog-state{background:#20372b;color:#9dd6ad;border-color:#375643}\n    .dek-catalog .catalog-state.closed{background:#332b26;color:#d6b69e;border-color:#59483b}\n</style>'))

    st.html(markup('<style>\n    .st-key-admin_workspace{--admin-panel:#fffdf9;--admin-border:#e3d5c5;--admin-muted:#826e5e;--admin-well:#eee5da}\n    .st-key-admin_workspace [data-testid="stTabs"] [role="tablist"]{background:var(--admin-well);padding:5px;border-radius:14px;border:1px solid var(--admin-border);gap:5px;overflow-x:auto;white-space:nowrap}\n    .st-key-admin_workspace [data-testid="stTabs"] [role="tab"]{height:43px;padding:0 18px;border-radius:10px;font-size:14px;font-weight:650;flex-shrink:0;color:var(--admin-muted)!important}\n    .st-key-admin_workspace [data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:var(--admin-panel);color:#b04b1d!important;box-shadow:0 2px 8px #59351a15}\n    .st-key-admin_workspace [data-testid="stTabs"] [data-baseweb="tab-highlight"],.st-key-admin_workspace [data-testid="stTabs"] [data-baseweb="tab-border"]{display:none}\n    .st-key-admin_workspace [data-testid="stForm"]{padding:24px!important;border-radius:22px!important;border-color:var(--admin-border)!important;background:var(--admin-panel)!important;box-shadow:0 8px 24px #54341a08}\n    .st-key-admin_workspace [data-testid="stForm"] [data-testid="stWidgetLabel"] p{font-weight:600}\n    .st-key-admin_workspace [data-testid="stExpander"]{background:var(--admin-panel);border-color:var(--admin-border);border-radius:18px;margin-bottom:8px}\n    .st-key-admin_workspace [data-testid="stExpander"] summary{padding:16px 18px!important;min-height:58px;font-weight:650}\n    .st-key-admin_workspace [data-testid="stExpander"] summary p{font-weight:650!important}\n    .st-key-admin_workspace [data-testid="stFileUploader"] section{background:var(--admin-well)!important;border:1px dashed var(--admin-border)!important;border-radius:14px!important}\n    .st-key-admin_workspace [data-testid="stMetric"]{padding:20px;border-radius:20px;border-color:var(--admin-border)!important;box-shadow:0 6px 20px #54341a08}\n    .st-key-queue_filters,.st-key-account_profile{background:var(--admin-panel,#fffdf9);border:1px solid var(--admin-border,#e3d5c5);border-radius:20px;padding:18px 20px;box-shadow:0 6px 20px #54341a08}\n    .dek-data-table{overflow:auto;max-height:580px;scrollbar-width:thin;margin:12px 0 20px}\n    .dek-data-table table{min-width:100%;width:max-content;max-width:none}\n    .dek-data-table th{position:sticky;top:0;z-index:1;white-space:nowrap}\n    .dek-data-table td{max-width:340px;overflow-wrap:anywhere;line-height:1.65}\n    .dek-data-table td:last-child{min-width:110px}\n    .dek-data-table .catalog-state.neutral{background:#f2e5d5;color:#85552d;border-color:#dfc9af}\n    @media(max-width:640px){.st-key-admin_workspace [data-testid="stForm"]{padding:16px!important}.st-key-admin_workspace [data-testid="stTabs"] [role="tab"]{padding:0 13px;font-size:12px}.st-key-admin_workspace [data-testid="stMetric"]{padding:12px}.st-key-admin_workspace [data-testid="stMetricValue"]{font-size:26px!important}}\n</style>'))
    if dark:
        st.html(markup('<style>\n    .st-key-admin_workspace{--admin-panel:#171e29;--admin-border:#334054;--admin-muted:#b4c1d2;--admin-well:#101722}\n    .st-key-admin_workspace [data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:#49331e;color:#ffd7a0!important;box-shadow:inset 0 0 0 1px #9b7445}\n    .st-key-admin_workspace [data-testid="stExpander"] summary{background:#1e2939!important;color:#e6edf5!important}\n    .st-key-admin_workspace [data-testid="stFileUploader"] section *{color:#c8d5e7}\n    .st-key-account_profile{background:#171e29;border-color:#334054}\n    .dek-data-table .catalog-state.neutral{background:#3b2f23;color:#e7bf8e;border-color:#6a5034}\n</style>'))

    st.html(markup('<style>.st-key-sales_chart{background:var(--admin-panel,#fffdf9);border:1px solid var(--admin-border,#e3d5c5);border-radius:22px;padding:22px 24px;margin:10px 0 16px;box-shadow:0 8px 24px #54341a08}.st-key-sales_chart h3{font-size:20px!important;margin:0}.st-key-sales_chart [data-testid="stVegaLiteChart"]{border-radius:14px;overflow:hidden}@media(max-width:640px){.st-key-sales_chart{padding:16px 12px}}</style>'))

    st.html(markup('<style>\n    [class*="st-key-best_seller_"]{background:var(--admin-panel,#fffdf9);border:1px solid var(--admin-border,#e3d5c5);border-radius:20px!important;padding:18px!important;box-shadow:0 6px 20px #54341a08;height:100%}\n    [class*="st-key-best_seller_"] [data-testid="stMetric"]{background:transparent!important;border:0!important;box-shadow:none!important;padding:4px 0!important}\n    [class*="st-key-best_seller_"] [data-testid="stImage"] img{width:100%!important;height:140px;object-fit:cover;border-radius:14px}\n    [class*="st-key-best_seller_"] .dek-food-photo{height:140px!important;margin-bottom:0!important}\n    [class*="st-key-best_seller_"] [data-testid="stMetricLabel"]{font-weight:650}\n</style>'))

    inject_polish(dark)

    st.html(markup('<style>\n    .st-key-owner_order_view [role="radiogroup"]{display:flex;gap:6px!important;padding:5px;background:var(--dek-surface-2);border:1px solid var(--dek-line);border-radius:13px;width:fit-content}\n    .st-key-owner_order_view [role="radiogroup"] label{margin:0!important;padding:9px 18px;border-radius:9px;color:var(--dek-muted);cursor:pointer}\n    .st-key-owner_order_view [role="radiogroup"] label>div:first-child{display:none}\n    .st-key-owner_order_view [role="radiogroup"] label p{color:inherit!important;margin:0;font-weight:650}\n    .st-key-owner_order_view [role="radiogroup"] label:has(input:checked){background:var(--dek-accent-soft);color:var(--dek-accent);box-shadow:0 2px 8px #0001}\n    .st-key-owner_order_view [role="radiogroup"] label:has(input:focus-visible){outline:2px solid var(--dek-accent);outline-offset:2px}\n    .dek-price .row span,.dek-tracker-hint{color:var(--dek-muted)!important}\n    .dek-price .row.total span{color:var(--dek-ink)!important}\n    .dek-ticket-items .opts{line-height:1.5}\n    .st-key-admin_workspace [data-testid="stMetricValue"]{font-size:clamp(22px,2.3vw,30px)!important}\n</style>'))


def featured_menu_html(recommendations):  # สร้างแถบเมนูแนะนำเลื่อนวนพร้อมรูปและข้อมูลที่ escape แล้ว
    from core import money
    recommendations=[(menu,photo) for menu,photo in recommendations if menu['available'] and photo][:5]
    if not recommendations: return ''
    count=len(recommendations)
    slides=[]
    sequence=recommendations+recommendations[:1] if count>1 else recommendations
    for index,(menu,photo) in enumerate(sequence):
        uri=display_uri(photo,1000)
        hidden=' aria-hidden="true"' if index==count else ''
        slides.append(f"""{markup('<article class="dek-featured-slide"')}{hidden}{markup('>\n        <div class="dek-featured-copy"><span class="dek-featured-kicker">เมนูแนะนำ</span>\n        <h3>')}{escape(menu['name'])}{markup('</h3><p>')}{escape(menu['description'])}{markup('</p>\n        <strong>฿')}{money(menu['price'])}{markup('</strong><small>ราคารวม VAT 7% แล้ว</small></div>\n        <img src="')}{uri}{markup('" alt="')}{escape(menu['name'], quote=True)}{markup('" class="dek-featured-image"></article>')}""")
    keyframes=[]
    if count>1:
        for index in range(count):
            keyframes.append(f'{index*100/count:.4f}%,{(index+.78)*100/count:.4f}%{{transform:translateX(-{index*100}%);}}')
        keyframes.append(f'100%{{transform:translateX(-{count*100}%);}}')
    animation=f'animation:dek-featured-cycle {count*8}s ease-in-out infinite;' if count>1 else ''
    return '''<style>
    .dek-featured{margin-top:28px;border-radius:22px;background:#1c1816;border:1px solid #8b69413b;box-shadow:0 18px 38px #38271922;overflow:hidden;color:#fff3e3}
    .dek-featured-heading{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid #fff2;font-size:12px;color:#e7d3b9}
    .dek-featured-heading span:last-child{font-size:10px;letter-spacing:.08em;color:#c09c72}
    .dek-featured-viewport{overflow:hidden;outline-offset:-3px}
    .dek-featured-track{display:flex;width:100%;will-change:transform;__ANIMATION__}
    .dek-featured-slide{position:relative;display:flex;align-items:center;flex:0 0 100%;min-width:0;min-height:252px;box-sizing:border-box;background:radial-gradient(ellipse at 70% 90%,#6a4121,#211b18 65%);overflow:hidden}
    .dek-featured-copy{position:relative;z-index:1;width:54%;box-sizing:border-box;padding:24px 18px}
    .dek-featured-kicker{font-size:9px;letter-spacing:.16em;color:#f0b967;font-weight:700}
    .dek-featured-copy h3{font-size:23px!important;line-height:1.25!important;color:#fff3e3!important;letter-spacing:-.035em;margin:12px 0 10px;overflow-wrap:anywhere}
    .dek-featured-copy p{display:block;font-size:11px;color:#d1bea9;line-height:1.7;margin:0 0 14px}
    .dek-featured-copy strong{display:block;font-size:25px;font-weight:800;color:#ffc06d}
    .dek-featured-copy small{display:block;font-size:9px;color:#c9b7a4;margin-top:4px}
    .dek-featured-image{position:absolute;right:0;top:0;bottom:0;width:46%;height:100%;object-fit:cover;object-position:center;mask-image:linear-gradient(to right,transparent,#000 18%);filter:drop-shadow(0 12px 15px #0005)}
    .dek-featured-foot{padding:11px 18px;font-size:10px;color:#cbb59e;border-top:1px solid #ffffff12}
    .dek-featured:hover .dek-featured-track,.dek-featured:focus-within .dek-featured-track{animation-play-state:paused}
    @keyframes dek-featured-cycle{__KEYFRAMES__}
    .st-key-featured_showcase{position:relative}
    .dek-featured{margin-top:0;border-radius:28px;border-color:#f9d6a22b;box-shadow:0 24px 60px #35221530;transition:box-shadow .25s,border-color .25s}
    .dek-featured-slide{min-height:380px;isolation:isolate}
    .dek-featured-slide::after{content:"";position:absolute;inset:0;z-index:0;background:linear-gradient(90deg,#0e0c0aec 0%,#1d130cbb 40%,#120d0620 78%,#160e0820)}
    .dek-featured-copy{width:70%;padding:42px 52px;transition:transform .3s}
    .dek-featured-kicker{display:inline-block;padding:7px 12px;border:1px solid #e9b87666;border-radius:99px;background:#30201488;font-size:11px;letter-spacing:0;color:#ffd69d}
    .dek-featured-copy h3{font-size:clamp(26px,3vw,38px)!important;margin:18px 0 12px;max-width:320px}
    .dek-featured-copy p{font-size:13px;max-width:250px;color:#e8d5c1}
    .dek-featured-copy strong{font-size:32px}.dek-featured-copy small{color:#dfcbb7;font-size:10px}
    .dek-featured-image{width:100%;mask-image:none;filter:none;z-index:-1;transition:transform .7s ease}
    .dek-featured:hover{border-color:#e7ae5c99;box-shadow:0 30px 65px #2e1b1342}
    .dek-featured:hover .dek-featured-image{transform:scale(1.04)}
    .dek-featured:hover .dek-featured-copy{transform:translateY(-3px)}
    .st-key-featured_controls{position:absolute!important;top:calc(50% - 24px);left:12px;width:calc(100% - 24px)!important;z-index:4;pointer-events:none}
    .st-key-featured_controls button[kind="secondary"]{pointer-events:auto;width:38px!important;min-height:42px!important;padding:0!important;border-radius:13px!important;background:#17130dab!important;color:#fff5e6!important;border:1px solid #ffe6bd55!important;backdrop-filter:blur(12px);box-shadow:0 4px 15px #0003}
    .st-key-featured_controls button[kind="secondary"] [data-testid="stMarkdownContainer"],.st-key-featured_controls button[kind="secondary"] p{font-size:28px!important;color:#fff5e6!important;line-height:1}
    .st-key-featured_controls button[kind="secondary"]:hover{background:#b86c2e!important;border-color:#ffc278!important}
    @media(max-width:640px){.dek-featured-slide{min-height:310px}.dek-featured-copy{width:85%;padding:34px 48px}.dek-featured-copy h3{font-size:27px!important}.dek-featured-copy p{font-size:12px}.dek-featured-copy strong{font-size:28px}.dek-featured-image{object-position:60% center}}
    @media(prefers-reduced-motion:reduce){.dek-featured:hover .dek-featured-image,.dek-featured:hover .dek-featured-copy{transform:none}}
    @media(prefers-reduced-motion:reduce){.dek-featured-track{animation:none!important;will-change:auto}.dek-featured-viewport{overflow-x:auto;scroll-snap-type:x mandatory}.dek-featured-slide{scroll-snap-align:start}}
    </style><section class="dek-featured" aria-label="เมนูแนะนำ">
    <div class="dek-featured-viewport" tabindex="0" aria-label="เมนูแนะนำเลื่อนอัตโนมัติ หยุดเมื่อชี้เมาส์หรือโฟกัส"><div class="dek-featured-track">__SLIDES__</div></div>
    </section>'''.replace('__ANIMATION__',animation).replace('__KEYFRAMES__',''.join(keyframes)).replace('__SLIDES__',''.join(slides))


def hero(recommendations=None):  # สร้างส่วนต้อนรับหน้าร้าน
    st.html(markup('<style>\n    .dek-hero{min-height:0!important;padding:20px 2px 18px!important}\n    .dek-hero h2{margin:0!important;font-size:clamp(34px,4vw,52px)!important;max-width:none;line-height:1.25!important}\n    .dek-hero h2 span{display:block;margin-top:8px}\n    .st-key-login_card{transition:box-shadow .25s,border-color .25s,transform .25s}\n    .st-key-login_card:hover{box-shadow:0 30px 80px #5630182b;border-color:#e6c3a0;transform:translateY(-2px)}\n    .st-key-login_card:focus-within{border-color:#d78e57;box-shadow:0 22px 70px #9a511b26}\n    .st-key-login_card [data-baseweb="input"],.st-key-login_card [data-baseweb="base-input"]{transition:border-color .2s,box-shadow .2s}\n    .st-key-login_card [data-baseweb="input"]:focus-within{box-shadow:0 0 0 3px #dc82351a;border-color:#c76a2e!important}\n    .st-key-login_card h1{font-size:28px!important}.st-key-login_card h3{font-size:18px!important}\n    @media(max-width:640px){.dek-hero{padding-top:8px!important}.dek-hero h2{font-size:34px!important}}\n    @media(prefers-reduced-motion:reduce){.st-key-login_card:hover{transform:none}}\n    </style><section class="dek-hero"><h2>มื้ออร่อย<span>เริ่มที่ Dek Steak</span></h2></section>'))


def banner(name, caption='อร่อยง่าย ๆ ในแบบของคุณ'):  # สร้างหัวแบนเนอร์ชื่อร้านและข้อความประกอบ
    st.html(f"""{markup('<div class="dek-banner"><img src="')}{image_uri(ASSETS / 'logo.png')}{markup('" alt="โลโก้ร้าน">\n    <div><div class="dek-eyebrow" style="color:#f2bc8d">FRESH FROM THE GRILL</div><h2>')}{escape(name)}{markup('</h2><p>')}{escape(tr(caption))}{markup('</p></div></div>')}""")


def steps(current,fulfillment="dine_in"):  # แสดงขั้นตอนสั่งอาหารตามรูปแบบรับอาหาร
    labels = ['รับกลับบ้าน', 'เลือกอาหาร', 'ชำระเงิน', 'รับอาหาร'] if fulfillment=='takeaway' else ['เลือกโต๊ะ', 'เลือกอาหาร', 'ชำระเงิน', 'อิ่มอร่อย']
    st.html('<div class="dek-step-row">' + ''.join((f"""<div class="dek-step {('current' if i == current else '')}"><b>0{i + 1}</b>{text}</div>""" for i, text in enumerate(labels))) + '</div>')


def table_card(table, selected=False):  # สร้างการ์ดโต๊ะพร้อมจำนวนที่นั่งและสถานะ
    free = table['enabled'] and (not table['order_id'] or table.get('can_add',False))
    state = 'โต๊ะของคุณ · สั่งเพิ่มได้' if table.get('can_add') else 'ว่าง พร้อมรับคุณ' if free else 'ปิดใช้งาน' if not table['enabled'] else 'มีลูกค้าแล้ว'
    photo=ASSETS/'seating'/f'seats-{table["seats"]}.png'
    visual=f"""{markup('<img class="dek-table-photo" src="')}{image_uri(photo)}{markup('" alt="โต๊ะ ')}{table['seats']}{markup(' ที่นั่ง">')}""" if photo.exists() else '🪑'
    st.html(f"""{markup('<div class="dek-table ')}{('free' if free else 'busy')}{markup(' ')}{('selected' if selected else '')}{markup('">')}{visual}{markup('<strong>')}{escape(table['name'])}{markup('</strong><span>')}{table['seats']}{markup(' ที่นั่ง</span><br><div class="state">')}{('เลือกแล้ว' if selected else state)}{markup('</div></div>')}""")


def menu_info(menu):  # แสดงชื่อ หมวด รายละเอียดและราคาเมนูตามภาษา
    from core import money
    st.html('<div class="dek-menu-info">'+f"""{markup('<div class="dek-menu-meta"><span class="dek-menu-category">')}{escape(tr(menu['category']))}{markup('</span><span class="dek-menu-price">฿')}{money(menu['price'])}{markup('</span></div><h3 class="dek-menu-title">')}{escape(menu_name(menu['name']))}{markup('</h3><p class="dek-menu-description">')}{escape(menu_description(menu['description']))}{markup('</p>')}"""+'</div>')


def food_image(data, category):  # แสดงภาพอาหารหรือภาพแทนเมื่อยังไม่มีรูป
    if data:
        uri = display_uri(data)
        style='object-fit:contain;background:#f6f3ec' if category=='เครื่องดื่ม' else 'object-fit:cover'
        st.html(f"""{markup('<img class="dek-food-photo" style="')}{style}{markup('" src="')}{uri}{markup('" alt="ภาพเมนูอาหาร">')}""")
    else:
        icon = '🥩' if category.startswith('สเต๊ก') else '🍝' if category=='พาสต้า' else '🥤' if category=='เครื่องดื่ม' else '🥗' if category=='สลัด' else '🍟'
        st.html(f"""{markup('<div class="dek-food-placeholder"><div>')}{icon}{markup('</div><span>รอภาพจริงจากทางร้าน</span></div>')}""")


def stock_card_html(item, photo=None):  # กำหนดกรอบภาพและพื้นที่ชื่อให้เท่ากัน โดยคงรูปต้นฉบับและแสดงชื่อเต็มใน tooltip
    from core import money
    name=escape(menu_name(item['name']),quote=True)
    if photo:
        fit='contain' if item['category']=='เครื่องดื่ม' else 'cover'
        visual=f'<img class="dek-stock-photo" src="{display_uri(photo,260)}" alt="{name}" style="object-fit:{fit}">'
    else:
        visual=f'<div class="dek-stock-photo dek-stock-placeholder" role="img" aria-label="{escape(tr("ยังไม่มีรูปอาหาร"),quote=True)}">🍽</div>'
    state=tr('พร้อมขาย' if item['available'] else 'หยุดขาย')
    badge='dek-stock-badge'+('' if item['available'] else ' off')
    return (f'<div class="dek-stock-body">{visual}<h3 class="dek-stock-title" title="{name}">{name}</h3>'
            f'<p class="dek-stock-price">฿{money(item["price"])} {escape(tr("รวม VAT 7% แล้ว"))}</p>'
            f'<div class="{badge}">{escape(state)}</div></div>')


def menu_catalog(menus, photos):  # สร้างตารางเมนูสำหรับเจ้าของพร้อมรูป ราคาและสถานะ
    """Read-only menu overview, styled in both themes and escaped for owner input."""
    from core import money
    rows=[]
    for item in menus:
        data=photos.get(f'menu_photo_{item["id"]}')
        visual=('<img src="'+display_uri(data,160)+'" alt="ภาพ '+escape(menu_name(item['name']),quote=True)+'">') if data else '<span class="catalog-placeholder" aria-label="ยังไม่มีรูปอาหาร">🍽</span>'
        state='เปิดขาย' if item['available'] else 'หยุดขาย'
        cls='' if item['available'] else ' closed'
        rows.append(f"""{markup('<tr><td><div class="catalog-food">')}{visual}{markup('<span>')}{escape(menu_name(item['name']))}{markup('</span></div></td><td class="catalog-category">')}{escape(tr(item['category']))}{markup('</td><td class="catalog-price">฿')}{money(item['price'])}{markup('</td><td><span class="catalog-state')}{cls}{markup('">')}{state}{markup('</span></td></tr>')}""")
    st.html('<div class="dek-catalog"><table aria-label="รายการอาหารทั้งหมด"><thead><tr><th scope="col">เมนูอาหาร</th><th scope="col">หมวด</th><th scope="col">ราคารวม VAT</th><th scope="col">สถานะ</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')


def admin_table(rows, label='รายการข้อมูล'):  # สร้างตารางข้อมูลเจ้าของและ escape ข้อความก่อนแสดง HTML
    """Escaped HTML overview with a theme-aware header and scrollable long data."""
    if not rows:
        st.info(tr('ยังไม่มีข้อมูลในรายการนี้'))
        return
    headers=list(rows[0])
    head=''.join(f'<th scope="col">{escape(str(key))}</th>' for key in headers)
    body=[]
    for row in rows:
        cells=[]
        for key in headers:
            value=row.get(key)
            text='—' if value is None else str(value)
            if key=='สถานะ':
                cls='' if text in ('ว่าง','เปิดขาย') else ' closed' if text in ('ปิด','หยุดขาย') else ' neutral'
                content=f'<span class="catalog-state{cls}">{escape(tr(text))}</span>'
            else: content=escape(tr(text))
            cells.append('<td>'+content+'</td>')
        body.append('<tr>'+''.join(cells)+'</tr>')
    st.html(f'<div class="dek-catalog dek-data-table" tabindex="0" aria-label="{escape(label, quote=True)}"><table aria-label="{escape(label, quote=True)}"><thead><tr>{head}</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div>')


def sales_chart_spec(rows, dark=False):  # กำหนด Vega-Lite ให้แกนเริ่มศูนย์ แท่งขนาดเหมาะสมและสีตรงธีม
    """Daily totals are summed in satang before chart conversion; axis always starts at zero."""
    from datetime import datetime
    from core import BANGKOK
    days={}
    for row in rows:
        day=datetime.fromtimestamp(row['paid_at'],BANGKOK).strftime('%Y-%m-%d')
        bucket=days.setdefault(day,{'satang':0,'orders':0})
        bucket['satang']+=row['total']
        bucket['orders']+=1
    values=[{'day':day,'label':datetime.strptime(day,'%Y-%m-%d').strftime('%d/%m/%Y'),'amount':value['satang']/100,'orders':value['orders']} for day,value in sorted(days.items())]
    ink='#c8d5e7' if dark else '#796553'
    accent='#ffb45e' if dark else '#db702c'
    grid='#334054' if dark else '#e8ded2'
    ceiling=max([v['amount'] for v in values] or [1])*1.22
    base={'data':{'values':values},'encoding':{
        'x':{'field':'label','type':'ordinal','sort':[v['label'] for v in values],'title':None,'scale':{'padding':0.6},'axis':{'labelAngle':0,'labelOverlap':'greedy','labelPadding':12,'ticks':False,'domain':False}},
        'y':{'field':'amount','type':'quantitative','title':'บาท','scale':{'zero':True,'domainMin':0,'domainMax':max(ceiling,1)},'axis':{'format':',.0f','tickCount':5,'domain':False,'ticks':False,'grid':True}},
        'tooltip':[{'field':'label','type':'nominal','title':'วันที่'},{'field':'amount','type':'quantitative','title':'ยอดรับเงิน (บาท)','format':',.2f'},{'field':'orders','type':'quantitative','title':'ออเดอร์','format':',d'}]
    }}
    bars={'mark':{'type':'bar','color':accent,'cornerRadiusTopLeft':7,'cornerRadiusTopRight':7,'size':min(38,max(1,600/max(len(values),1)))}}
    layers=[bars]
    if len(values)<=14:
        layers.append({'mark':{'type':'text','dy':-12,'color':accent,'fontSize':15,'fontWeight':650},'encoding':{'text':{'field':'amount','type':'quantitative','format':',.2f'}}})
    return {**base,'layer':layers,'height':280,'background':'transparent','padding':{'top':24,'left':4,'right':8,'bottom':4},'config':{'view':{'stroke':None},'axis':{'labelColor':ink,'titleColor':ink,'gridColor':grid,'gridDash':[3,5],'labelFontSize':14,'titleFontSize':14,'titlePadding':14,'labelLimit':100},'text':{'font':'sans-serif'}},'usermeta':{'embedOptions':{'actions':False}}}


def contact_footer(shop_name='Dek Steak', dark=False):  # แสดงช่องทาง Facebook Instagram และโทรศัพท์ท้ายเว็บ
    palette='--contact-bg:#171e29;--contact-line:#354256;--contact-ink:#edf2f8;--contact-muted:#b4c1d2;--contact-link:#ffcc95;--contact-hover:#263248' if dark else '--contact-bg:#fffdf9e8;--contact-line:#e4d4c1;--contact-ink:#3f3026;--contact-muted:#826e5e;--contact-link:#a75223;--contact-hover:#fff0e0'
    icons={
        'facebook':'<path d="M14 21v-8h3l.5-4H14V7c0-1 .3-2 2-2h2V1.5a24 24 0 0 0-3-.2c-3 0-5 1.8-5 5V9H7v4h3v8z" fill="currentColor"/>',
        'instagram':'<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8" fill="currentColor"/>',
        'phone':'<path d="M5 3h4l2 5-3 2a16 16 0 0 0 6 6l2-3 5 2v4c0 1-1 2-2 2C10 21 3 14 3 5c0-1 1-2 2-2z"/>'}
    def icon(name):  # เลือกสัญลักษณ์ช่องทางติดต่อสำหรับแสดงใน footer
        from urllib.parse import quote
        svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'+icons[name].replace('currentColor','black')+'</svg>'
        return f'<span class="dek-contact-icon" style="mask:url(\'data:image/svg+xml,{quote(svg,safe="")}\') center/contain no-repeat" aria-hidden="true"></span>'
    st.html('<style>\n    .dek-contact{background:var(--contact-bg);border:1px solid var(--contact-line);border-radius:24px;padding:28px 30px;margin-top:40px;box-shadow:0 8px 28px #54341a08;color:var(--contact-ink);letter-spacing:0}\n    .dek-contact-top{display:flex;align-items:center;justify-content:space-between;gap:28px;flex-wrap:wrap}\n    .dek-contact-brand{display:flex;align-items:center;gap:16px}.dek-contact-brand img{width:68px;height:72px;object-fit:contain}\n    .dek-contact h2{color:var(--contact-ink)!important;font-size:22px!important;margin:0!important;line-height:1.4}\n    .dek-contact p{color:var(--contact-muted)!important;font-size:13px;margin:6px 0 0;line-height:1.6}\n    .dek-contact-links{display:flex;gap:10px;flex-wrap:wrap}\n    .dek-contact a{display:inline-flex;align-items:center;gap:10px;padding:12px 15px;border:1px solid var(--contact-line);border-radius:13px;color:var(--contact-link)!important;text-decoration:none!important;background:var(--contact-bg);font-size:14px;font-weight:600;transition:background .18s,border-color .18s}\n    .dek-contact-icon{display:inline-block;width:22px;height:22px;flex:0 0 22px;background:currentColor}\n    .dek-contact a:hover{background:var(--contact-hover);border-color:var(--contact-link)}.dek-contact a:focus-visible{outline:2px solid var(--contact-link);outline-offset:3px}\n    .dek-contact-bottom{border-top:1px solid var(--contact-line);padding-top:16px;margin-top:24px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:var(--contact-muted);font-size:11px}\n    @media(max-width:640px){.dek-contact{padding:22px 18px;margin-top:28px}.dek-contact-top{gap:20px}.dek-contact-links{width:100%;display:grid;grid-template-columns:1fr 1fr}.dek-contact-links a:last-child{grid-column:1/-1;justify-content:center}.dek-contact a{justify-content:center;padding:12px 10px}.dek-contact-bottom{line-height:1.6}.dek-contact-brand img{width:54px;height:60px}}\n    </style>' + f"""{markup('<footer class="dek-contact" style="')}{palette}{markup('" aria-label="ติดต่อเจ้าของร้าน"><div class="dek-contact-top"><div class="dek-contact-brand"><img src="')}{image_uri(ASSETS / 'logo.png')}{markup('" alt="โลโก้ร้าน ')}{escape(shop_name, quote=True)}{markup('"><div><h2>')}{escape(shop_name)}{markup('</h2><p>ติดต่อเจ้าของร้าน</p></div></div><nav class="dek-contact-links" aria-label="ช่องทางติดต่อเจ้าของร้าน"><a href="https://www.facebook.com/share/1Ejw5arGzw/" target="_blank" rel="noopener noreferrer" aria-label="ติดต่อเจ้าของร้านทาง Facebook (เปิดแท็บใหม่)">')}{icon('facebook')}{markup('<span>Facebook</span></a><a href="https://instagram.com/yodsaphonr_u?xtok=dDRreHlxMTdybnJ6" target="_blank" rel="noopener noreferrer" aria-label="ติดต่อเจ้าของร้านทาง Instagram (เปิดแท็บใหม่)">')}{icon('instagram')}{markup('<span>Instagram</span></a><a href="tel:+66654461479" aria-label="โทรหาเจ้าของร้าน 0654461479">')}{icon('phone')}{markup('<span>065 446 1479</span></a></nav></div><div class="dek-contact-bottom"><span>')}{escape(shop_name)}{markup(' / GOOD FOOD. GOOD MOOD.</span><span>สอบถามร้านผ่านช่องทางด้านบน</span></div></footer>')}""")


# ---------------------------------------------------------------------------
# UI polish layer + extra components (appended; the original styles above are kept)
# ---------------------------------------------------------------------------
USE_WEB_FONT = False  # set False for fully offline use; the font stack still falls back to system Thai fonts

_FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap');"

POLISH_CSS = '''<style>
__FONT_IMPORT__
:root{--dek-font:'Noto Sans Thai','Sarabun','Prompt','Loma','Tahoma',system-ui,-apple-system,'Segoe UI',sans-serif;
 --dek-surface:#fffdf9;--dek-surface-2:#f6efe4;--dek-line:#e6d9c8;--dek-ink:#33271f;--dek-muted:#6b5646;
 --dek-accent:#c4501a;--dek-accent-soft:#fbe3cf;--dek-shadow:0 6px 20px #54341a0d;
 --dek-warn-bg:#fff0cc;--dek-warn:#855400;--dek-info-bg:#e2edfb;--dek-info:#1d58a0;--dek-ok-bg:#e3f1e1;--dek-ok:#2c6a37;
 --dek-cook-bg:#fde2cf;--dek-cook:#a13d0d;--dek-teal-bg:#dcf0ed;--dek-teal:#1b6862;--dek-done-bg:#ece6dd;--dek-done:#65584b;
 --dek-bad-bg:#fbdfda;--dek-bad:#a1372a}
html{scroll-behavior:smooth}
::selection{background:#f8c79b;color:#2b1c12}
.stApp,[data-testid="stMarkdownContainer"],[data-testid="stWidgetLabel"],button,input,textarea,[data-baseweb="select"],[data-baseweb="tab"]{font-family:var(--dek-font)}
.stApp p,.stApp li{line-height:1.7}

@keyframes dek-fade{from{opacity:0}to{opacity:1}}
button:active{transform:scale(.985)}
.stButton button[kind="secondary"]:hover,.stDownloadButton button:hover{border-color:var(--dek-accent)!important;color:var(--dek-accent)!important}
[data-testid="stAlert"],[data-testid="stAlertContainer"]{border-radius:14px}
.stApp [data-testid="stExpander"] summary{background:var(--dek-surface-2)!important;color:var(--dek-ink)!important;padding:14px 16px}
.stApp [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"],.stApp [data-testid="stExpander"] summary p{color:var(--dek-ink)!important}
.stApp [data-testid="stExpander"] summary svg{fill:var(--dek-ink)!important}
.stApp [data-testid="stExpander"] summary:hover{background:var(--dek-accent-soft)!important}
[data-testid="stDataFrame"]{border-radius:16px;overflow:hidden;border:1px solid var(--dek-line)}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:#cdb89f;border-radius:99px;border:2px solid transparent;background-clip:content-box}
.dek-section{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin:6px 0 18px}
.dek-section .eyebrow{font-size:11px;letter-spacing:.18em;font-weight:800;color:var(--dek-accent);text-transform:uppercase}
.dek-section h2{margin:4px 0 0!important;font-size:clamp(24px,2.4vw,32px)!important}
.dek-section p{margin:6px 0 0;color:var(--dek-muted);font-size:14px}
.dek-status{display:inline-flex;align-items:center;gap:7px;padding:5px 12px;border-radius:99px;font-size:12px;font-weight:650;line-height:1.4;white-space:nowrap;background:var(--dek-done-bg);color:var(--dek-done)}
.dek-status i{width:7px;height:7px;border-radius:50%;background:currentColor}
.dek-status.s-awaiting_payment{background:var(--dek-warn-bg);color:var(--dek-warn)}
.dek-status.s-submitted{background:var(--dek-info-bg);color:var(--dek-info)}
.dek-status.s-paid{background:var(--dek-ok-bg);color:var(--dek-ok)}
.dek-status.s-preparing{background:var(--dek-cook-bg);color:var(--dek-cook)}
.dek-status.s-preparing i{animation:dek-pulse 1.4s ease-in-out infinite}
.dek-status.s-served{background:var(--dek-teal-bg);color:var(--dek-teal)}
.dek-status.s-cancelled{background:var(--dek-bad-bg);color:var(--dek-bad)}
@keyframes dek-pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(1.5)}}
.dek-track{background:var(--dek-surface);border:1px solid var(--dek-line);border-radius:20px;padding:18px 14px 14px;margin:8px 0 14px;box-shadow:var(--dek-shadow)}
.dek-tracker{list-style:none;margin:0;padding:0;display:flex}
.dek-tracker li{flex:1;position:relative;text-align:center;font-size:12px;color:var(--dek-muted);padding-top:36px;min-width:0}
.dek-tracker li::before{content:attr(data-n);position:absolute;top:0;left:50%;transform:translateX(-50%);z-index:1;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:750;background:var(--dek-surface-2);border:2px solid var(--dek-line);box-sizing:border-box}
.dek-tracker li::after{content:"";position:absolute;top:13px;left:calc(-50% + 18px);right:calc(50% + 18px);height:2px;background:var(--dek-line)}
.dek-tracker li:first-child::after{display:none}
.dek-tracker li.done,.dek-tracker li.current{color:var(--dek-ink);font-weight:650}
.dek-tracker li.done::before{content:"✓";background:var(--dek-accent);border-color:var(--dek-accent);color:#fff}
.dek-tracker li.done::after,.dek-tracker li.current::after{background:var(--dek-accent)}
.dek-tracker li.current::before{background:var(--dek-surface);border-color:var(--dek-accent);color:var(--dek-accent);box-shadow:0 0 0 4px var(--dek-accent-soft)}
.dek-tracker-hint{text-align:center;font-size:13px;color:var(--dek-muted);margin:12px 0 0}
.dek-tracker-cancelled{display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:14px;background:var(--dek-bad-bg);color:var(--dek-bad);font-weight:650;font-size:14px;margin:8px 0 14px}
.dek-deadline{background:var(--dek-warn-bg);color:var(--dek-warn);border-radius:16px;padding:14px 18px;margin:10px 0}
.dek-deadline-top{display:flex;justify-content:space-between;align-items:baseline;gap:12px;font-size:13px;font-weight:650}
.dek-deadline-top strong{font-size:22px;font-variant-numeric:tabular-nums}
.dek-deadline-bar{height:7px;border-radius:99px;background:#0000001a;margin:10px 0 8px;overflow:hidden}
.dek-deadline-bar span{display:block;height:100%;border-radius:99px;background:currentColor}
.dek-deadline small{font-size:12px;opacity:.9}
.dek-deadline.urgent{background:var(--dek-bad-bg);color:var(--dek-bad)}
.dek-price{background:var(--dek-surface);border:1px solid var(--dek-line);border-radius:18px;padding:6px 18px;box-shadow:var(--dek-shadow);margin:10px 0}
.dek-price .row{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:11px 0;border-bottom:1px dashed var(--dek-line);font-size:14px;color:var(--dek-muted)}
.dek-price .row b{color:var(--dek-ink);font-variant-numeric:tabular-nums;font-weight:650}
.dek-price .row.total{border:0;font-size:15px;color:var(--dek-ink);font-weight:700}
.dek-price .row.total b{font-size:24px;color:var(--dek-accent);font-weight:800}
.dek-empty-state{text-align:center;padding:38px 20px;border:1px dashed var(--dek-line);border-radius:22px;background:var(--dek-surface-2);color:var(--dek-muted);margin:12px 0}
.dek-empty-state .ico{font-size:38px;line-height:1;margin-bottom:10px}
.dek-empty-state strong{display:block;font-size:16px;color:var(--dek-ink);margin-bottom:4px}
.dek-empty-state p{margin:0;font-size:13px}
.dek-ticket{background:var(--dek-surface);border:1px solid var(--dek-line);border-left:5px solid var(--dek-ok);border-radius:18px;padding:16px 18px;box-shadow:var(--dek-shadow);margin:10px 0}
.dek-ticket.late{border-left-color:#e0a010}.dek-ticket.over{border-left-color:#d1432f}
.dek-ticket header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding-bottom:12px;border-bottom:1px dashed var(--dek-line)}
.dek-ticket-table{font-size:26px;font-weight:800;letter-spacing:-.02em;color:var(--dek-ink);margin-right:10px}
.dek-ticket header small{color:var(--dek-muted);font-size:12px}
.dek-ticket-time{text-align:right;font-size:12px;color:var(--dek-ok);font-weight:650;line-height:1.2}
.dek-ticket-time b{display:block;font-size:26px;font-variant-numeric:tabular-nums}
.dek-ticket.late .dek-ticket-time{color:#9a6a00}.dek-ticket.over .dek-ticket-time{color:var(--dek-bad)}
.dek-ticket-items{list-style:none;margin:12px 0 0;padding:0;display:grid;gap:12px}
.dek-ticket-items li{display:flex;gap:12px;align-items:flex-start}
.dek-ticket-items .qty{flex:0 0 auto;min-width:38px;text-align:center;padding:4px 8px;border-radius:10px;background:var(--dek-accent-soft);color:var(--dek-accent);font-weight:800;font-size:15px}
.dek-ticket-items strong{font-size:15px;color:var(--dek-ink)}
.dek-ticket-items .opts{display:flex;flex-wrap:wrap;gap:6px;margin-top:5px}
.dek-chip{padding:3px 10px;border-radius:99px;background:var(--dek-surface-2);border:1px solid var(--dek-line);font-size:12px;color:var(--dek-ink)}
.dek-allergy{display:inline-flex;gap:6px;margin-top:6px;padding:5px 10px;border-radius:10px;background:var(--dek-bad-bg);color:var(--dek-bad);font-size:12px;font-weight:650}
.dek-ticket footer{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:14px;padding-top:12px;border-top:1px dashed var(--dek-line);font-size:12px;color:var(--dek-muted)}
.dek-ticket .order-note{margin-top:12px}
@media(max-width:640px){.dek-tracker li{font-size:10px;padding-top:34px}.dek-tracker li::after{left:calc(-50% + 16px);right:calc(50% + 16px)}.dek-ticket{padding:14px}.dek-ticket-table{font-size:22px}}
@media(prefers-reduced-motion:reduce){[data-testid="stMainBlockContainer"]{animation:none}.dek-status.s-preparing i{animation:none}}
</style>'''

POLISH_DARK_CSS = '''<style>
:root{--dek-surface:#171e29;--dek-surface-2:#1e2939;--dek-line:#334054;--dek-ink:#e6edf5;--dek-muted:#bdc9d8;
 --dek-accent:#ffb45e;--dek-accent-soft:#46321c;--dek-shadow:0 6px 20px #0003;
 --dek-warn-bg:#40331a;--dek-warn:#f2c46b;--dek-info-bg:#1b3350;--dek-info:#8fbdf2;--dek-ok-bg:#1f3a2a;--dek-ok:#9bd7ac;
 --dek-cook-bg:#46291a;--dek-cook:#ffb184;--dek-teal-bg:#17383a;--dek-teal:#92d8d0;--dek-done-bg:#2a3240;--dek-done:#b8c3d2;
 --dek-bad-bg:#47221f;--dek-bad:#ffa89b}
.dek-tracker li.done::before{color:#17130e}
.dek-ticket.late .dek-ticket-time{color:#f2c46b}
::-webkit-scrollbar-thumb{background:#46556b;background-clip:content-box}
</style>'''


def inject_polish(dark=False):  # เพิ่ม CSS รายละเอียดขององค์ประกอบ ตัวหนังสือและธีมมืด
    css = POLISH_CSS.replace('__FONT_IMPORT__', _FONT_IMPORT if USE_WEB_FONT else '').replace('</style>', TYPOGRAPHY_CSS+ALIGNMENT_CSS+STOCK_CARD_CSS+MENU_CARD_CSS+'</style>')
    st.html(css)
    if dark:
        st.html(POLISH_DARK_CSS)


_TRACK_STEPS = ['แจ้งชำระ', 'ร้านตรวจเงิน', 'รอครัว', 'กำลังปรุง', 'เสิร์ฟ', 'เสร็จสิ้น']
_TRACK_INDEX = {'awaiting_payment': 0, 'submitted': 1, 'paid': 2, 'preparing': 3, 'served': 4, 'completed': 6}
_TRACK_HINT = {
    'awaiting_payment': 'กรุณาชำระเงินแล้วกดแจ้งชำระ',
    'submitted': 'ร้านกำลังตรวจสอบการชำระเงิน',
    'paid': 'ชำระเงินแล้ว รอครัวเริ่มปรุง',
    'preparing': 'ครัวกำลังปรุงอาหารของคุณ',
    'served': 'เสิร์ฟแล้ว ขอให้อร่อย',
    'completed': 'ขอบคุณที่ใช้บริการ',
}


def section_header(title, subtitle='', eyebrow=''):  # สร้างหัวข้อหน้าและข้อความอธิบายให้จัดแนวเดียวกัน
    """Consistent page heading (all text escaped)."""
    eye = f'<div class="eyebrow">{escape(eyebrow)}</div>' if eyebrow else ''
    sub = f'<p>{escape(tr(subtitle))}</p>' if subtitle else ''
    st.html(f"""{markup('<div class="dek-section"><div>')}{eye}{markup('<h2>')}{escape(tr(title))}{markup('</h2>')}{sub}{markup('</div></div>')}""")


def status_badge_html(status,fulfillment="dine_in"):  # สร้าง HTML ป้ายสถานะโดยเลือกคำให้ตรงรูปแบบรับอาหาร
    from core import STATUSES
    key = status if status in STATUSES else 'unknown'
    label = STATUSES.get(status, str(status))
    if fulfillment=='takeaway': label={'served':'พร้อมรับอาหาร','completed':'รับอาหารแล้ว'}.get(status,label)
    return f'<span class="dek-status s-{escape(key, quote=True)}"><i></i>{escape(tr(label))}</span>'


def status_badge(status,fulfillment='dine_in'):  # นำป้ายสถานะไปแสดงบนหน้าจอ Streamlit
    st.html(status_badge_html(status, fulfillment))


def order_tracker_html(status, fulfillment="dine_in"):  # สร้างแถบความคืบหน้าออเดอร์ตามสถานะ
    if status == 'cancelled':
        return markup('<div class="dek-tracker-cancelled" role="status">✕ &nbsp;รายการนี้ถูกยกเลิก</div>')
    if status not in _TRACK_INDEX:
        return markup('<div class="dek-tracker-cancelled" role="status">ไม่พบสถานะรายการ</div>')
    current = _TRACK_INDEX[status]
    items = []
    labels=list(_TRACK_STEPS)
    if fulfillment=='takeaway': labels[4]='พร้อมรับ';labels[5]='รับอาหารแล้ว'
    for i, label in enumerate(labels):
        state = 'done' if i < current else 'current' if i == current else ''
        aria = ' aria-current="step"' if state == 'current' else ''
        items.append(f'<li class="{state}" data-n="{i + 1}"{aria}>{escape(tr(label))}</li>')
    hint = _TRACK_HINT.get(status, '')
    if fulfillment=='takeaway': hint={'served':'อาหารพร้อมแล้ว กรุณามารับที่ร้าน','completed':'รับอาหารแล้ว ขอบคุณที่ใช้บริการ'}.get(status,hint)
    hint_html = f'<p class="dek-tracker-hint">{escape(tr(hint))}</p>' if hint else ''
    return f"""{markup('<section class="dek-track" aria-label="สถานะรายการ"><ol class="dek-tracker">')}{''.join(items)}{markup('</ol>')}{hint_html}{markup('</section>')}"""


def order_tracker(status,fulfillment='dine_in'):  # แสดงแถบขั้นตอนติดตามออเดอร์
    st.html(order_tracker_html(status, fulfillment))


def payment_deadline_html(awaiting_since, minutes, now=None):  # คำนวณและสร้างแถบเวลาคงเหลือสำหรับแจ้งชำระ
    import time as _time
    from core import local_time
    now = _time.time() if now is None else now
    total = max(1, int(minutes) * 60)
    due = int(awaiting_since) + total
    left = due - now
    if left <= 0:
        return markup('<div class="dek-deadline urgent" role="status"><div class="dek-deadline-top"><span>หมดเวลาแจ้งชำระ</span></div><small>หมดเวลาสำหรับรายการนี้ กรุณารีเฟรชเพื่อตรวจสถานะล่าสุด</small></div>')
    mins = int(-(-left // 60))  # round up so it never shows 0 while time remains
    pct = max(0, min(100, round(left * 100 / total)))
    cls = ' urgent' if left <= 300 else ''
    return (f"""{markup('<div class="dek-deadline')}{cls}{markup('" role="status"><div class="dek-deadline-top"><span>เหลือเวลาแจ้งชำระ</span><strong>')}{mins}{markup(' นาที</strong></div><div class="dek-deadline-bar"><span style="width:')}{pct}{markup('%"></span></div><small>แจ้งก่อน ')}{escape(local_time(due))}{markup(' น. หากหมดเวลา ระบบจะยกเลิกและคืนโต๊ะ</small></div>')}""")


def payment_deadline(awaiting_since, minutes, now=None):  # แสดงเวลาชำระและระดับการเตือนบนหน้าจอ
    st.html(payment_deadline_html(awaiting_since, minutes, now))


def price_summary_html(subtotal, vat, total, vat_label='VAT 7%'):  # สร้างกล่องยอดอาหาร VAT และสุทธิ
    from core import money
    return (f"""{markup('<div class="dek-price"><div class="row"><span>ก่อน VAT</span><b>฿')}{money(subtotal)}{markup('</b></div><div class="row"><span>')}{escape(vat_label)}{markup('</span><b>฿')}{money(vat)}{markup('</b></div><div class="row total"><span>ยอดชำระสุทธิ</span><b>฿')}{money(total)}{markup('</b></div></div>')}""")


def price_summary(subtotal, vat, total, vat_label='VAT 7%'):  # แสดงสรุปยอดเงินบนหน้าจอ
    st.html(price_summary_html(subtotal, vat, total, vat_label))


def empty_state(icon, title, text=''):  # แสดงข้อความแนะนำเมื่อยังไม่มีรายการ
    body = f'<p>{escape(tr(text))}</p>' if text else ''
    st.html(f"""{markup('<div class="dek-empty-state"><div class="ico" aria-hidden="true">')}{escape(icon)}{markup('</div><strong>')}{escape(tr(title))}{markup('</strong>')}{body}{markup('</div>')}""")


def kitchen_ticket_html(order, items, now=None, late_after=15, over_after=25):  # สร้างบัตรคิวครัวพร้อมอาหารและสีเตือนตามเวลารอ
    """Kitchen display card. `order` comes from Store.orders(), `items` from Store.details()[0]."""
    import time as _time
    from core import local_time
    now = _time.time() if now is None else now
    started = order.get('paid_at') or order.get('created') or now
    mins = max(0, int((now - started) // 60))
    level = 'over' if mins >= over_after else 'late' if mins >= late_after else ''
    lines = []
    for item in items:
        chips = []
        if item.get('doneness', 'ไม่ระบุ') != 'ไม่ระบุ': chips.append(item['doneness'])
        if item.get('sauce', 'ไม่ใส่ซอส') != 'ไม่ใส่ซอส': chips.append('ซอส' + item['sauce'])
        if item.get('drink_option'): chips.append(item['drink_option'])
        chip_html = ''.join(f'<span class="dek-chip">{escape(str(c))}</span>' for c in chips)
        opts = f'<div class="opts">{chip_html}</div>' if chip_html else ''
        note = f'<div class="dek-allergy">⚠ {escape(str(item["note"]))}</div>' if item.get('note') else ''
        lines.append(f'<li><span class="qty">×{int(item.get("quantity", 1))}</span><div><strong>{escape(str(item.get("name", "")))}</strong>{opts}{note}</div></li>')
    order_note = f'<div class="dek-allergy order-note">⚠ {escape(str(order["note"]))}</div>' if order.get('note') else ''
    pickup = f"""{markup('<div class="dek-chip">สั่งกลับบ้าน · ')}{escape(str(order.get('pickup_name', '')))}{markup('</div>')}""" if order.get('fulfillment')=='takeaway' else ''
    party='รับกลับบ้าน' if order.get('fulfillment')=='takeaway' else str(int(order.get('guests',1)))+' คน'
    time_label = 'นาทีนับจากรับเงิน' if order.get('paid_at') else 'นาทีนับจากสั่ง'
    return (f"""{markup('<article class="dek-ticket ')}{level}{markup('"><header><div><span class="dek-ticket-table">')}{escape(str(order.get('table_name', '')))}{markup('</span><small>#')}{int(order['id']):06}{markup(' · ')}{party}{markup('</small></div><div class="dek-ticket-time"><b>')}{mins}{markup('</b>')}{time_label}{markup('</div></header>')}{pickup}{markup('<ul class="dek-ticket-items">')}{''.join(lines)}{markup('</ul>')}{order_note}{markup('<footer>')}{status_badge_html(order.get('status', ''), order.get('fulfillment', 'dine_in'))}{markup('<span>สั่งเมื่อ ')}{escape(local_time(order.get('created')))}{markup('</span></footer></article>')}""")


def kitchen_ticket(order, items, now=None, late_after=15, over_after=25):  # แสดงบัตรคิวครัวบนหน้าจอ
    st.html(kitchen_ticket_html(order, items, now, late_after, over_after))

TYPOGRAPHY_CSS = '''

.st-key-fulfillment_choice [role="radiogroup"]{gap:10px}.st-key-fulfillment_choice [role="radiogroup"] label{padding:10px 18px;border:1px solid var(--dek-line);border-radius:12px;background:var(--dek-surface);color:var(--dek-ink)}.st-key-fulfillment_choice [role="radiogroup"] label>div:first-child{display:none}.st-key-fulfillment_choice [role="radiogroup"] label p{color:inherit!important;font-size:16px!important}.st-key-fulfillment_choice [role="radiogroup"] label:has(input:checked){background:var(--dek-accent-soft);border-color:var(--dek-accent)}
/* Readable Thai typography and consistent text baselines across the application. */
.stApp{font-size:16px}
.stApp [data-testid="stMarkdownContainer"] p,.stApp [data-testid="stMarkdownContainer"] li{font-size:16px;line-height:1.65}
.stApp [data-testid="stCaptionContainer"] p{font-size:14px!important;line-height:1.6!important;color:var(--dek-muted)!important;margin:0!important;overflow-wrap:anywhere}
.stApp [data-testid="stWidgetLabel"] p{font-size:14px!important;line-height:1.6!important;font-weight:600}
.stApp input,.stApp textarea,.stApp [data-baseweb="select"]{font-size:16px!important;line-height:1.55!important}
.stApp input::placeholder,.stApp textarea::placeholder{color:var(--dek-muted)!important}
.stApp h1,.stApp h2,.stApp h3{letter-spacing:0!important;overflow-wrap:anywhere;line-height:1.45!important}
.stApp button p{font-size:15px!important;line-height:1.5!important;margin:0!important}
.stApp button{height:auto;min-height:44px}
.stApp [data-testid="stMetricLabel"] p{font-size:14px!important;line-height:1.5!important;white-space:normal!important}
.stApp [data-testid="stMetricValue"]{font-variant-numeric:tabular-nums;line-height:1.25!important;font-size:clamp(24px,2.3vw,32px)!important;overflow-wrap:anywhere}
.stApp [data-testid="stMetric"]{min-width:0}
.stApp [data-testid="stMetricValue"] *{font-size:inherit!important;line-height:1.3!important}
.stApp [data-testid="stMetricValue"]>div{white-space:normal!important;overflow:visible!important;text-overflow:clip!important}
.dek-menu-description{font-size:15px!important;line-height:1.7!important;min-height:3.4em;color:var(--dek-muted)!important}
.dek-menu-title{font-size:21px!important;line-height:1.45!important;min-height:2.9em;display:flex;align-items:flex-start}
.dek-menu-meta{align-items:center;gap:12px}.dek-menu-category{font-size:13px!important;line-height:1.6}.dek-menu-price{font-size:19px!important;line-height:1.4;white-space:nowrap}
.stApp [class*="st-key-menu_card_"] [data-testid="stWidgetLabel"] p{font-size:14px!important}
.stApp [class*="st-key-menu_card_"] [role="radiogroup"] label p{font-size:14px!important;line-height:1.5!important}
.stApp [class*="st-key-menu_card_"] [role="radiogroup"] label{min-height:44px;height:auto!important}
.stApp [class*="st-key-drink_choices_"] [role="radiogroup"] label{min-height:48px}
.stApp [data-testid="stExpander"] summary p{font-size:15px!important;line-height:1.6!important}
.st-key-menu_category [role="radiogroup"] label p{font-size:14px!important;line-height:1.5!important}
.st-key-menu_category [role="radiogroup"] label{padding:9px 13px!important}
.st-key-sidebar_navigation [role="radiogroup"] label p{font-size:15px!important;line-height:1.55!important}
.st-key-owner_page [role="radiogroup"] label p::after{font-size:13px!important;line-height:1.55!important;color:var(--dek-muted)!important}
.st-key-owner_page [role="radiogroup"] label{min-height:78px!important;align-items:center!important}
.st-key-sidebar_navigation [data-testid="stWidgetLabel"] p{font-size:13px!important;letter-spacing:0!important}
.stApp [data-testid="stTabs"] [role="tab"]{min-height:46px!important;height:auto!important}
.stApp [data-testid="stTabs"] [role="tab"] p{font-size:15px!important;line-height:1.5!important}
.dek-food-placeholder span{font-size:13px!important;color:var(--dek-muted)!important}
.dek-step{font-size:14px!important;line-height:1.55!important}.dek-step b{font-size:12px!important}
.dek-table span,.dek-table .state,.dek-stock-badge{font-size:14px!important;line-height:1.6!important}
.dek-table.busy{opacity:1}.dek-table strong{line-height:1.5}
.dek-banner p,.dek-section p,.dek-tracker-hint,.dek-empty-state p{font-size:15px!important;line-height:1.7!important;color:var(--dek-muted)!important}
.dek-banner .dek-eyebrow,.dek-section .eyebrow{font-size:12px!important;letter-spacing:.1em}
.dek-status,.dek-chip,.dek-allergy{font-size:14px!important;line-height:1.55!important}
.dek-tracker li{font-size:13px!important;line-height:1.55!important;overflow-wrap:anywhere}
.dek-track ol{padding-left:0!important;margin:0!important;list-style:none!important}
.dek-deadline small,.dek-ticket header small,.dek-ticket-time,.dek-ticket footer{font-size:14px!important;line-height:1.6!important}
.dek-price .row{font-size:16px!important;line-height:1.6!important;gap:20px}.dek-price .row b{white-space:nowrap}
.dek-price .row.total b{font-size:26px!important}
.dek-catalog th{font-size:14px!important;line-height:1.6!important}.dek-catalog td{font-size:15px!important;line-height:1.65!important}
.dek-catalog .catalog-category,.dek-catalog .catalog-state{font-size:14px!important;line-height:1.5!important}
.dek-catalog .catalog-food{min-width:170px}.dek-catalog{overflow-x:auto}
.dek-contact p{font-size:15px!important;line-height:1.6!important}.dek-contact-bottom{font-size:13px!important;line-height:1.6!important}.dek-contact a{font-size:15px!important;line-height:1.5!important}
.dek-featured-copy p{font-size:15px!important;line-height:1.65!important}.dek-featured-copy small,.dek-featured-badge{font-size:13px!important}
.st-key-sticky_basket{padding:14px 18px!important;min-height:90px;box-sizing:border-box}
.st-key-sticky_basket [data-testid="stHorizontalBlock"]{align-items:center!important;gap:16px}
.st-key-sticky_basket [data-testid="stColumn"]{min-width:0!important}
.dek-sticky-copy{display:flex;flex-direction:column;gap:6px;min-width:0;justify-content:center}
.dek-sticky-copy strong{display:flex;font-size:17px;line-height:1.45;min-height:32px;align-items:center;color:var(--dek-ink);font-weight:750;overflow-wrap:anywhere}
.dek-sticky-copy span{display:block;font-size:14px;line-height:1.55;color:var(--dek-muted);overflow-wrap:anywhere}
.dek-sticky-amount strong{font-size:22px;font-variant-numeric:tabular-nums;white-space:nowrap}
.stApp .st-key-sticky_basket button p{font-size:15px!important;line-height:1.5!important}
@media(max-width:800px){.st-key-sticky_basket{padding:12px!important;bottom:10px}.st-key-sticky_basket [data-testid="stHorizontalBlock"]{gap:10px!important}.dek-sticky-copy strong{font-size:15px;line-height:1.45;min-height:44px}.dek-sticky-copy span{font-size:13px;line-height:1.55}.dek-sticky-amount strong{font-size:clamp(15px,4.3vw,18px)}.stApp .st-key-sticky_basket button p{font-size:14px!important}}
@media(max-width:640px){.stApp [data-testid="stMainBlockContainer"]{padding-left:16px!important;padding-right:16px!important}.dek-step{font-size:13px!important;min-width:0!important;padding:12px 7px!important}.dek-menu-description{min-height:0}.dek-tracker{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 4px}.dek-tracker li{font-size:12px!important}.dek-tracker li:nth-child(4)::after{display:none}.dek-price .row{font-size:15px!important}.dek-price .row.total b{font-size:23px!important}.dek-featured-copy p{font-size:14px!important}.dek-menu-title{font-size:20px!important;min-height:0}.dek-contact-bottom{font-size:13px!important}.dek-data-table table{min-width:600px}}

[role="dialog"] [data-testid="stMarkdownContainer"] p{font-size:16px!important;line-height:1.65!important}
[role="dialog"] [data-testid="stCaptionContainer"] p{font-size:14px!important;line-height:1.6!important;color:var(--dek-muted)!important}
[role="dialog"] [data-testid="stWidgetLabel"] p{font-size:14px!important;line-height:1.6!important;font-weight:600}
[role="dialog"] input,[role="dialog"] textarea{font-size:16px!important;line-height:1.55!important}
[role="dialog"] button p{font-size:15px!important;line-height:1.5!important}
[role="dialog"] h2,[role="dialog"] h3{line-height:1.45!important;letter-spacing:0!important}
'''


# การ์ดเปิด/หยุดขายใช้ขนาดรูปเดียวกันและสำรองพื้นที่ชื่อสองบรรทัด โดยไม่ตัดชื่อยาวทิ้ง
STOCK_CARD_CSS = r"""
.dek-stock-body{display:flex;flex-direction:column;align-items:flex-start;gap:10px;width:100%;min-width:0}
.dek-stock-photo{display:block;width:130px!important;height:130px!important;max-width:100%;flex:0 0 130px;border-radius:14px;background:var(--dek-surface-2,#f6f3ec);object-position:center}
.dek-stock-placeholder{display:flex;align-items:center;justify-content:center;font-size:36px;color:var(--dek-muted,#746b63)}
.stApp .dek-stock-title{font-size:16px!important;font-weight:700!important;line-height:1.6!important;min-height:3.2em;margin:0!important;white-space:normal;overflow-wrap:anywhere;color:var(--dek-ink,#30251f)}
.stApp .dek-stock-price{font-size:14px!important;line-height:1.6!important;margin:0!important;color:var(--dek-muted,#746b63)}
.dek-stock-body .dek-stock-badge{margin:0;min-height:30px;align-items:center}
[class*="st-key-stock_card_"] [data-testid="stButton"] button{min-height:44px}
"""


# หน้าเลือกอาหาร: รูป/ภาพแทนสูงเท่ากัน สำรองพื้นที่ข้อความ และดันปุ่มเพิ่มตะกร้าให้เสมอกันในแถว
MENU_CARD_CSS = r"""
.stApp [class*="st-key-menu_card_"] .dek-food-photo,
.stApp [class*="st-key-menu_card_"] .dek-food-placeholder{display:block;width:100%;height:200px!important;min-height:200px;max-height:200px;margin:0!important;border-radius:14px;object-position:center;box-sizing:border-box}
.stApp [class*="st-key-menu_card_"] .dek-food-placeholder{display:flex}
.stApp [class*="st-key-menu_card_"] .dek-menu-info{min-height:174px;width:100%;min-width:0}
.stApp [class*="st-key-menu_card_"] .dek-menu-title{min-height:2.9em;white-space:normal;overflow-wrap:anywhere}
.stApp [class*="st-key-menu_card_"] .dek-menu-description{min-height:3.4em;white-space:normal;overflow-wrap:anywhere}
.stApp [class*="st-key-menu_card_"] [data-testid="stForm"]{display:flex;flex-direction:column;flex-grow:1;min-height:0}
.stApp [class*="st-key-menu_card_"] [data-testid="stElementContainer"]:has([data-testid="stFormSubmitButton"]){margin-top:auto!important}
.stApp [class*="st-key-menu_card_"] [data-testid="stFormSubmitButton"]{margin-top:auto!important}
.stApp [class*="st-key-menu_card_"] [data-testid="stFormSubmitButton"] button{min-height:46px}
@media(max-width:640px){
 .stApp [class*="st-key-menu_card_"] .dek-food-photo,
 .stApp [class*="st-key-menu_card_"] .dek-food-placeholder{height:190px!important;min-height:190px;max-height:190px}
 .stApp [class*="st-key-menu_card_"] .dek-menu-info{min-height:0}
 .stApp [class*="st-key-menu_card_"] .dek-menu-title,
 .stApp [class*="st-key-menu_card_"] .dek-menu-description{min-height:0}
}
"""
