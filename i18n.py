"""Presentation-only translations; canonical database values stay unchanged."""
import re
import streamlit as st

LANGUAGES={'th':'ไทย','en':'English','zh':'中文'}
CATALOG={}
DATA='''เลือกอาหาร|Choose your meal|选择餐点
เลือกโต๊ะ|Choose a table|选择餐桌
รับกลับบ้าน|Takeaway|外带
รับอาหาร|Collect your meal|领取餐点
ชำระเงิน|Payment|付款
อิ่มอร่อย|Enjoy your meal|享用美食
รับอาหารแบบไหน|How would you like to dine?|用餐方式
ทานที่ร้าน|Dine in|堂食
สั่งกลับบ้าน|Takeaway|外带
ทั้งหมด|All|全部
ของทานเล่น|Sides|小吃
พาสต้า|Pasta|意大利面
สลัด|Salads|沙拉
สเต๊กปลา|Fish steaks|鱼排
สเต๊กหมู|Pork steaks|猪排
สเต๊กเนื้อ|Beef steaks|牛排
สเต๊กไก่|Chicken steaks|鸡排
เครื่องดื่ม|Drinks|饮料
เมนูอาหาร|Food menu|餐点菜单
เมนูของคุณ|Your menu|您的菜单
หมวดอาหาร|Category|分类
หมวด|Category|分类
ค้นหาเมนู|Search the menu|搜索餐点
เช่น Ribeye, ไก่, ชา|e.g. Ribeye, chicken, tea|例如：牛排、鸡排、奶茶
จำนวน|Quantity|数量
จำนวนคน|Guests|人数
จำนวนผู้ใช้บริการ|Guests|用餐人数
ความสุก|Doneness|熟度
ไม่ระบุ|No preference|无偏好
ซอส|Sauce|酱汁
เกรวี่|Gravy|肉汁酱
พริกไทยดำ|Black pepper|黑胡椒酱
บาร์บีคิว|Barbecue|烧烤酱
ไม่ใส่ซอส|No sauce|不加酱
ระดับความหวาน|Sweetness|甜度
ไม่หวาน (0%)|No sugar (0%)|无糖 (0%)
หวานน้อย (25%)|Less sweet (25%)|微糖 (25%)
หวานกลาง (50%)|Half sweet (50%)|半糖 (50%)
หวานปกติ (100%)|Regular (100%)|全糖 (100%)
อุณหภูมิน้ำ|Water temperature|水温
เย็น|Chilled|冰的
ไม่เย็น|Room temperature|常温
หมายเหตุ / แจ้งแพ้อาหาร (ถ้ามี)|Notes / food allergies (optional)|备注／食物过敏（选填）
หมายเหตุ / แจ้งแพ้อาหาร|Notes / food allergies|备注／食物过敏
หมายเหตุรวมถึงร้าน|Notes for the restaurant|给餐厅的备注
＋ เพิ่มในตะกร้า|＋ Add to basket|＋ 加入购物篮
ตะกร้า|Basket|购物篮
ตะกร้าของคุณ|Your basket|您的购物篮
🛒 ตะกร้าของคุณ|🛒 Your basket|🛒 您的购物篮
ตรวจตะกร้า|Review basket|查看购物篮
ตรวจตะกร้าและยืนยัน|Review and confirm|查看并确认
ดูตะกร้า (|View basket (|查看购物篮 (
จำนวนในตะกร้า|Basket quantity|购物篮数量
ยืนยันออเดอร์และไปชำระเงิน|Confirm order and pay|确认订单并付款
ลบ|Remove|删除
ตะกร้ายังว่าง|Your basket is empty|购物篮为空
เลือกอาหารจากหน้าเมนูเพื่อเริ่มออเดอร์|Choose a meal from the menu to start|请从菜单选择餐点
ตะกร้ายังว่าง เลือกจานโปรดจากหน้าเมนูได้เลย|Your basket is empty. Choose a meal from the menu.|购物篮为空，请从菜单选择餐点。
ยังไม่มีอาหารในตะกร้า เลือกอาหารก่อนเริ่มรายการ|Choose a meal before checking out.|请先选择餐点。
เลือกจานโปรดในแบบของคุณ|Make your meal your own|选择您喜爱的餐点
เลือกจานโปรด แล้วให้เราดูแลมื้อนี้|Choose your favourites. We will take care of your meal.|选好餐点，剩下的交给我们。
โต๊ะที่เลือก|Selected table|已选餐桌
โต๊ะสำหรับรายการนี้|Table for this order|本订单餐桌
โต๊ะ|Table|餐桌
เลือกโต๊ะนี้|Choose this table|选择此桌
เลือกแล้ว|Selected|已选择
ว่าง พร้อมรับคุณ|Available|空桌
มีลูกค้าแล้ว|Occupied|已有客人
ปิดใช้งาน|Closed|已关闭
ดูรูปโต๊ะและสถานะทั้งหมด|View all tables and availability|查看餐桌照片及状态
รีเฟรชโต๊ะว่าง|Refresh tables|刷新餐桌
ชื่อผู้รับอาหาร|Pickup name|取餐人姓名
เบอร์โทรผู้รับ (10 หลัก)|Pickup phone (10 digits)|取餐电话（10位）
มารับอาหารที่ร้าน · ร้านเริ่มทำเมื่อยืนยันรับเงิน · ไม่มีบริการจัดส่ง|Collect at the restaurant · Cooking starts after payment approval · No delivery|到店取餐 · 确认收款后制作 · 不提供配送
สั่งกลับบ้าน · ไม่ต้องเลือกโต๊ะ · กรอกข้อมูลผู้รับในหน้าตะกร้า|Takeaway · No table needed · Enter pickup details in your basket|外带 · 无需选桌 · 在购物篮填写取餐信息
เพิ่มอาหารแล้วเปิดตะกร้าเพื่อกรอกชื่อและเบอร์โทรผู้รับ|Add your meals, then enter your pickup name and phone in the basket.|添加餐点后，在购物篮填写取餐人姓名及电话。
ราคาหน้าเมนูยังไม่รวม VAT 7% • มารับอาหารที่ร้าน|Menu prices exclude 7% VAT · Restaurant pickup|菜单价格未含7%增值税 · 到店取餐
ราคาหน้าเมนูยังไม่รวม VAT 7% • โต๊ะจะถูกกันเมื่อยืนยันออเดอร์|Menu prices exclude 7% VAT · Table reserved after order confirmation|菜单价格未含7%增值税 · 确认订单后保留餐桌
เลือกโต๊ะ · เลือกจานโปรด · ตรวจยอดรวม VAT ก่อนยืนยัน|Choose a table · Choose your meal · Review the total including VAT|选择餐桌 · 选择餐点 · 确认含税总额
สั่งกลับบ้าน · ข้อมูลผู้รับ · ตรวจยอดรวม VAT ก่อนยืนยัน|Takeaway · Pickup details · Review the total including VAT|外带 · 取餐信息 · 确认含税总额
ตรวจโต๊ะ จำนวนคน และราคาอาหารก่อนยืนยัน ร้านจะกันโต๊ะเมื่อสร้างออเดอร์สำเร็จ|Check your table, guests and prices. Your table is reserved once the order is created.|请确认餐桌、人数及价格。订单成功后保留餐桌。
ตรวจสอบราคาอีกครั้งเมื่อยืนยัน หากราคาเปลี่ยนต้องนำเมนูออกแล้วเพิ่มใหม่ก่อนสั่ง|Prices are checked at confirmation. If changed, remove and add the meal again.|确认时会重新核对价格。如有变动，请删除并重新添加餐点。
ราคาก่อน VAT|Price before VAT|税前价格
ก่อน VAT|Before VAT|税前
ราคาอาหาร|Meal subtotal|餐点小计
ยอดชำระสุทธิ|Total due|应付总额
รวม VAT 7% แล้ว|Includes 7% VAT|已含7%增值税
รวม|Total|总额
ออเดอร์และชำระเงิน|Orders and payment|订单与付款
รายการของฉัน / ชำระเงิน|My orders / payment|我的订单／付款
ช่องทางชำระเงิน|Payment method|付款方式
เงินสด|Cash|现金
เงินสดที่เคาน์เตอร์|Cash at the counter|柜台现金付款
QR / โอน|QR / transfer|二维码／转账
แจ้งชำระเงิน|Submit payment|提交付款
แจ้งชำระ|Submit payment|提交付款
โอนแล้วแนบสลิป เพื่อให้ร้านตรวจสอบและยืนยันรับเงิน|Transfer and upload the receipt for payment approval.|转账后上传凭证，等待餐厅确认收款。
แนบสลิป JPEG/PNG ไม่เกิน 5 MB|Upload receipt: JPEG/PNG, up to 5 MB|上传付款凭证：JPEG/PNG，不超过5MB
ยอดเงินที่โอน (บาท)|Transferred amount (THB)|转账金额（泰铢）
ยอดที่โอน (บาท)|Transferred amount (THB)|转账金额（泰铢）
ดูใบเสร็จรับเงิน|View receipt|查看收据
ดาวน์โหลดใบเสร็จสำหรับพิมพ์ / PDF|Download printable receipt / PDF|下载可打印收据／PDF
ยกเลิกออเดอร์|Cancel order|取消订单
เหตุผลยกเลิก|Cancellation reason|取消原因
รีเฟรชสถานะ|Refresh status|刷新状态
สถานะอัปเดตอัตโนมัติทุก 8 วินาที|Status updates every 8 seconds|每8秒自动更新状态
รอชำระเงิน|Awaiting payment|等待付款
รอตรวจสอบเงิน|Awaiting payment approval|等待确认收款
ชำระแล้ว|Paid|已付款
รอครัว|Waiting for kitchen|等待厨房
กำลังปรุง|Preparing|制作中
เสิร์ฟ|Served|上餐
เสิร์ฟแล้ว|Served|已上餐
พร้อมรับ|Ready for pickup|可取餐
พร้อมรับอาหาร|Ready for pickup|可以取餐
รับอาหารแล้ว|Collected|已取餐
เสร็จสิ้น|Completed|已完成
จบรายการ|Completed|已完成
ยกเลิก|Cancelled|已取消
รายการนี้ถูกยกเลิก|This order was cancelled|此订单已取消
กรุณาชำระเงินแล้วกดแจ้งชำระ|Please pay, then submit your payment.|请付款后提交付款信息。
ร้านกำลังตรวจสอบการชำระเงิน|The restaurant is checking your payment.|餐厅正在核对付款。
ชำระเงินแล้ว รอครัวเริ่มปรุง|Payment approved. Waiting for the kitchen.|付款已确认，等待厨房制作。
ครัวกำลังปรุงอาหารของคุณ|The kitchen is preparing your meal.|厨房正在制作您的餐点。
เสิร์ฟแล้ว ขอให้อร่อย|Served. Enjoy your meal!|已上餐，祝您用餐愉快！
อาหารพร้อมแล้ว กรุณามารับที่ร้าน|Your meal is ready. Please collect it at the restaurant.|餐点已做好，请到店领取。
รับอาหารแล้ว ขอบคุณที่ใช้บริการ|Collected. Thank you!|已取餐，谢谢惠顾！
ขอบคุณที่ใช้บริการ|Thank you for dining with us!|谢谢惠顾！
ร้านตรวจเงิน|Payment check|核对收款
เหลือเวลาแจ้งชำระ|Time left to submit payment|提交付款剩余时间
นาที|minutes|分钟
หมดเวลาสำหรับรายการนี้ กรุณารีเฟรชสถานะ|Time has expired. Please refresh the status.|此订单已超时，请刷新状态。
เข้าสู่ระบบ|Sign in|登录
สมัครสมาชิก|Sign up|注册
สร้างบัญชี|Create account|创建账户
ชื่อที่ใช้เรียก|Your name|姓名
อีเมล|Email|电子邮箱
อีเมลสำหรับสมัคร|Email for registration|注册邮箱
รหัสผ่าน|Password|密码
ตั้งรหัสผ่าน (10–128 ตัวอักษร)|Password (10–128 characters)|密码（10–128个字符）
ยืนยันรหัสผ่าน|Confirm password|确认密码
รับทราบว่าร้านจัดเก็บบัญชี รายการอาหาร และสลิปเพื่อดำเนินรายการ|I acknowledge that account, order and payment receipt data are stored to process orders.|我知悉餐厅会保存账户、订单及付款凭证以处理订单。
ยินดีต้อนรับ|Welcome|欢迎
ลืมรหัสผ่าน?|Forgot password?|忘记密码？
ลืมรหัสผ่าน|Forgot password|忘记密码
อีเมลที่สมัครไว้|Registered email|注册邮箱
ส่งรหัสยืนยัน|Send verification code|发送验证码
มีรหัสยืนยันแล้ว|I already have a code|已有验证码
กรอกอีเมลที่สมัครไว้ เพื่อรับรหัสสำหรับตั้งรหัสผ่านใหม่|Enter your registered email to receive a password reset code.|输入注册邮箱以接收重置密码验证码。
อีเมลสำหรับตั้งรหัสใหม่|Email for password reset|重置密码邮箱
รหัสยืนยัน 8 หลัก|8-digit verification code|8位验证码
รหัสผ่านใหม่ (10–128 ตัวอักษร)|New password (10–128 characters)|新密码（10–128个字符）
ตั้งรหัสผ่านใหม่|Reset password|重置密码
กลับไปกรอกอีเมล / ส่งรหัสอีกครั้ง|Go back / resend code|返回／重新发送验证码
กลับไปเข้าสู่ระบบ|Back to sign in|返回登录
ใช้รหัสล่าสุด 8 หลักที่ได้รับทางอีเมล • รหัสมีอายุ 10 นาที|Use the latest 8-digit email code · Valid for 10 minutes|使用最新收到的8位验证码 · 10分钟内有效
ตั้งรหัสใหม่สำเร็จ เข้าสู่ระบบด้วยรหัสใหม่ได้เลย|Password reset. Sign in with your new password.|密码重置成功，请使用新密码登录。
หากอีเมลนี้มีบัญชีอยู่ ระบบจะส่งรหัสให้ทางอีเมล กรุณาตรวจกล่องจดหมายและสแปม|If an account exists for this email, a code will be sent. Check your inbox and spam.|如果该邮箱已注册，系统将发送验证码。请检查收件箱及垃圾邮件。
ร้านยังไม่ได้ตั้งค่าอีเมลผู้ส่ง กรุณาติดต่อร้านเพื่อเปิดบริการรับรหัสยืนยัน|The email service is not configured. Please contact the restaurant.|邮件服务尚未设置，请联系餐厅。
ร้านยังไม่ได้เปิดบริการส่งอีเมล กรุณาลองใหม่เมื่อร้านตั้งค่าเสร็จ|Email delivery is not available yet. Please try after setup.|邮件服务尚未启用，请在设置完成后重试。
รหัสผ่านไม่ตรงกัน|Passwords do not match|密码不一致
กรุณารับทราบการจัดเก็บข้อมูล|Please acknowledge the data storage notice.|请确认数据保存说明。
อีเมลนี้ถูกใช้แล้ว|This email is already registered|此邮箱已注册
กรุณากรอกอีเมลให้ถูกต้อง|Please enter a valid email.|请输入有效邮箱。
อีเมลหรือรหัสผ่านไม่ถูกต้อง|Incorrect email or password|邮箱或密码不正确
ขอรหัสหลายครั้งเกินไป กรุณารอแล้วลองใหม่ภายหลัง|Too many requests. Please wait and try again.|请求过多，请稍后再试。
รหัสยืนยันไม่ถูกต้องหรือหมดอายุ|Invalid or expired verification code|验证码错误或已过期
บัญชี|Account|账户
บัญชีของฉัน|My account|我的账户
สมาชิก|Member|会员
สวัสดี |Hello |您好 
ออกจากระบบ|Sign out|退出登录
โทนเข้ม|Dark mode|深色模式
ข้อมูลเวลาประเทศไทย • VAT 7%|Thailand time • VAT 7%|泰国时间 • 增值税7%
ติดต่อเจ้าของร้าน|Contact the owner|联系店主
สอบถามร้านผ่านช่องทางด้านบน|Contact us using the links above|请通过以上方式联系餐厅
เลือกโต๊ะก่อนยืนยัน|Choose a table before confirming|确认前请选择餐桌
ยังไม่มีโต๊ะว่าง กรุณารีเฟรชหรือติดต่อร้าน|No tables available. Refresh or contact us.|暂无空桌，请刷新或联系餐厅。
ยังไม่มีโต๊ะว่าง กรุณาติดต่อร้านหรือกลับมาเลือกใหม่|No tables available. Contact us or try again later.|暂无空桌，请联系餐厅或稍后重试。
ร้านหยุดรับออเดอร์ชั่วคราว|The restaurant has paused new orders.|餐厅暂时停止接收新订单。
ไม่มีเมนูที่เปิดขาย|No meals currently available|暂无可售餐点
มีเมนูที่หยุดขาย กรุณานำออกในหน้าตะกร้า|Remove unavailable meals from your basket.|请从购物篮删除停售餐点。
มีราคาเปลี่ยน กรุณานำเมนูออกแล้วเพิ่มใหม่ในราคาปัจจุบัน|A price has changed. Remove and add the meal again.|价格已变动，请删除并重新添加餐点。
คุณมีออเดอร์ที่กำลังดำเนินการ ไปที่รายการของฉัน / ชำระเงิน|You have an active order. Open Orders and payment.|您有进行中的订单，请打开订单与付款。
คุณมีรายการที่ยังไม่จบ กรุณาดูที่รายการของฉัน|You have an active order. Please check My orders.|您有进行中的订单，请查看我的订单。
กรุณากรอกจำนวนอาหารก่อนยืนยัน|Add a meal before confirming.|确认前请添加餐点。
กรุณากรอกชื่อผู้รับและเบอร์โทร|Please enter the pickup name and phone.|请填写取餐人姓名及电话。
กรุณากรอกเบอร์โทรไทย 10 หลัก|Please enter a 10-digit Thai phone number.|请输入10位泰国电话号码。
กรุณาแนบสลิป|Please upload your payment receipt.|请上传付款凭证。
ตะกร้ารับได้ไม่เกิน 50 รายการ|The basket holds up to 50 items.|购物篮最多可容纳50项。
เฟรนช์ฟรายส์ทอดใหม่|Freshly fried fries|现炸薯条
คาโบนาราซอสครีม|Creamy carbonara|奶油培根意大利面
ซีซาร์สลัด|Caesar salad|凯撒沙拉
แซลมอนย่างพร้อมสลัด|Grilled salmon with salad|烤三文鱼配沙拉
พอร์กชอปย่างซอสพริกไทยดำ|Grilled pork chop with black pepper sauce|烤猪排配黑胡椒酱
ริบอายย่าง เสิร์ฟพร้อมเฟรนช์ฟรายส์และสลัด|Grilled ribeye with fries and salad|烤肋眼牛排配薯条和沙拉
อกไก่ย่างพร้อมผักและมันฝรั่ง|Grilled chicken with vegetables and potatoes|烤鸡排配蔬菜和土豆
น้ำดื่มขวด|Bottled drinking water|瓶装饮用水
ชาไทยเย็น|Iced Thai milk tea|泰式冰奶茶
น้ำเปล่า|Drinking water|饮用水
ชาเย็น|Iced Thai tea|泰式冰奶茶
French Fries|French Fries|薯条
Spaghetti Carbonara|Spaghetti Carbonara|培根奶油意大利面
Caesar Salad|Caesar Salad|凯撒沙拉
Salmon Steak|Salmon Steak|三文鱼排
Pork Chop|Pork Chop|猪排
Ribeye Steak|Ribeye Steak|肋眼牛排
Chicken Steak|Chicken Steak|鸡排
บันทึกเรียบร้อย|Saved|已保存
จัดการร้าน|Manage restaurant|餐厅管理
รับออเดอร์|Orders|接收订单
รายงานยอดขาย|Sales reports|销售报告
จัดการโต๊ะ|Manage tables|餐桌管理
ตั้งค่าร้าน|Restaurant settings|餐厅设置
เจ้าของร้าน|Owner|店主
ออเดอร์ / คิวครัว|Orders / kitchen queue|订单／厨房队列
จัดการออเดอร์|Manage orders|管理订单
คิวครัว|Kitchen queue|厨房队列
รีเฟรชคิว|Refresh queue|刷新队列
คิวอัปเดตอัตโนมัติทุก 8 วินาที|Queue updates every 8 seconds|队列每8秒更新
เริ่มปรุง|Start cooking|开始制作
จบรายการและคืนโต๊ะ|Complete and release table|完成并释放餐桌
ยืนยันรับเงิน|Approve payment|确认收款
ตรวจแล้วว่าได้รับเงินครบจริง|I verified that full payment was received|已核实收到全额付款
ตรวจแล้วว่ายังไม่ได้รับเงิน|I verified that payment was not received|已核实尚未收到付款
ขอให้ลูกค้าแก้หลักฐาน|Request corrected receipt|要求更正付款凭证
เหตุผล|Reason|原因
ช่วงเวลา|Period|时间范围
วัน|Day|日
สัปดาห์|Week|周
เดือน|Month|月
ปี|Year|年
กำหนดเอง|Custom|自定义
วันที่อ้างอิง|Reference date|参考日期
วันเริ่ม|Start date|开始日期
วันสิ้นสุด|End date|结束日期
รับเงินรวม|Total received|收款总额
จำนวนออเดอร์|Orders|订单数量
อันดับเมนูขายดี|Best-selling meals|畅销餐点排行
เมนูที่ยังไม่มียอดขาย|Meals with no sales|尚无销量餐点
เมนูขายดีและเมนูที่ยังไม่มียอดขาย|Best sellers and meals with no sales|畅销与未售出餐点
ดาวน์โหลดรายงาน CSV (เปิดด้วย Excel ได้)|Download report CSV|下载CSV报告
ดาวน์โหลดสรุปยอดขายแต่ละเมนู CSV|Download meal sales CSV|下载餐点销售CSV
แก้ไขเมนู|Edit menu|编辑菜单
เพิ่มเมนูใหม่|Add meal|添加餐点
ชื่อเมนู|Meal name|餐点名称
รายละเอียด|Description|说明
ราคาไม่รวม VAT (บาท)|Price excluding VAT (THB)|未含税价格（泰铢）
เปิดขาย|Available|可售
หยุดขาย|Unavailable|停售
บันทึกเมนู|Save meal|保存餐点
ภาพอาหาร|Meal photos|餐点照片
เปิด / หยุดขาย|Availability|销售状态
เมนูแนะนำ|Recommended meals|推荐餐点
เพิ่มโต๊ะใหม่|Add table|添加餐桌
แก้ไขโต๊ะ|Edit table|编辑餐桌
ชื่อโต๊ะ|Table name|餐桌名称
จำนวนที่นั่ง|Seats|座位数
เปิดใช้งาน|Enabled|启用
บันทึกโต๊ะ|Save table|保存餐桌
ข้อมูลและรับเงิน|Details and payment|信息与收款
ภาพร้าน|Restaurant photos|餐厅照片
อีเมล OTP|OTP email|验证码邮件
สำรองข้อมูล|Backups|备份
ดูแลบัญชี|Account support|账户支持
ชื่อร้าน|Restaurant name|餐厅名称
เปิดรับออเดอร์ใหม่|Accept new orders|接收新订单
บันทึกการตั้งค่า|Save settings|保存设置
ตรวจการเชื่อมต่ออีเมล|Check email connection|检查邮件连接
เตรียมไฟล์สำรอง|Prepare backup|准备备份
ดาวน์โหลดฐานข้อมูลสำรอง|Download database backup|下载数据库备份
เปลี่ยนรหัสผ่าน|Change password|修改密码
รหัสผ่านปัจจุบัน|Current password|当前密码
รหัสผ่านใหม่|New password|新密码
บันทึกรหัสผ่านใหม่|Save new password|保存新密码
ผู้ใช้|User|用户
ลูกค้า|Customer|顾客
สถานะ|Status|状态
ออเดอร์|Order|订单
ราคา|Price|价格
อันดับ|Rank|排名
จำนวนที่ขาย (หน่วย)|Quantity sold|销售数量
ช่องทาง|Method|方式
เวลา|Time|时间
แสดงสถานะ|Show status|显示状态
ข้อมูลรายการไม่ถูกต้อง|Invalid order data|订单信息不正确
ไม่มีสิทธิ์ดำเนินการ|You do not have permission|无权执行此操作
ไม่พบรายการหรือไม่มีสิทธิ์|Order not found or access denied|订单不存在或无访问权限
ตัวเลือกอาหารไม่ถูกต้อง|Invalid meal options|餐点选项不正确
ตัวเลือกเครื่องดื่มไม่ถูกต้อง|Invalid drink options|饮料选项不正确
เมนูหมดหรือจำนวนไม่ถูกต้อง กรุณาตรวจตะกร้า|Meal unavailable or invalid quantity. Check your basket.|餐点售罄或数量不正确，请检查购物篮。
เมนูนี้หยุดขาย กรุณานำออกจากตะกร้า|This meal is unavailable. Remove it from the basket.|此餐点已停售，请从购物篮删除。
โต๊ะนี้มีลูกค้าเลือกแล้ว กรุณาเลือกโต๊ะอื่น|This table is already reserved. Choose another.|此桌已被预订，请选择其他餐桌。
จำนวนคนเกินความจุโต๊ะ หรือโต๊ะปิดใช้งาน|Too many guests or the table is closed|人数超过座位数或餐桌已关闭
กรุณายืนยันตัวตนก่อน|Please verify identity first.|请先核实身份。
ยินดีต้อนรับสู่มื้ออร่อยของคุณ|Welcome to your next delicious meal|欢迎享用美味餐点
เลือกโต๊ะ · สั่งอาหาร · ชำระเงิน|Choose a table · Order · Pay|选择餐桌 · 点餐 · 付款
ราคาชำระรวม VAT 7% พร้อมตรวจสอบก่อนยืนยัน|Payment includes 7% VAT. Review before confirming.|付款金额已含7%增值税，请在确认前核对。
มื้ออร่อย|A delicious meal|美味餐点
เริ่มที่ Dek Steak|Starts at Dek Steak|从Dek Steak开始
เมนูก่อนหน้า|Previous meal|上一道餐点
เมนูถัดไป|Next meal|下一道餐点
รอภาพจริงจากทางร้าน|Photo coming soon|照片即将上线
มีรูปแล้ว|Photo available|已有照片
ก่อน VAT · |Before VAT · |税前 · 
 ที่นั่ง)| seats)| 个座位)
 ที่นั่ง| seats| 个座位
 คน| guests| 人
 นาที| minutes| 分钟
 ก่อน VAT| before VAT| 税前
ความสุก: |Doneness: |熟度：
ซอส: |Sauce: |酱汁：
เพิ่ม |Added |已添加 
 ลงตะกร้าแล้ว| to your basket| 到购物篮
สมัครเรียบร้อย ยินดีต้อนรับ |Account created. Welcome |注册成功，欢迎 
 สู่ Dek Steak| to Dek Steak| 来到Dek Steak
 · เจ้าของร้าน| · Owner| · 店主
 · พื้นที่จัดการร้าน| · Restaurant management| · 餐厅管理
โต๊ะ |Table |餐桌 
รายการ |items |项 
รายการ|items|项'''
for line in DATA.splitlines():
    if line.count('|')==2:
        th,en,zh=line.split('|');CATALOG[th]=(en,zh)
