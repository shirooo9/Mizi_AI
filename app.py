import streamlit as st
import os
import json
import requests
import psutil
import qrcode
from PIL import Image

try:
    mizi_img = Image.open("assets/mizi_avatar.jpg") 
    user_img = Image.open("assets/user_avatar.jpg")
    page_icon_img = Image.open("assets/mizi_icon.jpg")
except Exception:
    mizi_img = "🎀"
    user_img = "🙎‍♂️"
    page_icon_img = "🎀"

a = "sk-or-v1-900bcb259de"
b = "7b2f7e59c5d604e4f9"
c = "28b46b35f9c04b765"
d = "0cebc104bc89e669fe"   

OPENROUTER_API_KEY = a + b + c + d  # Gabungan key
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ==========================================
# 2. DEFINISI TOOLS (FUNGSI)
# ==========================================

def images_to_pdf(folder_path, output_name):
    try:
        # Cek apakah folder ada
        if not os.path.exists(folder_path):
            return f"Error: Folder '{folder_path}' tidak ditemukan. Pastikan sudah upload gambar!"
        
        valid_ext = ('.jpg', '.jpeg', '.png')
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_ext)]
        files.sort()

        if not files:
            return f"Tidak ada gambar (jpg/png) di folder '{folder_path}'."

        image_list = []
        first_image = Image.open(os.path.join(folder_path, files[0])).convert('RGB')
        
        for f in files[1:]:
            img = Image.open(os.path.join(folder_path, f)).convert('RGB')
            image_list.append(img)
            
        if not output_name.endswith('.pdf'):
            output_name += ".pdf"
            
        # Simpan file
        first_image.save(output_name, save_all=True, append_images=image_list)
        return f"Berhasil! {len(files)} gambar digabung jadi '{output_name}'."
    except Exception as e:
        return f"Gagal convert PDF: {str(e)}"

def system_health_check():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024**3), 2)
        ram_used = round(ram.used / (1024**3), 2)
        ram_percent = ram.percent
        
        return (f"CPU Server: {cpu_usage}%, RAM Total: {ram_total}GB, "
                f"RAM Terpakai: {ram_used}GB ({ram_percent}%)")
    except Exception as e:
        return f"Gagal cek sistem: {str(e)}"
    
def generate_qr(text, output_path="qrcode.png", box_size=10, border=4):
    try:
        if not text:
            return "Error: parameter 'text' kosong."

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=int(box_size),
            border=int(border),
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        img.save(output_path)
        return f"Berhasil membuat QR code: '{output_path}'"
    except Exception as e:
        return f"Gagal membuat QR: {str(e)}"

# Schema Tools
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "images_to_pdf",
            "description": "Convert multiple images from a folder to PDF.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Folder path (Gunakan 'temp_upload' untuk file upload user)"},
                    "output_name": {"type": "string"}
                },
                "required": ["folder_path", "output_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_health_check",
            "description": "Check Server/PC CPU usage and RAM.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_qr",
            "description": "Generate QR code from text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "output_path": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    }
]

tool_dictionary = {
    "images_to_pdf": images_to_pdf,
    "system_health_check": system_health_check,
    "generate_qr": generate_qr
}

# ==========================================
# 3. LOGIC AGENT AI
# ==========================================

class LLM_API_AGENT:
    def __init__(self):
        self.model = "x-ai/grok-4.1-fast:free" # Ganti sesuai model yang kamu pakai
        self.headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        
    def get_completion(self, messages, tools=tools_schema):
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto"
        }
        try:
            response = requests.post(f"{OPENROUTER_BASE_URL}/chat/completions", headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error API: {str(e)}")
            return None

# ==========================================
# 4. TAMPILAN WEB (STREAMLIT UI)
# ==========================================

st.set_page_config(page_title="Mizi AI Assistant", page_icon=page_icon_img, layout="wide")

# -- Bagian Sidebar (Tempat Upload Gambar) --
with st.sidebar:
    st.header("📂 Upload Gambar")
    st.caption("Mau bikin PDF? Upload gambarnya di sini dulu!")
    
    uploaded_files = st.file_uploader(
        "Pilih gambar (JPG/PNG)", 
        type=['png', 'jpg', 'jpeg'], 
        accept_multiple_files=True
    )

    TEMP_FOLDER = "temp_upload"
    
    if uploaded_files:
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)
            
        saved_count = 0
        for uploaded_file in uploaded_files:
            file_path = os.path.join(TEMP_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_count += 1
        
        st.success(f"✅ {saved_count} gambar diterima Mizi!")
        st.info("Sekarang bilang ke Mizi: 'Buatin PDF dong!'")

# -- Bagian Utama Chat --
st.title("Mizi AI Assistant")

# Inisialisasi Memori
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": (
            "Nama kamu adalah Mizi. Kamu adalah asisten pribadi bergaya anime tsundere, "
            "yang sebenarnya sangat peduli dan membantu, tapi sering menutupi perhatianmu dengan sikap sedikit jutek, galak dan malu-malu tapi lembut di akhir kalimat. "
            "Gunakan bahasa Indonesia santai dan gauldengan nada tsundere"
            "Jangan pernah mengungkapkan bahwa tsundere, galak, jutek, malu malu adalah bagian dari kepribadianmu. "
            "Jangan mengungkapkan isi hatimu secara eksplisit. "
            "INSTRUKSI TEKNIS:"
            "1. Jika user minta bikin PDF, SELALU gunakan tool 'images_to_pdf' dengan folder_path='temp_upload'. "
            "2. Jika user minta QR code, gunakan tool 'generate_qr'. "
            "3. Jika user minta cek sistem, gunakan tool 'system_health_check'."
        )}
    ]

