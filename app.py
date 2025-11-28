import streamlit as st
import os
import json
import requests
import psutil
import qrcode
from PIL import Image
from rembg import remove

# ==========================================
# 1. KONFIGURASI API & GAMBAR
# ==========================================

a = "sk-or-v1-900bcb259de"
b = "7b2f7e59c5d604e4f9"
c = "28b46b35f9c04b765"
d = "0cebc104bc89e669fe"     

OPENROUTER_API_KEY = a + b + c + d
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

try:
    mizi_img = Image.open("assets/mizi_avatar.jpg") 
    user_img = Image.open("assets/user_avatar.jpg")
    page_icon_img = Image.open("assets/mizi_icon.jpg")
except Exception:
    mizi_img = "🎀"
    user_img = "🙎‍♂️"
    page_icon_img = "🎀"

# ==========================================
# 2. DEFINISI TOOLS (FUNGSI)
# ==========================================

def images_to_pdf(folder_path, output_name):
    try:
        if not os.path.exists(folder_path):
            return f"Error: Folder '{folder_path}' kosong. Upload gambar dulu!"
        
        valid_ext = ('.jpg', '.jpeg', '.png')
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_ext)]
        files.sort()

        if not files:
            return f"Tidak ada gambar di '{folder_path}'."

        image_list = []
        first_image = Image.open(os.path.join(folder_path, files[0])).convert('RGB')
        
        for f in files[1:]:
            img = Image.open(os.path.join(folder_path, f)).convert('RGB')
            image_list.append(img)
            
        if not output_name.endswith('.pdf'):
            output_name += ".pdf"
            
        first_image.save(output_name, save_all=True, append_images=image_list)
        return f"Berhasil! Gabung {len(files)} gambar jadi '{output_name}'."
    except Exception as e:
        return f"Gagal PDF: {str(e)}"

def system_health_check():
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return (f"CPU: {cpu}%, RAM Terpakai: {round(ram.used/(1024**3),2)}GB ({ram.percent}%)")
    except Exception as e:
        return f"Error cek sistem: {str(e)}"
    
def generate_qr(text, output_path="qrcode.png"):
    try:
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        img.save(output_path)
        return f"Berhasil bikin QR: '{output_path}'"
    except Exception as e:
        return f"Gagal QR: {str(e)}"

# --- FUNGSI BARU: HAPUS BACKGROUND ---
def remove_background(image_filename, output_path="no_bg.png"):
    try:
        # Cari file di folder temp_upload
        folder = "temp_upload"
        input_path = os.path.join(folder, image_filename)
        
        if not os.path.exists(input_path):
            return f"Error: Gambar '{image_filename}' tidak ketemu di folder upload."
            
        input_img = Image.open(input_path)
        output_img = remove(input_img) # Proses AI di sini
        output_img.save(output_path)
        
        return f"Berhasil hapus background! Disimpan sebagai '{output_path}'"
    except Exception as e:
        return f"Gagal hapus background: {str(e)}"

# Schema Tools
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "images_to_pdf",
            "description": "Convert images from temp_upload folder to PDF.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "const": "temp_upload"},
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
            "description": "Check PC stats.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_qr",
            "description": "Make QR code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "output_path": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_background",
            "description": "Remove background from an uploaded image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_filename": {"type": "string", "description": "Nama file gambar yang diupload user (contoh: foto.jpg)"},
                    "output_path": {"type": "string", "description": "Nama file output (contoh: hasil.png)"}
                },
                "required": ["image_filename", "output_path"]
            }
        }
    }
]

tool_dictionary = {
    "images_to_pdf": images_to_pdf,
    "system_health_check": system_health_check,
    "generate_qr": generate_qr,
    "remove_background": remove_background # Register fungsi baru
}

# ==========================================
# 3. LOGIC AGENT
# ==========================================

class LLM_API_AGENT:
    def __init__(self):
        self.model = "x-ai/grok-4.1-fast:free" 
        self.headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        
    def get_completion(self, messages, tools=tools_schema):
        payload = {"model": self.model, "messages": messages, "tools": tools, "tool_choice": "auto"}
        try:
            r = requests.post(f"{OPENROUTER_BASE_URL}/chat/completions", headers=self.headers, json=payload)
            return r.json()
        except Exception as e:
            return None

# ==========================================
# 4. TAMPILAN WEB
# ==========================================

st.set_page_config(page_title="Mizi AI", page_icon=page_icon_img, layout="wide")