# Default menu names are fully localized; custom names are left unchanged.
MENU_TH={'French Fries':'เฟรนช์ฟรายส์','Spaghetti Carbonara':'สปาเก็ตตีคาโบนารา','Caesar Salad':'ซีซาร์สลัด','Salmon Steak':'สเต๊กแซลมอน','Pork Chop':'พอร์กชอป','Ribeye Steak':'สเต๊กริบอาย','Chicken Steak':'สเต๊กไก่','น้ำเปล่า':'น้ำเปล่า','ชาเย็น':'ชาเย็น'}

# ข้อความนโยบาย Gmail ใช้ร่วมกันทั้งหน้าจอและข้อผิดพลาดจาก core.py
CATALOG.update({
    'สมัครและเข้าสู่ระบบด้วยอีเมล @gmail.com เท่านั้น': ('Use an @gmail.com email to sign up and sign in.', '注册和登录仅支持 @gmail.com 邮箱。'),
    'กรุณาใช้อีเมลที่ลงท้ายด้วย @gmail.com เท่านั้น': ('Please use an email ending in @gmail.com.', '请使用以 @gmail.com 结尾的邮箱。'),
})

# ปุ่มส่งออกใบเสร็จและข้อความผิดพลาดของการสร้างภาพในเบราว์เซอร์
CATALOG.update({
    'ดาวน์โหลดใบเสร็จ PNG': ('Download receipt PNG', '下载PNG收据'),
    'สร้างรูปใบเสร็จไม่สำเร็จ กรุณาลองใหม่': ('Could not create the receipt image. Please try again.', '无法生成收据图片，请重试。'),
})