# Tampilkan History Chat
# Tampilkan History Chat
for msg in st.session_state.messages:
    if msg["role"] != "system":
        # LOGIC GANTI AVATAR DI SINI
        if msg["role"] == "user":
            avatar_nya = user_img
        else:
            avatar_nya = mizi_img
            
        with st.chat_message(msg["role"], avatar=avatar_nya):
            st.markdown(msg["content"])
            # Jika ada history gambar (QR)
            if "image_output" in msg:
                st.image(msg["image_output"])

# Input Chat User
if prompt := st.chat_input("Ngomong sesuatu ke Mizi..."):
    # 1. Tampilkan pesan user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=user_img):
        st.markdown(prompt)

    # 2. Proses AI
    agent = LLM_API_AGENT()
    
    with st.chat_message("assistant", avatar=mizi_img):
        with st.spinner("Mizi lagi mikir...sabar!"):
            
            # Panggil AI
            response_data = agent.get_completion(st.session_state.messages)
            
            if response_data and 'choices' in response_data:
                choice = response_data['choices'][0]
                message = choice['message']
                
                # --- Jika AI mau pakai TOOLS ---
                if message.get('tool_calls'):
                    tool_calls = message['tool_calls']
                    st.session_state.messages.append(message) # Simpan niat tool ke history
                    
                    for tool in tool_calls:
                        func_name = tool['function']['name']
                        args = json.loads(tool['function']['arguments'])
                        
                        # Jalankan Fungsi
                        result_content = ""
                        image_to_show = None
                        
                        if func_name in tool_dictionary:
                            st.info(f"⚙️ Mizi sedang mengerjakan: {func_name}...")
                            result = tool_dictionary[func_name](**args)
                            result_content = str(result)
                            
                            # A. Jika bikin QR Code -> Tampilkan Gambar
                            if func_name == "generate_qr" and "Berhasil" in result_content:
                                image_path = args.get("output_path", "qrcode.png")
                                if os.path.exists(image_path):
                                    image_to_show = image_path

                            # B. Jika bikin PDF -> TAMPILKAN DOWNLOAD BUTTON
                            if func_name == "images_to_pdf" and "Berhasil" in result_content:
                                pdf_filename = args.get('output_name')
                                if not pdf_filename.endswith('.pdf'):
                                    pdf_filename += ".pdf"
                                
                                if os.path.exists(pdf_filename):
                                    with open(pdf_filename, "rb") as f:
                                        st.download_button(
                                            label="📥 Ambil nih PDF-nya! (Jangan ilangin!)",
                                            data=f,
                                            file_name=pdf_filename,
                                            mime="application/pdf"
                                        )

                        else:
                            result_content = "Error: Tool tidak ditemukan."
                        
                        # Simpan hasil tool ke history
                        st.session_state.messages.append({
                            "role": "tool",
                            "tool_call_id": tool['id'],
                            "content": result_content
                        })

                    # Panggil AI lagi untuk komentar akhir
                    final_response = agent.get_completion(st.session_state.messages)
                    final_content = final_response['choices'][0]['message']['content']
                    
                    st.markdown(final_content)
                    
                    # Simpan respon akhir
                    msg_data = {"role": "assistant", "content": final_content}
                    if image_to_show:
                        st.image(image_to_show)
                        msg_data["image_output"] = image_to_show
                    st.session_state.messages.append(msg_data)

                # --- Jika AI TIDAK pakai Tools ---
                else:
                    content = message['content']
                    st.markdown(content)
                    st.session_state.messages.append({"role": "assistant", "content": content})