import io
import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

# Google API Anahtarını Yükle
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# API Anahtarı Kontrolü
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_api_key_here":
    st.error("Lütfen .env dosyasında GOOGLE_API_KEY'i ayarlayın.")
    st.stop()

# Gemini Modelini Yapılandır
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- KOKTEYL TEMASINA GÖRE DEĞİŞTİRİLEN KISIMLAR ---

# Streamlit Sayfa Yapılandırması
st.set_page_config(page_title="Kokteyl Asistanı", page_icon="🍸")
st.title("🍸 Kokteyl Miksoloji Asistanı")
st.subheader("Elinizdeki içkilerle ve malzemelerle neler hazırlayabileceğinizi keşfedin")

# Oturum Durumu Başlatma
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Merhaba! Elinizde bulunan içki ve kokteyl malzemelerini yazabilir veya fotoğrafını yükleyebilirsiniz. Size uygun kokteyl tarifleri önereceğim."
        }
    ]

# Sistem Talimatı (Chatbot'un Rolü ve Kuralları - KOKTEYL ODAKLI)
system_instruction = """
Sen profesyonel bir miksoloji chatbotusun. Kullanıcıların elindeki içki, meyve, şurup ve diğer malzemelere göre kokteyl tarifleri öneriyorsun.
Aşağıdaki kurallara uy:
1. Öncelikle klasik ve popüler kokteyl tariflerini öner, ancak istenirse farklı temalı kokteyller de sunabilirsin.
2. Kullanıcı malzemeleri metin olarak girdiğinde veya resim yüklediğinde, bu malzemelerle yapılabilecek kokteyl tariflerini öner.
3. Her tarif için **içeriği (oranları ile birlikte)**, **yapılış adımlarını** ve **gerekli kokteyl araçlarını (shaker, süzgeç, bardak türü)** detaylı olarak açıkla.
4. Eğer eksik bir içki veya malzeme varsa, alternatif içki/malzeme veya basitleştirilmiş tarifler öner. (Örn: Cointreau yerine Triple Sec)
5. Cevaplarını Türkçe olarak ver.
6. Resim yüklendiğinde, resimdeki içkileri ve malzemeleri tanımla ve onlarla yapılabilecek kokteyl tarifleri öner.
"""

# --- KODUN GERİ KALANI AYNI KALIYOR (Chat Mantığı) ---

# Geçmiş Mesajları Gösterme
# history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Giriş Seçeneği
input_option = st.radio(
    "Tarif önerisi alma yöntemi",
    ("Metin ile malzeme/içki girin", "Malzemelerin fotoğrafını yükleyin"),
)

# Gemini'ye gönderilecek mesajlar listesini hazırla
gemini_messages = []

# --- METİN GİRİŞİ SEÇENEĞİ ---
if input_option == "Metin ile malzeme/içki girin":
    user_input = st.chat_input("Elinizdeki içki ve malzemeleri yazın...")

    if user_input:
        # Kullanıcı Mesajını Oturum Durumuna Ekle
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Gemini için Mesajları Hazırla
        # 1. Sistem Talimatı ve Model Onayı
        gemini_messages = [
            {"role": "user", "parts": [system_instruction]},
            {"role": "model", "parts": ["Anladım, bu kurallara göre hareket edeceğim."]},
        ]

        # 2. Geçmiş mesajları ekle
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                if msg["content"] != "Bu fotoğraftaki malzemelerle neler yapabiliriz?":
                    gemini_messages.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg["content"]]})
        
        # Asistan Mesajı Alanı
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.text("Kokteyl tarifleri hazırlanıyor...")

            # Gemini API Çağrısı
            response = model.generate_content(gemini_messages)
            assistant_response = response.text

            # Yanıtı Göster ve Oturum Durumuna Ekle
            message_placeholder.write(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})


# --- RESİM YÜKLEME SEÇENEĞİ ---
elif input_option == "Malzemelerin fotoğrafını yükleyin":
    uploaded_file = st.file_uploader(
        "Malzemelerin fotoğrafını yükleyin", type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        # Yüklenen Resmi Aç ve Göster
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen fotoğraf", use_column_width=True)

        # Kullanıcı Mesajını Hazırla
        user_message = "Bu fotoğraftaki malzemelerle neler yapabiliriz?"
        
        # 'Tarif Öner' butonu
        if st.button("Tarif Öner"):
            
            # Kullanıcı Mesajını Oturum Durumuna Ekle
            st.session_state.messages.append({"role": "user", "content": user_message})
            with st.chat_message("user"):
                st.write(user_message)

            # Gemini için Mesajları Hazırla
            gemini_messages = []

            # 1. Sistem Talimatı
            gemini_messages.append({"role": "user", "parts": [system_instruction]})
            
            # 2. Model Onayı
            gemini_messages.append(
                {
                    "role": "model",
                    "parts": ["Anladım, bu kurallara göre hareket edeceğim."],
                }
            )
            
            # 3. Resimli Kullanıcı İsteği (Inline data formatı)
            gemini_messages.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": "Bu fotoğrafta hangi içkiler/malzemeler var? Bu malzemelerle yapılabilecek kokteyl tarifleri önerir misin?",
                        },
                        {
                            "inline_data": {
                                "mime_type": uploaded_file.type,
                                "data": uploaded_file.getvalue(),
                            },
                        },
                    ],
                }
            )

            # Asistan Mesajı Alanı
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.text("Kokteyl tarifleri hazırlanıyor...")

                # Gemini API Çağrısı
                response = model.generate_content(gemini_messages)
                assistant_response = response.text

                # Yanıtı Göster ve Oturum Durumuna Ekle
                message_placeholder.write(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