def language():  # อ่านรหัสภาษาปัจจุบันจาก session และใช้ไทยเมื่อค่าไม่รองรับ
    value=st.session_state.get('language','th')
    return value if value in LANGUAGES else 'th'

def t(value,lang=None):  # แปลข้อความ UI ที่มีใน catalog โดยคงข้อความที่ไม่รู้จักไว้
    if not isinstance(value,str): return value
    lang=language() if lang is None else lang
    if lang=='th': return value
    pair=CATALOG.get(value)
    if pair: return pair[0 if lang=='en' else 1]
    if not re.search('[\u0e00-\u0e7f]',value):return value
    # Static sentence fragments may surround numeric values in HTML/f-strings.
    result=value
    for key in sorted(CATALOG,key=len,reverse=True):
        if re.search('[\u0e00-\u0e7f]',key) and key in result:
            result=result.replace(key,CATALOG[key][0 if lang=='en' else 1])
    return result

def menu_name(value):  # แปลชื่อเมนูเริ่มต้น ส่วนชื่อที่เจ้าของเพิ่มเองคงตามข้อมูลจริง
    if value not in MENU_TH:return value
    return MENU_TH[value] if language()=='th' else t(value)

def markup(value):  # แปลส่วนข้อความคงที่ของ HTML ที่ผู้พัฒนาเตรียมไว้
    # Only source-code literal fragments are passed here, never customer input.
    if language()=='th': return value
    if '<' not in value:return t(value)
    return re.sub(r'(?<=>)[^<>]+(?=<)|^[^<>]+(?=<)|(?<=>)[^<>]+$',lambda match:t(match.group()),value)

