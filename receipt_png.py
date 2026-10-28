"""Private receipt PNG export, rendered locally by the customer's browser on demand."""
import json
from html import escape

from core import local_time, money
from i18n import language, t as tr, menu_name, translated_item_options


def receipt_png_payload(order):  # เตรียมข้อความและยอดจากใบเสร็จที่ตรวจสิทธิ์แล้ว โดยไม่ส่งอีเมลหรือ hash บัญชีไปด้วย
    if order.get('paid_at') is None:
        raise ValueError('PNG receipts require an approved payment')
    service = ([tr('สั่งกลับบ้าน · ผู้รับ: ') + order.get('pickup_name', ''),
                tr('โทร: ') + order.get('pickup_phone', '')]
               if order.get('fulfillment') == 'takeaway' else
               [tr('โต๊ะ: ') + str(order['table_name']) + ' · ' + str(order['guests']) + ' ' + tr('ท่าน')])
    return {
        'language': language(), 'filename': f"dek_steak_receipt_{int(order['id']):06}.png",
        'shop': order['shop_name'], 'title': tr('ใบเสร็จรับเงิน'),
        'meta': [tr('รายการ: ') + f"#{int(order['id']):06}", *service,
                 tr('ลูกค้า: ') + order['customer'], tr('รับเงินเมื่อ: ') + local_time(order['paid_at']),
                 tr('ราคาต่อรายการรวม VAT 7% แล้ว' if order.get('vat_included',0) else 'ราคาต่อรายการก่อน VAT 7%')],
        'items': [{'name': menu_name(item['name']),
                   'quantity': f"{item['quantity']} × ฿{money(item['price'])}",
                   'options': translated_item_options(item),
                   'amount': '฿' + money(item['price'] * item['quantity'])}
                  for item in order['items']],
        'columns': [tr('รายการอาหาร'), tr('จำนวนเงิน')],
        'totals': [[tr('ก่อน VAT'), '฿' + money(order['subtotal'])],
                   [tr('VAT 7%'), '฿' + money(order['vat'])]],
        'grand': [tr('รวมสุทธิ'), '฿' + money(order['total'])],
        'method': [tr('ชำระผ่าน'), tr('เงินสด' if order['payment_method'] == 'cash' else 'QR / โอนเงิน')],
        'thanks': tr('ขอบคุณที่ให้เราดูแลมื้อนี้'), 'reference': f"DEK-{int(order['id']):06}",
        'foot': [tr('เก็บไว้เป็นหลักฐานการรับเงิน'), tr('เอกสารนี้ไม่ใช่ใบกำกับภาษีเต็มรูป')],
        'error': tr('สร้างรูปใบเสร็จไม่สำเร็จ กรุณาลองใหม่'),
    }


