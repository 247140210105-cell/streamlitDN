import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components



# ==============================
# CẤU HÌNH
# ==============================

API_KEY = "14ca543dd2310109fc8a0752d7909f51"
CITY = "Da Nang"
COUNTRY = "VN"

EMAIL_SENDER = "247140210105@hpu2.edu.vn"
EMAIL_PASSWORD = "123456Aa@"
EMAIL_RECEIVER = "trai2526200@gmail.com"

# ==============================
# LẤY DỮ LIỆU THỜI TIẾT
# ==============================

def get_weather_data():
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "q": f"{CITY},{COUNTRY}",
        "appid": API_KEY,
        "units": "metric",
        "lang": "vi"
    }

    try:
        res = requests.get(url, params=params, timeout=10)

        # lỗi HTTP (404, 401…)
        res.raise_for_status()

        data = res.json()

        weather_main = data["weather"][0]["main"]
        weather_desc = data["weather"][0]["description"]
        temperature = data["main"]["temp"]

        return weather_main, weather_desc, temperature

    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Lỗi HTTP: {e}")
    except requests.exceptions.ConnectionError:
        st.error("❌ Không có kết nối internet")
    except requests.exceptions.Timeout:
        st.error("❌ Timeout (API phản hồi chậm)")
    except Exception as e:
        st.error(f"❌ Lỗi khác: {e}")

    return None, None, None

def load_html(city, desc, temp):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    from datetime import datetime

    html = html.replace("{{city}}", city)
    html = html.replace("{{desc}}", desc)
    html = html.replace("{{temp}}", str(temp))
    html = html.replace("{{time}}", datetime.now().strftime("%H:%M:%S"))

    return html

# ==============================
# KIỂM TRA MƯA
# ==============================

st_autorefresh(interval=10000, key="refresh")  # 10 giây

def is_rain(main, desc):
    keywords = ["rain", "drizzle", "thunderstorm"]
    return any(k in main.lower() or k in desc.lower() for k in keywords)

# ==============================
# GỬI EMAIL
# ==============================

def send_email(message):
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "🌧️ Nhắc nhở thời tiết"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        return True
    except:
        return False

# ==============================
# GIAO DIỆN STREAMLIT
# ==============================

st.set_page_config(page_title="Theo dõi thời tiết", page_icon="🌦️")

st.title("🌦️ Theo dõi thời tiết & cảnh báo mưa")

st.write(f"📍 Thành phố: **{CITY}**")

if "history" not in st.session_state:
    st.session_state.history = []  # lưu (time, temp)

# Nút kiểm tra
if st.button("🔍 Kiểm tra thời tiết ngay"):
    main, desc, temp = get_weather_data()

    if main is None:
        st.error("❌ Lỗi lấy dữ liệu thời tiết")
    else:
        html = load_html(CITY, desc, temp)
        components.html(html, height=500)

        now = datetime.now().strftime("%H:%M:%S")
        st.session_state.history.append({"time": now, "temp": temp})

        if is_rain(main, desc):
            st.warning("🌧️ Có khả năng mưa!")

            now = datetime.now().strftime("%d/%m/%Y %H:%M")

            message = f"""
Thời gian: {now}
Địa điểm: {CITY}

Dự báo: {desc}
Nhiệt độ: {temp}°C

Có khả năng mưa! Hãy mang ô!
"""

            if st.button("📧 Gửi email cảnh báo"):
                if send_email(message):
                    st.success("📨 Đã gửi email!")
                else:
                    st.error("❌ Gửi email thất bại")
        else:
            st.info("☀️ Không có mưa")


st.subheader("📊 Biểu đồ nhiệt độ")

if len(st.session_state.history) > 0:
    df = pd.DataFrame(st.session_state.history)
    df = df.set_index("time")

    st.line_chart(df["temp"])
else:
    st.info("Chưa có dữ liệu. Hãy bấm kiểm tra thời tiết.")