def display_option(formatter=None):  # สร้างตัวแสดงป้ายตัวเลือกตามภาษาโดยไม่เปลี่ยนค่าจริง
    selected_language=language()
    return lambda value:t(formatter(value) if formatter else str(value),selected_language)

def menu_description(value):  # แปลรายละเอียดเมนูที่มีคำแปลและคงข้อความอื่นไว้
    pair=CATALOG.get(value)
    return value if language()=='th' or not pair else pair[0 if language()=='en' else 1]

def translated_item_options(item):  # แปลป้ายและตัวเลือกอาหาร แต่รักษาหมายเหตุที่ลูกค้ากรอก
    parts=[]
    if item.get('doneness','ไม่ระบุ')!='ไม่ระบุ':parts.append(t('ความสุก: ')+t(item['doneness']))
    if item.get('sauce','ไม่ใส่ซอส')!='ไม่ใส่ซอส':parts.append(t('ซอส: ')+t(item['sauce']))
    if item.get('drink_option'):parts.append(t(item['drink_option']))
    if item.get('note'):parts.append(item['note'])
    return ' · '.join(parts)

EXTRA=''' · เรียงตามจำนวนที่ขายจากออเดอร์ยืนยันรับเงินแล้ว| · Ranked by approved paid quantities| · 按已确认收款的销量排名
 · โทร | · Phone | · 电话 
 ที่ยังไม่จบ ไปที่ “รายการของฉัน / ชำระเงิน”| is active. Open My orders / payment.| 正在进行中，请打开我的订单／付款。
 เมนู| meals| 道餐点
 เมนู · เปิดขาย | meals · Available | 道餐点 · 可售 
 ให้ตรงกัน| to match| 保持一致
QR นี้เป็น QR ของร้าน ยอดเงินไม่ได้ถูกฝังโดยแอป ลูกค้าต้องกรอกยอดตามออเดอร์|This is the restaurant QR. Enter the exact order amount in your banking app.|这是餐厅二维码，请在银行应用中输入订单金额。
QR รับเงินของร้าน JPEG/PNG (ไม่เกิน 5 MB)|Restaurant payment QR: JPEG/PNG, up to 5 MB|餐厅收款二维码：JPEG/PNG，不超过5MB
กดแก้ไขโต๊ะ แล้วเปิดแท็บแก้ไขโต๊ะเพื่อปรับข้อมูล|Choose Edit table, then open the editing tab.|选择编辑餐桌后，打开编辑标签页。
กรุณาเลือกภาพก่อนบันทึก|Please select an image before saving.|保存前请选择图片。
คิวครัวยังว่าง|The kitchen queue is empty|厨房队列为空
คืนรายการให้แจ้งชำระใหม่|Return for payment resubmission|退回并重新提交付款
คุณมีออเดอร์ #|You have order #|您有订单 #
จัดการออเดอร์ / คิวครัว|Manage orders / kitchen queue|管理订单／厨房队列
จัดการเมนู|Manage menu|管理菜单
ชื่อผู้รับเงิน / ธนาคาร / เลขบัญชีหรือพร้อมเพย์|Recipient / bank / account or PromptPay|收款人／银行／账户或PromptPay
ช่วงวันที่ไม่ถูกต้อง|Invalid date range|日期范围不正确
ช่วยลูกค้าตั้งรหัสผ่านใหม่|Help reset a customer password|帮助顾客重置密码
ตรวจชื่อผู้รับก่อนโอน และกรอกยอด ฿|Check the recipient before transferring. Enter THB |转账前核对收款人，输入泰铢金额 
ตรวจยืนยันตัวตนลูกค้าก่อน ตั้งรหัสผ่านชั่วคราวและแจ้งให้เปลี่ยนทันที ห้ามเผยแพร่รหัสผ่าน|Verify the customer first. Set a temporary password and ask them to change it immediately. Keep it private.|请先核实顾客身份，设置临时密码并要求立即修改。请勿公开密码。
ตรวจยืนยันตัวตนลูกค้าแล้ว|Customer identity verified|已核实顾客身份
ตรวจเงินสดที่รับจริง หรือยอดเข้าบัญชี/ชื่อผู้รับ/วันเวลา/เลขอ้างอิงให้ตรงกับออเดอร์ก่อนอนุมัติ สลิปอาจปลอมได้|Verify actual cash or bank credit, recipient, time and reference before approving. Receipts can be forged.|确认收款前请核实现金或到账金额、收款人、时间及交易编号。凭证可能伪造。
ตั้งค่า Gmail ในเครื่องด้วย python configure_email.py แล้วรีเฟรชหน้าเว็บ • ดูคู่มือ EMAIL_SETUP_TH.md|Run python configure_email.py locally, then refresh. See EMAIL_SETUP_TH.md.|在本机运行python configure_email.py后刷新。参阅EMAIL_SETUP_TH.md。
ตั้งค่าผู้ส่งครบแล้ว • ลูกค้าขอ OTP ที่หน้าเข้าสู่ระบบได้|Sender configured · Customers can request OTP on the sign-in page|发件人已设置 · 顾客可在登录页申请验证码
ตั้งแต่|From|从
ตำแหน่ง |Position |位置 
ตำแหน่งภาพ|Image position|图片位置
ถึง (รวมวันนี้)|To (inclusive)|至（含当天）
ทางร้านกำลังเพิ่มภาพสถานที่จริง คุณสามารถดูภาพร้านได้ที่หน้านี้เมื่ออัปโหลดแล้ว|Restaurant photos will appear here once uploaded.|上传后将在此显示餐厅照片。
ทุกเมนูมียอดขายในช่วงนี้|Every meal has sales in this period.|此期间所有餐点均有销量。
นับเฉพาะยอดที่ร้านยืนยันรับเงินแล้ว ตามวันรับเงินในประเทศไทย ไม่ใช่วันสร้างออเดอร์|Includes approved payments by Thailand payment date, not order creation date.|仅按泰国时间的确认收款日期统计，不按订单创建日期。
นำภาพออก|Remove image|移除图片
นำยอดรวมไปจ่ายที่เคาน์เตอร์ เจ้าของร้านจะกดยืนยันเมื่อรับเงินแล้ว|Pay the total at the counter. The owner confirms after receiving payment.|请在柜台支付总额，店主收款后确认。
นำรูปเมนูออก|Remove meal photo|移除餐点照片
นำออก|Remove|移除
บรรยากาศร้าน|Restaurant gallery|餐厅相册
บริการรีเซ็ตรหัสผ่านทางอีเมล|Email password recovery|邮件密码找回
บันทึก QR ของร้าน|Save restaurant QR|保存餐厅二维码
บันทึกภาพร้าน|Save restaurant photo|保存餐厅照片
บันทึกรูปอาหาร|Save meal photo|保存餐点照片
บันทึกเมนูแนะนำ|Save recommendations|保存推荐餐点
บันทึกเมนูใหม่ก่อน จากนั้นเลือกเมนูเพื่ออัปโหลดรูปอาหาร|Save the new meal first, then select it to upload a photo.|先保存新餐点，再选择餐点上传照片。
ประวัติการดำเนินการ (ล่าสุด 500 รายการ)|Activity log (latest 500)|操作记录（最近500条）
ปิดเพื่อซ่อนจากเมนูสั่งอาหาร|Disable to hide from the ordering menu|关闭后不显示在点餐菜单中
ผู้ให้บริการยอมรับการเชื่อมต่อแล้ว กรุณาทดลองรับ OTP จากหน้าเข้าสู่ระบบ|Email connection accepted. Test OTP delivery from the sign-in page.|邮件连接已通过，请在登录页测试验证码接收。
ภาพบรรยากาศร้าน|Restaurant gallery|餐厅照片
ภาพรวมที่นั่ง|Seating overview|座位概览
ภาพร้านจริง JPEG/PNG ไม่เกิน 5 MB|Restaurant photo: JPEG/PNG, up to 5 MB|餐厅照片：JPEG/PNG，不超过5MB
มีลูกค้า|Occupied|已有客人
มุมมอง|View|视图
มุมโปรดของคุณที่ร้าน|Your favourite spot|您喜爱的座位
ยังไม่มีออเดอร์|No orders yet|暂无订单
ยังไม่มีออเดอร์ที่ยืนยันรับเงินในช่วงนี้ จึงยังจัดอันดับขายดีไม่ได้|No approved paid orders in this period, so no ranking is available.|此期间暂无已确认收款订单，无法排名。
ยังไม่ได้ตั้งค่าบัญชีเจ้าของร้าน ให้ผู้ดูแลรัน python manage.py setup-owner ในโฟลเดอร์โปรเจกต์ก่อนเปิดบริการ|Owner account is not configured. Run python manage.py setup-owner before opening.|尚未设置店主账户，营业前请运行python manage.py setup-owner。
ยืนยันรหัสผ่านใหม่|Confirm new password|确认新密码
ยืนยันรหัสใหม่|Confirm new password|确认新密码
ยืนยันว่าไม่ได้โอนเงินสำหรับรายการนี้|I confirm that I have not transferred payment for this order|我确认尚未为此订单转账
รหัสผ่านชั่วคราว 10–128 ตัวอักษร|Temporary password (10–128 characters)|临时密码（10–128个字符）
รหัสผ่านเดิม|Current password|当前密码
รอตรวจเงิน|Awaiting payment check|等待核对收款
ราคานี้รวม VAT 7% แล้ว ไม่มีบวกเพิ่มตอนชำระ|This price includes 7% VAT; no extra VAT at checkout.|此价格已含7%增值税，结账时不再加收。
รับอาหารที่ร้านด้วยหมายเลขออเดอร์นี้|Collect your meal with this order number.|凭此订单号到店取餐。
รับเงินวันนี้|Today's receipts|今日收款
ราคาเมนูเปลี่ยน กรุณานำรายการนี้ออกแล้วเพิ่มใหม่เพื่อยืนยันราคา|The price changed. Remove and add this meal again.|价格已变动，请删除并重新添加餐点。
รายการอาหารทั้งหมด|All meals|所有餐点
รูปอาหารของเมนูนี้|Photo for this meal|此餐点照片
ร้านกำลังตรวจสอบการชำระเงิน กรุณารอการยืนยัน หากชำระเงินจริงแล้ว อย่าโอนซ้ำ|The restaurant is checking payment. Please wait; do not transfer again if already paid.|餐厅正在核对付款，请等待确认。已付款请勿重复转账。
ลำดับที่บันทึกไว้|Saved order|已保存顺序
วัตถุดิบ รสชาติ หรือเครื่องเคียงของเมนูนี้|Ingredients, taste or sides|食材、口味或配菜
สถานะขาย|Availability|销售状态
สั่งกลับบ้าน · ผู้รับ |Takeaway · Recipient |外带 · 取餐人 
สเต๊กเนื้อจะแสดงตัวเลือกระดับความสุกให้ลูกค้า|Beef steaks show doneness options.|牛排显示熟度选项。
สแกนจ่ายมื้อนี้|Scan to pay|扫码付款
หลักฐานสลิปที่ส่ง|Uploaded payment receipt|已上传的付款凭证
หากลูกค้าโอนแล้วแต่ยังไม่ได้แจ้ง ให้ลูกค้าแนบสลิปก่อน ห้ามยกเลิกจนกว่าจะตรวจเงิน|If transferred but not submitted, ask for the receipt. Check payment before cancelling.|如已转账但未提交，请顾客上传凭证。核实收款前请勿取消。
ออเดอร์ที่ยืนยันรับเงินแล้วจะแสดงที่นี่|Approved paid orders appear here.|已确认收款的订单显示在此。
อันดับขายดี (|Best sellers (|畅销排行 (
อัปโหลดภาพอาหารจริง JPEG/PNG ไม่เกิน 5 MB|Upload meal photo: JPEG/PNG, up to 5 MB|上传餐点照片：JPEG/PNG，不超过5MB
อัปโหลดรูปอาหารในแท็บแก้ไขเมนูก่อน แล้วกลับมาเลือกเมนูแนะนำ|Upload a meal photo in the edit tab before selecting recommendations.|先在编辑菜单页上传照片，再选择推荐餐点。
เช่น Ribeye Steak|e.g. Ribeye Steak|例如：肋眼牛排
เช่น T01|e.g. T01|例如：T01
เปลี่ยนเฉพาะสถานะขาย ราคาและรายละเอียดเมนูคงเดิม|Only availability changes; price and details stay the same.|仅更改销售状态，价格及说明保持不变。
เมนูเปิดขายที่มียอด 0 แยกจากเมนูหยุดขาย สถานะขายเป็นสถานะปัจจุบันของร้าน|Zero-sales available meals are separate from unavailable meals. Availability is current.|可售但销量为零的餐点与停售餐点分开显示，销售状态为当前状态。
เมนูแนะนำหน้าเข้าสู่ระบบ|Sign-in page recommendations|登录页推荐餐点
เรียงคิวตามเวลารับเงิน · สีเตือนเมื่อรอเกิน 15 และ 25 นาที นับจากรับเงิน|Ordered by payment time · Alerts after 15 and 25 minutes from payment|按收款时间排序 · 收款后等待超过15和25分钟提醒
เลือกสถานะอื่นเพื่อดูรายการ|Select another status to view orders.|选择其他状态查看订单。
เลือกเมนูเพื่อแก้ไข หรือเพิ่มใหม่|Select a meal to edit or add a new one.|选择餐点进行编辑或添加新餐点。
เลือกโต๊ะและอาหารเพื่อเริ่มมื้อนี้|Choose a table and meal to start.|选择餐桌及餐点以开始。
เลือกได้ไม่เกิน 5 เมนู เรียงจากตำแหน่ง 1 ไป 5 เมนูที่หยุดขายจะซ่อนจากหน้าลูกค้าอัตโนมัติ|Choose up to 5 meals in order. Unavailable meals are hidden from customers.|最多按顺序选择5道餐点，停售餐点将自动对顾客隐藏。
เหตุผลยกเลิกโดยร้าน|Restaurant cancellation reason|餐厅取消原因
แสดงล่าสุด 100 รายการ รายงานยอดขายดูได้ในหน้ารายงาน|Latest 100 orders. See Reports for sales.|显示最近100笔订单，销售数据请查看报告。
โต๊ะที่มีลูกค้า|Occupied tables|已占用餐桌
ไฟล์สำรองรวมรหัสผ่านที่แฮชและสลิปลูกค้า เก็บเฉพาะในที่ที่เจ้าของร้านเข้าถึงได้|Backups contain password hashes and customer receipts. Store them privately.|备份包含密码哈希和顾客付款凭证，请妥善保密保存。
ไม่มีรายการรับเงินในช่วงเวลานี้|No payments received in this period.|此期间无收款记录。
ไม่มีออเดอร์ในสถานะนี้|No orders with this status.|此状态无订单。
คิวครัวยังว่าง|Kitchen queue is empty|厨房队列为空
รายการนี้ถูกยกเลิก|This order was cancelled|此订单已取消
แจ้งก่อน |Submit before |请在此时间前提交 
หากหมดเวลา ระบบจะยกเลิกและคืนโต๊ะ|When time expires, the order is cancelled and the table released.|超时后系统将取消订单并释放餐桌。
ไม่พบสถานะรายการ|Unknown order status|未知订单状态
ไม่พบรายการ|Order not found|未找到订单
ใหม่|New|新
ขายดี|Best seller|畅销
เปิดขายเมนูนี้|Make available|设为可售
หยุดขายเมนูนี้|Mark unavailable|设为停售
รหัสผ่านควรมีความยาว 10–128 ตัวอักษร|Password must be 10–128 characters.|密码长度须为10–128个字符。
ชื่อควรมีความยาว 1–80 ตัวอักษร|Name must be 1–80 characters.|姓名长度须为1–80个字符。
ยืนยันรหัสไม่ถูกต้องหรือหมดอายุ|Invalid or expired code|验证码错误或过期
กรุณากรอกรหัสยืนยัน 8 หลัก|Please enter the 8-digit code.|请输入8位验证码。
ยอดเงินไม่ตรง กรุณาตรวจยอดรวม VAT|Amount does not match. Check the total including VAT.|金额不符，请核对含税总额。
ช่องทางชำระเงินไม่ถูกต้อง|Invalid payment method|付款方式不正确
กำลังดำเนินการ|In progress|进行中
รหัสผ่านใหม่ต้องต่างจากรหัสผ่านเดิม|New password must differ from the current one.|新密码须不同于旧密码。'''
for line in EXTRA.splitlines():
    if line.count('|')==2:
        th,en,zh=line.split('|');CATALOG[th]=(en,zh)

