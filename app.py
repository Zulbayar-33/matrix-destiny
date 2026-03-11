import streamlit as st
import datetime
import os

st.set_page_config(
    page_title="Хосын хувь тавилангийн матриц",
    page_icon="🔮",
    layout="centered"
)

st.title("🔮 Хосын хувь тавилангийн матриц")

# -----------------------
# Helper functions
# -----------------------

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
    labels = [
        "1", "2", "3",
        "4", "5", "6",
        "7", "8", "9"
    ]
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

# -----------------------
# Payment section
# -----------------------

st.subheader("💳 Төлбөр")
st.write("Бүрэн тайлан харахын тулд **2000₮** төлнө үү.")

qr_path = "qr.png"

if os.path.exists(qr_path):
    st.image(qr_path, caption="QR кодоор төлнө үү", use_container_width=True)
else:
    st.warning("⚠️ qr.png файл олдсонгүй. app.py-тай нэг folder дотор qr.png хийнэ үү.")

uploaded = st.file_uploader(
    "Гүйлгээний screenshot upload",
    type=["png", "jpg", "jpeg", "webp"],
    key="payment_upload"
)

# -----------------------
# Preview section
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

# -----------------------
# Full result after payment proof
# -----------------------

if uploaded is not None:
    st.success("✅ Төлбөрийн баримт хүлээн авлаа")

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

    st.subheader("📊 Бүрэн үр дүн")

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

else:
    st.info("Бүрэн тайлан харахын тулд төлбөрийн screenshot upload хийнэ үү.")