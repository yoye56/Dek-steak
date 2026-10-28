"""Restaurant theme schedule always uses Bangkok time, including public hosts."""
from datetime import datetime, timezone, timedelta

BANGKOK=timezone(timedelta(hours=7))


def scheduled_dark(now=None):  # เลือกโทนเข้มก่อน 06:00 หรือตั้งแต่ 18:00 ตามเวลาไทย
    current=now if now is not None else datetime.now(BANGKOK)
    if current.tzinfo is None:
        raise ValueError('Theme schedule requires a timezone-aware time')
    hour=current.astimezone(BANGKOK).hour
    return hour<6 or hour>=18


def scheduled_period(now=None):  # ระบุรอบเช้าหรือเย็นเพื่อให้การปรับธีมเองอยู่ถึงขอบเขตรอบถัดไป
    current=now if now is not None else datetime.now(BANGKOK)
    if current.tzinfo is None:
        raise ValueError('Theme schedule requires a timezone-aware time')
    local=current.astimezone(BANGKOK)
    if local.hour<6:
        boundary=(local-timedelta(days=1)).replace(hour=18,minute=0,second=0,microsecond=0)
    else:
        boundary=local.replace(hour=6 if local.hour<18 else 18,minute=0,second=0,microsecond=0)
    return boundary.isoformat()