FINAL_TEXT='''มุมโปรดของคุณที่ Dek Steak|Your favourite spot at Dek Steak|您在Dek Steak喜爱的座位
ยกเลิกและคืนโต๊ะ|Cancel and release table|取消并释放餐桌
ยอดขาย ฿|Sales THB |销售额（泰铢）
ยอดที่ต้องโอน|Amount to transfer|应转账金额
ยอดยืนยันรับเงินรวม VAT 7% · ชี้ที่แท่งกราฟเพื่อดูยอดและจำนวนออเดอร์|Approved receipts including 7% VAT · Hover for amounts and order counts|已确认收款含7%增值税 · 悬停查看金额及订单数
ยอดรับเงินรายวัน|Daily receipts|每日收款
ยังไม่มีข้อมูลในรายการนี้|No data available|暂无数据
ยังไม่มียอดขาย (|No sales (|暂无销量 (
ยังไม่มียอดยืนยันรับเงินในช่วงนี้ จึงยังจัดอันดับขายดีไม่ได้|No approved payments in this period; rankings are not available.|此期间暂无已确认收款，无法排名。
QR / โอนเงิน|QR / transfer|二维码／转账
สั่งกลับบ้าน · ผู้รับ: |Takeaway · Recipient: |外带 · 取餐人：
โทร: |Phone: |电话：
ท่าน|guests|人
ใบเสร็จรับเงิน|Payment receipt|付款收据
รายการ: |Order: |订单：
ลูกค้า: |Customer: |顾客：
รับเงินเมื่อ: |Payment received: |收款时间：
รายการอาหาร|Meals|餐点
จำนวนเงิน|Amount|金额
รวมสุทธิ|Total|总额
ชำระผ่าน|Payment method|付款方式
ขอบคุณที่ให้เราดูแลมื้อนี้|Thank you for dining with us|感谢光临
เก็บไว้เป็นหลักฐานการรับเงิน|Keep as proof of payment|请保留作为付款证明
เอกสารนี้ไม่ใช่ใบกำกับภาษีเต็มรูป|This is not a full tax invoice.|此收据不是完整税务发票。
เปิดไฟล์แล้วกด Ctrl+P เพื่อพิมพ์หรือบันทึกเป็น PDF|Open the file and press Ctrl+P to print or save as PDF.|打开文件后按Ctrl+P打印或保存为PDF。
ยอดรับเงิน (บาท)|Receipts (THB)|收款金额（泰铢）
วันที่|Date|日期
สถานะการชำระเงิน|Payment status|付款状态
ภาพเมนูอาหาร|Meal photo|餐点照片
Medium Rare|Medium rare|三分熟
Medium|Medium|五分熟
Rare|Rare|一分熟
Well Done|Well done|全熟'''
for line in FINAL_TEXT.splitlines():
    if line.count('|')==2:
        th,en,zh=line.split('|');CATALOG[th]=(en,zh)
