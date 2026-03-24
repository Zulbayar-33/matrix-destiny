import streamlit as st
import datetime
import os
import sqlite3
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Хосын хувь тавилангийн матриц",
    page_icon="🔮",
    layout="centered"
)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "subscriptions.db"
PAYMENT_DIR = BASE_DIR / "payments"

PAYMENT_DIR.mkdir(exist_ok=True)

PLAN_MAP = {
    "7 хоног - 3000₮": {"price": 3000, "days": 7, "qr": "qr_codes/7days.png"},
    "1 сар - 10000₮": {"price": 10000, "days": 30, "qr": "qr_codes/1month.png"},
    "6 сар - 30000₮": {"price": 30000, "days": 180, "qr": "qr_codes/6months.png"},
    "1 жил - 50000₮": {"price": 50000, "days": 365, "qr": "qr_codes/1year.png"},
}

# =========================
# DB
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_key TEXT NOT NULL,
            phone TEXT,
            plan_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            payment_image TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_customer_key(phone: str) -> str:
    phone = (phone or "").strip()
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()


def save_subscription(phone: str, plan_name: str, price: int, days: int, payment_image_path: str):
    today = datetime.date.today()
    expiry = today + datetime.timedelta(days=days)

    customer_key = get_customer_key(phone)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO subscriptions (
            customer_key, phone, plan_name, price, start_date, expiry_date, payment_image, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_key,
        phone,
        plan_name,
        price,
        str(today),
        str(expiry),
        payment_image_path,
        str(datetime.datetime.now())
    ))

    conn.commit()
    conn.close()

    return today, expiry


def get_latest_active_subscription(phone: str):
    customer_key = get_customer_key(phone)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT plan_name, price, start_date, expiry_date, payment_image, created_at
        FROM subscriptions
        WHERE customer_key = ?
        ORDER BY id DESC
        LIMIT 1
    """, (customer_key,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    plan_name, price, start_date, expiry_date, payment_image, created_at = row

    today = datetime.date.today()
    is_active = today <= datetime.date.fromisoformat(expiry_date)

    return {
        "plan_name": plan_name,
        "price": price,
        "start_date": start_date,
        "expiry_date": expiry_date,
        "payment_image": payment_image,
        "created_at": created_at,
        "is_active": is_active
    }


# =========================
# MATRIX / HELPER FUNCTIONS
# =========================
def reduce_number(n):
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def life_path(date_text):
    digits = [int(x) for x in date_text.replace("-", "")]
    return reduce_number(sum(digits))


def build_matrix(num):
    return [reduce_number(num + i) for i in range(9)]


def compatibility(a, b):
    diff = abs(a - b)
    if diff == 0:
        return "💞 Төгс тохироо"
    elif diff <= 2:
        return "❤️ Сайн тохироо"
    elif diff <= 4:
        return "💛 Дунд зэрэг тохироо"
    else:
        return "⚡ Сорилттой тохироо"


def zodiac(month, day):
    signs = [
        ((1, 20), "♑ Матар"),
        ((2, 19), "♒ Хумх"),
        ((3, 21), "♓ Загас"),
        ((4, 20), "♈ Хонь"),
        ((5, 21), "♉ Үхэр"),
        ((6, 21), "♊ Ихэр"),
        ((7, 23), "♋ Мэлхий"),
        ((8, 23), "♌ Арслан"),
        ((9, 23), "♍ Охин"),
        ((10, 23), "♎ Жинлүүр"),
        ((11, 22), "♏ Хилэнц"),
        ((12, 22), "♐ Нум"),
        ((12, 31), "♑ Матар")
    ]
    for (m, d), sign in signs:
        if (month, day) <= (m, d):
            return sign
    return "♑ Матар"


def calculate_age(birth_date):
    today = datetime.date.today()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    return age


def matrix_grid_html(matrix):
    labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    html = """
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;">
    """
    for i, value in enumerate(matrix):
        html += f"""
        <div style="
            background:#1e293b;
            border:1px solid #334155;
            border-radius:14px;
            padding:16px;
            text-align:center;
            color:white;
        ">
            <div style="font-size:24px;font-weight:bold;">{value}</div>
            <div style="font-size:12px;color:#cbd5e1;">Cell {labels[i]}</div>
        </div>
        """
    html += "</div>"
    return html


# =========================
# OPENAI
# =========================
def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def extract_response_text(response):
    text = getattr(response, "output_text", None)
    if text:
        return text

    try:
        chunks = []
        for item in response.output:
            if getattr(item, "type", "") == "message":
                for content in item.content:
                    if getattr(content, "type", "") in ("output_text", "text"):
                        chunks.append(content.text)
        return "\n".join(chunks).strip()
    except Exception:
        return "AI хариу уншиж чадсангүй."


def build_ai_prompt(name1, date1, name2, date2, lp1, lp2, z1, z2, age1, age2, matrix1, matrix2, plan_name):
    return f"""