# Canvas uses the browser's text shaping and fallback fonts for Thai and Chinese.
# It does not capture the whole page, load external scripts/fonts, or run on every refresh.
SCRIPT = r'''
const receipt = __PAYLOAD__;
const button = document.getElementById('download-png');
const status = document.getElementById('png-status');

function createReceiptCanvas(data) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Canvas is unavailable');
  const W = 1000, L = 65, R = W - L, content = R - L;
  const ops = [];
  let y = 45;
  const family = 'Tahoma, Arial, sans-serif';
  const font = (size, bold) => `${bold ? '700' : '400'} ${size}px ${family}`;
  const segmenter = typeof Intl.Segmenter === 'function' ? new Intl.Segmenter(data.language, {granularity:'word'}) : null;
  const graphemes = typeof Intl.Segmenter === 'function' ? new Intl.Segmenter(data.language, {granularity:'grapheme'}) : null;
  const clusters = value => graphemes ? Array.from(graphemes.segment(value), x => x.segment) : (value.match(/\P{M}\p{M}*|\p{M}+/gu) || []);

  function lines(value, width, size, bold=false) {
    ctx.font = font(size, bold);
    const result = [];
    for (const paragraph of String(value ?? '').replace(/\r\n?/g,'\n').split('\n')) {
      if (!paragraph) { result.push(''); continue; }
      const words = segmenter ? Array.from(segmenter.segment(paragraph), x => x.segment) : clusters(paragraph);
      let line = '';
      for (const word of words) {
        if (ctx.measureText(line + word).width <= width) { line += word; continue; }
        if (line) { result.push(line.trimEnd()); line = ''; }
        const token = word.trimStart();
        if (ctx.measureText(token).width <= width) { line = token; continue; }
        for (const cluster of clusters(token)) {
          if (line && ctx.measureText(line + cluster).width > width) { result.push(line); line = ''; }
          line += cluster;
        }
      }
      if (line) result.push(line.trimEnd());
    }
    return result;
  }
  function text(value, x, yy, size=28, bold=false, color='#302b27', align='left', width=null) {
    ops.push({kind:'text',value:String(value),x,y:yy,size,bold,color,align,width});
  }
  function block(value, size=28, bold=false, color='#302b27', width=content, align='left') {
    const list = lines(value,width,size,bold);
    for (const value of list) {
      text(value,align==='center' ? W/2 : L,y,size,bold,color,align);
      y += Math.ceil(size * 1.55);
    }
  }
  function rule(dashed=false) {
    ops.push({kind:'line',y,dashed});
    y += 22;
  }
  function pair(values,size=28,bold=false,color='#302b27') {
    const left = lines(values[0],content*0.51,size,bold);
    const right = lines(values[1],content*0.45,size,bold);
    const count=Math.max(left.length,right.length);
    for(let i=0;i<count;i++){
      if(left[i]!==undefined) text(left[i],L,y,size,bold,color);
      if(right[i]!==undefined) text(right[i],R,y,size,bold,color,'right');
      y+=Math.ceil(size*1.55);
    }
    y+=6;
  }

  block('FRESH FROM THE GRILL',20,false,'#84776b',content,'center');
  y+=10;
  block(data.shop,50,true,'#302b27',content,'center');
  block(data.title,26,false,'#70675e',content,'center');
  y+=30;
  for(const meta of data.meta) block(meta,27,false,'#554b43');
  y+=15;
  rule(true);
  pair(data.columns,24,false,'#70675e');
  rule(true);
  for(const item of data.items){
    const top=y;
    block(item.name,31,true,'#302b27',content-245);
    text(item.amount,R,top,28,false,'#302b27','right',230);
    block(item.quantity,25,false,'#746b63');
    if(item.options) block(item.options,25,false,'#746b63');
    y+=15;
    rule(false);
  }
  y+=12;
  for(const total of data.totals) pair(total,28);
  y+=10;
  rule(false);
  pair(data.grand,43,true);
  y+=10;
  pair(data.method,26);
  y+=28;
  block('THANK YOU · '+data.thanks,24,true,'#302b27',content,'center');
  y+=18;
  block(data.reference,25,false,'#70675e',content,'center');
  y+=20;
  for(const footer of data.foot) block(footer,21,false,'#817971',content,'center');
  y+=35;
  const height=Math.ceil(y);
  if(height>30000) throw new Error('Receipt image is too tall');
  canvas.width=W;canvas.height=height;
  ctx.fillStyle='#ffffff';ctx.fillRect(0,0,W,height);
  ctx.fillStyle='#332920';ctx.fillRect(0,0,W,10);ctx.fillRect(0,height-10,W,10);
  ctx.textBaseline='top';
  for(const op of ops){
    if(op.kind==='line'){
      ctx.beginPath();ctx.strokeStyle=op.dashed?'#aaa096':'#ded9d3';ctx.lineWidth=op.dashed?2:1;
      ctx.setLineDash(op.dashed?[7,6]:[]);ctx.moveTo(L,op.y);ctx.lineTo(R,op.y);ctx.stroke();ctx.setLineDash([]);
    } else {
      ctx.font=font(op.size,op.bold);ctx.fillStyle=op.color;ctx.textAlign=op.align;
      if(op.width) ctx.fillText(op.value,op.x,op.y,op.width);
      else ctx.fillText(op.value,op.x,op.y);
    }
  }
  return canvas;
}

button.addEventListener('click', async () => {
  button.disabled=true;status.textContent='';
  try {
    await document.fonts.ready;
    const canvas=createReceiptCanvas(receipt);
    const blob=await new Promise((resolve,reject)=>canvas.toBlob(value=>value?resolve(value):reject(new Error('PNG encoding failed')),'image/png'));
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');link.href=url;link.download=receipt.filename;
    document.body.appendChild(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),60000);
  } catch(error) {
    status.textContent=receipt.error;
  } finally {
    button.disabled=false;
  }
});
'''


def receipt_png_download(order, dark=False):  # สร้างปุ่ม PNG ให้เบราว์เซอร์วาดภาพเมื่อกด โดยไม่มีการส่งข้อมูลไปภายนอก
    payload = json.dumps(receipt_png_payload(order), ensure_ascii=False).replace('&', r'\u0026').replace('<', r'\u003c').replace('>', r'\u003e')
    label = escape(tr('ดาวน์โหลดใบเสร็จ PNG'))
    foreground, background, border = ('#f0e8dc','#171e29','#465365') if dark else ('#743a20','#fffaf3','#ddbea3')
    return f'''<!doctype html><html lang="{language()}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{{margin:0;background:transparent;font-family:Tahoma,Arial,sans-serif}}body{{padding:2px}}button{{display:inline-flex;align-items:center;justify-content:center;gap:9px;max-width:100%;min-height:44px;padding:10px 14px;border:1px solid {border};border-radius:9px;background:{background};color:{foreground};font:400 15px/1.5 Tahoma,Arial,sans-serif;cursor:pointer}}button:hover{{border-color:#e66b27}}button:focus-visible{{outline:3px solid #e66b27;outline-offset:2px}}button:disabled{{opacity:.6;cursor:wait}}#png-status{{color:{foreground};font-size:13px;line-height:1.6;margin:4px 0 0}}#png-status:empty{{display:none}}</style></head>
<body><button id="download-png" type="button"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3v12m-4-4 4 4 4-4M5 16v5h14v-5"/></svg><span>{label}</span></button><p id="png-status" role="status" aria-live="polite"></p>
<script>{SCRIPT.replace('__PAYLOAD__',payload)}</script></body></html>'''