ERROR_TEXT='''กรุณาระบุเหตุผลที่ไม่อนุมัติ|Please state why payment was rejected.|请说明拒绝付款凭证的原因。
กรุณาระบุเหตุผลไม่เกิน 300 ตัวอักษร|Enter a reason of up to 300 characters.|原因最多300个字符。
การตั้งค่าอีเมลไม่ครบหรือไม่ถูกต้อง กรุณาตรวจผู้ส่ง พอร์ต และ TLS|Invalid email setup. Check the sender, port and TLS.|邮件设置不完整或不正确，请检查发件人、端口及TLS。
ข้อมูลร้านไม่ถูกต้อง|Invalid restaurant details|餐厅信息不正确
ข้อมูลเมนูไม่ถูกต้อง|Invalid meal data|餐点信息不正确
ข้อมูลเมนูไม่ถูกต้อง กรุณาตรวจตะกร้า|Invalid meal data. Please check your basket.|餐点信息不正确，请检查购物篮。
ข้อมูลโต๊ะไม่ถูกต้อง|Invalid table data|餐桌信息不正确
ชื่อโต๊ะนี้ถูกใช้แล้ว|This table name is already used.|此餐桌名称已使用。
ตรวจฐานข้อมูลหลังอัปเดตไม่ผ่าน|Database validation failed after the update.|更新后的数据库验证失败。
ตะกร้าหรือข้อมูลรายการไม่ถูกต้อง|Invalid basket or order data|购物篮或订单信息不正确
ประเภทภาพไม่ถูกต้อง|Invalid image type|图片类型不正确
ผู้ให้บริการปฏิเสธอีเมลผู้รับ|The email provider rejected the recipient.|邮件服务拒绝了收件人。
ผู้ให้บริการไม่ยอมรับบัญชีผู้ส่ง กรุณาตรวจ Gmail App Password และการยืนยันตัวตนสองขั้นตอน|Sender authentication failed. Check the Gmail App Password and two-step verification.|发件人验证失败，请检查Gmail应用密码及两步验证。
มีบัญชีเจ้าของร้านแล้ว ใช้คำสั่ง reset-owner หากลืมรหัสผ่าน|An owner account already exists. Use reset-owner to recover access.|店主账户已存在，忘记密码请使用reset-owner。
ยกเลิกได้เฉพาะรายการที่ยังไม่แจ้งชำระเงิน หากโอนแล้วให้ติดต่อร้าน|Only unsubmitted payments can be cancelled. If transferred, contact the restaurant.|仅未提交付款的订单可取消。如已转账，请联系餐厅。
ยังไม่ได้ตั้งค่าบริการส่งอีเมลอย่างครบถ้วน|Email delivery is not fully configured.|邮件发送服务尚未完整设置。
ยังไม่ได้รับการยืนยันชำระเงิน|Payment has not been approved.|付款尚未确认。
รหัสผ่านต้องมีความยาว 10–128 ตัวอักษร|Password must be 10–128 characters.|密码长度须为10–128个字符。
รหัสผ่านเดิมไม่ถูกต้อง|Incorrect current password|当前密码不正确
รหัสไม่ถูกต้อง หมดอายุ หรือใช้แล้ว กรุณาตรวจรหัสหรือขอรหัสใหม่|The code is invalid, expired or used. Check it or request a new code.|验证码错误、过期或已使用，请核对或申请新验证码。
รับเฉพาะรูป JPEG/PNG ขนาดไม่เกิน 16 ล้านพิกเซล|Only JPEG/PNG images up to 16 megapixels are accepted.|仅接受不超过1600万像素的JPEG/PNG图片。
ราคาเมนูเปลี่ยน กรุณานำเมนูออกแล้วเพิ่มใหม่เพื่อยืนยันราคาปัจจุบัน|A meal price changed. Remove and add it again at the current price.|餐点价格已变动，请删除并按当前价格重新添加。
รายการนี้ไม่อยู่ในสถานะรอชำระเงิน|This order is not awaiting payment.|此订单不处于等待付款状态。
รูปต้องไม่เกิน 5 MB|Image must be no larger than 5 MB.|图片不得超过5MB。
รูปแบบรับอาหารไม่ถูกต้อง|Invalid dining mode|用餐方式不正确
ร้านยังไม่ได้ตั้งค่า QR รับเงิน กรุณาเลือกเงินสด|Payment QR is not configured. Please choose cash.|收款二维码尚未设置，请选择现金付款。
ลองเข้าสู่ระบบหลายครั้ง กรุณารอ 15 นาที|Too many sign-in attempts. Please wait 15 minutes.|登录尝试过多，请等待15分钟。
สถานะรายการเปลี่ยนแล้ว กรุณารีเฟรช|Order status changed. Please refresh.|订单状态已变更，请刷新。
สถานะเปิดขายไม่ถูกต้อง|Invalid availability status|销售状态不正确
สลิปนี้ถูกใช้กับรายการอื่นแล้ว|This receipt was used for another order.|此付款凭证已用于其他订单。
สลิปนี้เคยถูกปฏิเสธแล้ว กรุณาตรวจเหตุผลของร้านและแนบสลิปที่ถูกต้อง|This receipt was rejected. Check the reason and upload the correct receipt.|此凭证曾被拒绝，请查看原因并上传正确凭证。
อ่านการตั้งค่าอีเมลไม่ได้ กรุณาตรวจรูปแบบ .streamlit/secrets.toml|Unable to read email settings. Check .streamlit/secrets.toml.|无法读取邮件设置，请检查.streamlit/secrets.toml。
เชื่อมต่อบริการอีเมลไม่สำเร็จ กรุณาตรวจการตั้งค่าและเครือข่าย|Email connection failed. Check settings and network.|邮件连接失败，请检查设置及网络。
เมนูแนะนำต้องเป็นเมนูที่มีรูปอาหารแล้ว|Recommended meals must have photos.|推荐餐点须已有照片。
เลือกระดับความสุกได้เฉพาะสเต๊กเนื้อ|Doneness is available for beef steaks only.|仅牛排可选择熟度。
เลือกเมนูแนะนำไม่เกิน 5 เมนู และห้ามเลือกซ้ำ|Choose up to 5 distinct recommended meals.|最多选择5道不重复的推荐餐点。
เหตุผลยาวเกิน 300 ตัวอักษร|Reason exceeds 300 characters.|原因超过300个字符。
แก้โต๊ะได้เมื่อโต๊ะว่างเท่านั้น|Only available tables can be edited.|仅空桌可编辑。
ไฟล์รูปภาพไม่ถูกต้อง|Invalid image file|图片文件不正确
ไม่พบบัญชีลูกค้า|Customer account not found|未找到顾客账户
ไม่พบเมนู|Meal not found|未找到餐点
ไม่พบเมนูที่ต้องการใส่รูป|Meal for this photo was not found.|未找到要添加照片的餐点。
ไม่สามารถสมัครบัญชีเจ้าของร้านผ่านหน้าเว็บ|Owner accounts cannot be registered through the website.|无法通过网站注册店主账户。'''
for line in ERROR_TEXT.splitlines():
    if line.count('|')==2:
        th,en,zh=line.split('|');CATALOG[th]=(en,zh)