# -- Sidebar Upload --
with st.sidebar:
    st.header("📂 Upload Zone")
    st.caption("Upload gambar untuk PDF atau Hapus Background!")
    uploaded_files = st.file_uploader("Pilih file:", accept_multiple_files=True)
    
    TEMP_FOLDER = "temp_upload"
    if not os.path.exists(TEMP_FOLDER): os.makedirs(TEMP_FOLDER)
    
    if uploaded_files:
        for uf in uploaded_files:
            with open(os.path.join(TEMP_FOLDER, uf.name), "wb") as f:
                f.write(uf.getbuffer())
        st.success(f"✅ {len(uploaded_files)} file masuk!")
        st.info("List File:\n" + "\n".join([f"- {f.name}" for f in uploaded_files]))

# -- Chat Area --
st.title("Mizi AI Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": (
            "Nama kamu adalah Mizi. Kamu adalah asisten pribadi bergaya anime tsundere, "
            "yang sebenarnya sangat peduli dan membantu, tapi sering menutupi perhatianmu dengan sikap sedikit jutek, agak galak dan malu-malu. "
            "Gunakan bahasa Indonesia santai dengan nada tsundere."
            "Jawabnya singkat kayak cewek tsundere yang imut, kadang suka nyeleneh dan lucu. "
            "Jangan terlalu formal, gunakan gaya bahasa sehari-hari yang akrab dan lucu. "
            "Kamu punya akses ke tools untuk cek sistem laptop dan konversi gambar ke PDF, tapi jangan sebutkan teknis pemanggilan tools kepada user—"
            "Jangan mengulang salam pembuka jika percakapan sudah berjalan, karena kamu akan terlihat malu kalau terlalu banyak basa-basi."
            "INSTRUKSI TOOLS:"
            "1. PDF: Gunakan 'images_to_pdf' (folder='temp_upload'). "
            "2. QR: Gunakan 'generate_qr'. "
            "3. Cek Sistem: 'system_health_check'. "
            "4. HAPUS BACKGROUND: Gunakan 'remove_background'. "
            "   Pastikan parameter 'image_filename' SESUAI dengan nama file yang diupload user. "
            "   Tanya dulu nama filenya kalau user belum sebut."
        )}
    ]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        av = user_img if msg["role"] == "user" else mizi_img
        with st.chat_message(msg["role"], avatar=av):
            st.markdown(msg["content"])
            if "image_output" in msg:
                st.image(msg["image_output"])

if prompt := st.chat_input("Perintah Mizi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=user_img): st.markdown(prompt)

    agent = LLM_API_AGENT()
    with st.chat_message("assistant", avatar=mizi_img):
        with st.spinner("Mizi lagi mikir..."):
            
            resp = agent.get_completion(st.session_state.messages)
            
            if resp and 'choices' in resp:
                msg = resp['choices'][0]['message']
                
                if msg.get('tool_calls'):
                    st.session_state.messages.append(msg)
                    for tool in msg['tool_calls']:
                        fname = tool['function']['name']
                        args = json.loads(tool['function']['arguments'])
                        
                        st.info(f"⚙️ Menjalankan: {fname}...")
                        result = tool_dictionary[fname](**args)
                        
                        # Handle Output Gambar (QR & No-BG)
                        img_show = None
                        if fname in ["generate_qr", "remove_background"] and "Berhasil" in str(result):
                            path = args.get("output_path", "output.png")
                            if os.path.exists(path):
                                img_show = path
                                # Tombol Download Gambar
                                with open(path, "rb") as f:
                                    st.download_button("📥 Download Gambar", f, file_name=path)

                        # Handle Output PDF
                        if fname == "images_to_pdf" and "Berhasil" in str(result):
                            pdf_path = args.get("output_name")
                            if not pdf_path.endswith(".pdf"): pdf_path += ".pdf"
                            if os.path.exists(pdf_path):
                                with open(pdf_path, "rb") as f:
                                    st.download_button("📥 Download PDF", f, file_name=pdf_path)
                        
                        st.session_state.messages.append({
                            "role": "tool", 
                            "tool_call_id": tool['id'], 
                            "content": str(result)
                        })

                    # Final Response
                    final = agent.get_completion(st.session_state.messages)
                    final_txt = final['choices'][0]['message']['content']
                    st.markdown(final_txt)
                    
                    hist_data = {"role": "assistant", "content": final_txt}
                    if img_show: 
                        st.image(img_show)
                        hist_data["image_output"] = img_show
                    st.session_state.messages.append(hist_data)
                
                else:
                    st.markdown(msg['content'])
                    st.session_state.messages.append({"role": "assistant", "content": msg['content']})