Та Монгол хэл дээр мэргэжлийн, ойлгомжтой, хэрэглэгчид таалагдахуйц тайлан гаргадаг эксперт болно.

Доорх 2 хүний хосын хувь тавилангийн матрицын ДЭЛГЭРЭНГҮЙ тайлан гарга.

1-р хүн:
- Нэр: {name1}
- Төрсөн огноо: {date1}
- Нас: {age1}
- Орд: {z1}
- Life Path: {lp1}
- Матриц: {matrix1}

2-р хүн:
- Нэр: {name2}
- Төрсөн огноо: {date2}
- Нас: {age2}
- Орд: {z2}
- Life Path: {lp2}
- Матриц: {matrix2}

Хосын үндсэн тохироо:
- Үр дүн: {compatibility(lp1, lp2)}

Сонгосон багц:
- {plan_name}

Дараах бүтэцтэй, цэвэр Монгол хэлээр, emoji бага хэрэглэж, гоё тайлан бич:
1. Ерөнхий дүгнэлт
2. 1-р хүний зан төлөв, давуу тал
3. 2-р хүний зан төлөв, давуу тал
4. Хосын сэтгэлзүйн нийцэл
5. Харилцаанд гарч болох сорилтууд
6. Илүү сайн ойлголцох зөвлөмж
7. Ирээдүйн төлөвийн товч дүгнэлт