def localized_selectbox(container,label,options,**kwargs):  # รักษาค่าที่เลือกขณะเปลี่ยนภาษาและแยก key ภายในจากป้ายแสดง
    """Recreate translated option labels while preserving the canonical selection."""
    choices=list(options)
    base=kwargs.get('key')
    fmt=kwargs.get('format_func',str)
    lang=language()
    # Numeric quantities do not need a new frontend label or widget identity.
    if not base or lang=='th' or all(fmt(value)==str(value) for value in choices):
        return container.selectbox(label,choices,**kwargs)
    actual=f'{base}__{lang}'
    selected=st.session_state.get(base)
    if selected not in choices:
        index=kwargs.get('index',0)
        selected=choices[index] if choices and index is not None else None
    if st.session_state.get(f'_language_for_{base}')!=lang:
        if selected is not None:st.session_state[actual]=selected
        st.session_state[f'_language_for_{base}']=lang
    kwargs['key']=actual
    callback=kwargs.get('on_change')
    if callback:
        callback_args=kwargs.pop('args',())
        callback_kwargs=kwargs.pop('kwargs',{})
        def changed():  # อัปเดตค่าตัวเลือกหลักก่อนเรียก callback ของผู้ใช้งานฟังก์ชัน
            st.session_state[base]=st.session_state[actual]
            callback(*callback_args,**callback_kwargs)
        kwargs['on_change']=changed
    value=container.selectbox(label,choices,**kwargs)
    st.session_state[base]=value
    return value