Хариулт нь хэт богино биш, гэхдээ хэт нуршуу биш байна.
"""


def generate_ai_report(name1, date1, name2, date2, lp1, lp2, z1, z2, age1, age2, matrix1, matrix2, plan_name):
    client = get_openai_client()
    if client is None:
        return "⚠️ OPENAI_API_KEY тохируулагдаагүй байна."

    prompt = build_ai_prompt(
        name1, date1, name2, date2,
        lp1, lp2, z1, z2, age1, age2,
        matrix1, matrix2, plan_name
    )

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Та Монгол хэл дээр хосын хувь тавилангийн тайлан гаргадаг туслах."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return extract_response_text(response)
    except Exception as e:
        return f"⚠️ AI тайлан үүсгэх үед алдаа гарлаа: {e}"


# =========================
# FILE SAVE
# =========================
def save_uploaded_payment(uploaded_file, phone: str):
    suffix = Path(uploaded_file.name).suffix.lower()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_phone = "".join(ch for ch in phone if ch.isdigit()) or "unknown"
    file_name = f"{safe_phone}_{ts}{suffix}"
    file_path = PAYMENT_DIR / file_name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path)


# =========================
# APP START
# =========================
init_db()
st.title("🔮 Хосын хувь тавилангийн матриц")
st.markdown("Та төлөвлөгөө сонгож, төлбөрийн баримтаа upload хийсний дараа AI дэлгэрэнгүй тайлан авах боломжтой.")

# -----------------------
# Input
# -----------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Эрэгтэй")
    name1 = st.text_input("Нэр", key="name1")
    date1 = st.date_input(
        "Төрсөн огноо",
        min_value=datetime.date(1950, 1, 1),
        max_value=datetime.date(2016, 12, 31),
        value=datetime.date(1996, 1, 16),
        key="date1"
    )

with col2:
    st.subheader("Эмэгтэй")
    name2 = st.text_input("Нэр", key="name2")
    date2 = st.date_input(
        "Төрсөн огноо",
        min_value=datetime.date(1950, 1, 1),
        max_value=datetime.date(2016, 12, 31),
        value=datetime.date(2001, 5, 19),
        key="date2"
    )

st.divider()

# -----------------------
# Preview
# -----------------------
st.subheader("👀 Preview")

preview_lp1 = life_path(str(date1))
preview_lp2 = life_path(str(date2))

pcol1, pcol2, pcol3 = st.columns(3)
with pcol1:
    st.metric("1-р хүний Life Path", preview_lp1)
with pcol2:
    st.metric("2-р хүний Life Path", preview_lp2)
with pcol3:
    st.metric("Тохироо", compatibility(preview_lp1, preview_lp2))

st.divider()

# -----------------------
# Payment / Activation
# -----------------------
st.subheader("💳 Төлбөр ба идэвхжүүлэлт")

phone = st.text_input("Утасны дугаар", placeholder="99112233")

plan_name = st.selectbox("Төлөвлөгөө сонгох", list(PLAN_MAP.keys()))
selected_price = PLAN_MAP[plan_name]["price"]
selected_days = PLAN_MAP[plan_name]["days"]

st.info(f"Сонгосон багц: {plan_name}")
st.write(f"💰 Төлөх дүн: **{selected_price}₮**")
st.write(f"⏳ Хугацаа: **{selected_days} хоног**")

qr_path = BASE_DIR / PLAN_MAP[plan_name]["qr"]

if qr_path.exists():
    st.image(str(qr_path), caption=f"{plan_name} төлбөр", use_container_width=True)
else:
    st.warning(f"⚠️ QR файл олдсонгүй: {qr_path}")

uploaded = st.file_uploader(
    "Гүйлгээний screenshot upload",
    type=["png", "jpg", "jpeg", "webp"],
    key="payment_upload"
)

activate_btn = st.button("✅ Идэвхжүүлэх", use_container_width=True)

if activate_btn:
    if not phone.strip():
        st.error("Утасны дугаараа оруулна уу.")
    elif uploaded is None:
        st.error("Төлбөрийн баримтын зураг upload хийнэ үү.")
    else:
        saved_path = save_uploaded_payment(uploaded, phone)
        start_date, expiry_date = save_subscription(
            phone=phone,
            plan_name=plan_name,
            price=selected_price,
            days=selected_days,
            payment_image_path=saved_path
        )
        st.success(f"✅ Багц идэвхжлээ. Эхлэх: {start_date} | Дуусах: {expiry_date}")

st.divider()

# -----------------------
# Subscription status
# -----------------------
st.subheader("📦 Идэвхтэй эрх шалгах")

check_phone = st.text_input("Идэвхтэй багц шалгах утасны дугаар", value=phone, key="check_phone")
check_btn = st.button("Шалгах", use_container_width=True)

active_sub = None

if check_btn or check_phone.strip():
    if check_phone.strip():
        active_sub = get_latest_active_subscription(check_phone.strip())

if active_sub:
    st.write(f"**Багц:** {active_sub['plan_name']}")
    st.write(f"**Эхэлсэн:** {active_sub['start_date']}")
    st.write(f"**Дуусах:** {active_sub['expiry_date']}")
    if active_sub["is_active"]:
        st.success("✅ Идэвхтэй эрх байна")
    else:
        st.warning("⛔ Эрхийн хугацаа дууссан байна")
elif check_phone.strip():
    st.info("Одоогоор энэ дугаарт идэвхтэй мэдээлэл олдсонгүй.")

st.divider()

# -----------------------
# Full result
# -----------------------
st.subheader("📊 Бүрэн үр дүн")

current_phone = check_phone.strip() if check_phone.strip() else phone.strip()
current_sub = get_latest_active_subscription(current_phone) if current_phone else None

if current_sub and current_sub["is_active"]:
    d1 = str(date1)
    d2 = str(date2)

    lp1 = life_path(d1)
    lp2 = life_path(d2)

    z1 = zodiac(date1.month, date1.day)
    z2 = zodiac(date2.month, date2.day)

    age1 = calculate_age(date1)
    age2 = calculate_age(date2)

    matrix1 = build_matrix(lp1)
    matrix2 = build_matrix(lp2)

    info1, info2 = st.columns(2)

    with info1:
        st.markdown(f"### {name1 if name1 else '1-р хүн'}")
        st.write(f"**Төрсөн огноо:** {date1}")
        st.write(f"**Нас:** {age1}")
        st.write(f"**Орд:** {z1}")
        st.write(f"**Life Path:** {lp1}")

    with info2:
        st.markdown(f"### {name2 if name2 else '2-р хүн'}")
        st.write(f"**Төрсөн огноо:** {date2}")
        st.write(f"**Нас:** {age2}")
        st.write(f"**Орд:** {z2}")
        st.write(f"**Life Path:** {lp2}")

    st.subheader("❤️ Хосын тохироо")
    st.success(compatibility(lp1, lp2))

    st.subheader("🔢 Matrix Destiny Chart")

    mcol1, mcol2 = st.columns(2)

    with mcol1:
        st.markdown(f"**{name1 if name1 else '1-р хүн'} матриц**")
        st.markdown(matrix_grid_html(matrix1), unsafe_allow_html=True)

    with mcol2:
        st.markdown(f"**{name2 if name2 else '2-р хүн'} матриц**")
        st.markdown(matrix_grid_html(matrix2), unsafe_allow_html=True)

    st.subheader("📋 Matrix numbers")
    st.write(f"**{name1 if name1 else '1-р хүн'}:** {matrix1}")
    st.write(f"**{name2 if name2 else '2-р хүн'}:** {matrix2}")

    st.divider()
    st.subheader("🤖 AI Дэлгэрэнгүй тайлан")

    if st.button("AI тайлан гаргах", use_container_width=True):
        with st.spinner("AI тайлан үүсгэж байна..."):
            ai_report = generate_ai_report(
                name1=name1 if name1 else "1-р хүн",
                date1=str(date1),
                name2=name2 if name2 else "2-р хүн",
                date2=str(date2),
                lp1=lp1,
                lp2=lp2,
                z1=z1,
                z2=z2,
                age1=age1,
                age2=age2,
                matrix1=matrix1,
                matrix2=matrix2,
                plan_name=current_sub["plan_name"]
            )
        st.markdown(ai_report)

else:
    st.info("Бүрэн үр дүн харахын тулд эхлээд төлбөрөө идэвхжүүлнэ үү.")