MORE_ORDERS={
'คุณมีออเดอร์ที่รอชำระหรือรอตรวจเงิน กรุณาดำเนินการรายการนั้นก่อนสั่งเพิ่ม':('You have an order awaiting payment or approval. Finish payment before adding another order.','您有等待付款或确认收款的订单，请先完成该订单付款。'),
'ต้องยืนยันรับเงินออเดอร์ก่อนหน้าก่อนสั่งเพิ่มที่โต๊ะนี้':('The previous order must be approved as paid before ordering more at this table.','此桌原订单须先确认收款，才能加点。'),
'สั่งเพิ่มได้แล้ว เลือกทานที่โต๊ะเดิมหรือสั่งกลับบ้าน รายการใหม่ชำระแยกจากรายการก่อนหน้า':('You can order more for your table or takeaway. The new order has a separate payment.','您可以在原桌加点或选择外带，新订单单独付款。'),
'โต๊ะของคุณ · สั่งเพิ่มได้':('Your table · Order more','您的餐桌 · 可加点'),
}
CATALOG.update(MORE_ORDERS)

CATALOG['จบรายการ (โต๊ะยังมีออเดอร์อื่น)']=('Complete (other orders remain at this table)','完成（此桌仍有其他订单）')

CATALOG['สั่งอาหารเพิ่ม / สั่งกลับบ้าน']=('Order more / takeaway','加点／外带')

# คำอธิบายราคาแบบรวม VAT เพื่อให้ทั้งสามภาษาแสดงวิธีคิดตรงกัน
CATALOG.update({
    'ราคารวม VAT (บาท)': ('Price including VAT (THB)', '含税价格（泰铢）'),
    'ราคารวม VAT': ('Price including VAT', '含税价格'),
    'ราคารวม VAT 7% แล้ว': ('Price includes 7% VAT', '价格已含7%增值税'),
    'ราคาต่อรายการรวม VAT 7% แล้ว': ('Item prices include 7% VAT', '单项价格已含7%增值税'),
    'ราคาต่อรายการก่อน VAT 7%': ('Item prices exclude 7% VAT', '单项价格未含7%增值税'),
    'ราคาหน้าเมนูรวม VAT 7% แล้ว • มารับอาหารที่ร้าน': ('Menu prices include 7% VAT • Pick up at the restaurant', '菜单价格已含7%增值税 • 到店取餐'),
    'ราคาหน้าเมนูรวม VAT 7% แล้ว • โต๊ะจะถูกกันเมื่อยืนยันออเดอร์': ('Menu prices include 7% VAT • Table reserved when order is confirmed', '菜单价格已含7%增值税 • 确认订单后保留餐桌'),
})
