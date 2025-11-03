import streamlit as st
import qrcode
import os
import math
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile
import tempfile

# --------------------------
# QR Code Generator Function
# --------------------------
def generate_qr_codes_2(text_list, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_paths = []
    for idx, text in enumerate(text_list):
        qr = qrcode.make(text, border=2, box_size=15).convert("RGBA")
        qr_width, qr_height = qr.size

        try:
            font = ImageFont.truetype("montserrat.ttf", 40)
        except Exception:
            font = ImageFont.load_default()

        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width, text_height = draw.textsize(text, font=font)

        padding = 20
        total_height = qr_height + text_height + padding
        final_img = Image.new("RGB", (qr_width, total_height), "white")
        draw = ImageDraw.Draw(final_img)

        text_x = max((qr_width - text_width) // 2, 0)
        text_y = 10
        draw.text((text_x, text_y), text, fill="black", font=font)

        qr_y = text_y + text_height + 5
        box = (0, qr_y, qr_width, qr_y + qr_height)
        alpha = qr.split()[3] if qr.mode == "RGBA" else None
        final_img.paste(qr.convert("RGB"), box, mask=alpha)

        safe_text = "".join(c if c.isalnum() else "_" for c in text).strip("_") or f"qr_{idx}"
        file_path = os.path.join(output_dir, f"{safe_text}.png")
        final_img.save(file_path)
        image_paths.append(file_path)

    return image_paths


# --------------------------
# A4 Sheet Arrangement Function
# --------------------------
def arrange_qr_codes_on_a4(input_dir, output_dir="qr_sheets", margin=10, padding=10):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    A4_WIDTH, A4_HEIGHT = 2480, 3508  # A4 at 300 DPI

    image_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not image_files:
        return []

    sample_img = Image.open(image_files[0])
    img_w, img_h = sample_img.size
    sample_img.close()

    cols = max(1, (A4_WIDTH - 2 * margin + padding) // (img_w + padding))
    rows = max(1, (A4_HEIGHT - 2 * margin + padding) // (img_h + padding))
    per_page = cols * rows

    pages = []
    total_pages = math.ceil(len(image_files) / per_page)

    for page_num in range(total_pages):
        page = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        start_idx = page_num * per_page
        end_idx = start_idx + per_page
        subset = image_files[start_idx:end_idx]

        for i, path in enumerate(subset):
            img = Image.open(path)
            col = i % cols
            row = i // cols
            x = margin + col * (img_w + padding)
            y = margin + row * (img_h + padding)
            page.paste(img, (x, y))
            img.close()

        output_path = os.path.join(output_dir, f"qr_sheet_{page_num + 1}.png")
        page.save(output_path, "PNG")
        pages.append(output_path)

    return pages


# --------------------------
# STREAMLIT UI
# --------------------------
st.set_page_config(page_title="QR Generator + A4 Sheets", page_icon="🧾")
st.title("🧾 Bulk Matric QR Generator + Printable A4 Sheets")

matric_prefix = "DU"
prefixInput = st.text_input("Enter matric prefix", value=matric_prefix).upper()
matricNumText = st.text_input("Enter custom matric number(s), separated by commas (LEAVE EMPTY IF NOT NEEDED) e.g.1300,402,2000:", value="")
start_num = st.number_input("Starting matric number (e.g., 1 for DU0001):", min_value=1, value=1)
count = st.number_input("Number of matric numbers to generate:", min_value=1, value=5)



# Temp directories for session
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if "qr_files" not in st.session_state:
    st.session_state.qr_files = []
if "a4_sheets" not in st.session_state:
    st.session_state.a4_sheets = []

# --- Generate QR Codes ---
if st.button("Generate QR Codes"):
    if matricNumText.strip():
        matricNumList = [num.strip() for num in matricNumText.split(",") if num.strip()]
        matric_numbers = [f"{prefixInput}{int(num):04d}" for num in matricNumList]
    else:
        matric_numbers = [f"{prefixInput}{num:04d}" for num in range(start_num, start_num + count)]

    st.session_state.qr_files = generate_qr_codes_2(matric_numbers, st.session_state.temp_dir)
    st.success(f"Generated {len(st.session_state.qr_files)} QR codes successfully!")

# --- Display Generated QRs ---
if st.session_state.qr_files:
    st.subheader("Generated QR Codes")
    cols = st.columns(3)
    for i, path in enumerate(st.session_state.qr_files):
        with cols[i % 3]:
            st.image(path, caption=os.path.basename(path), use_container_width=True)

    # ZIP download for QR codes
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zipf:
        for path in st.session_state.qr_files:
            zipf.write(path, os.path.basename(path))
    st.download_button("📦 Download QR Codes (ZIP)", zip_buf.getvalue(),
                       file_name="qr_codes.zip", mime="application/zip")

# --- Generate A4 Sheets (NO PAGE CLEAR) ---
if st.session_state.qr_files:
    st.subheader("🖨️ Arrange on A4 Sheets")
    if st.button("Generate A4 Sheets"):
        output_dir = os.path.join(st.session_state.temp_dir, "a4_sheets")
        st.session_state.a4_sheets = arrange_qr_codes_on_a4(st.session_state.temp_dir, output_dir)
        if st.session_state.a4_sheets:
            st.success(f"✅ Created {len(st.session_state.a4_sheets)} A4 sheet(s)!")

# --- Display & Download A4 Sheets ---
if st.session_state.a4_sheets:
    for i, path in enumerate(st.session_state.a4_sheets, start=1):
        st.image(path, caption=f"A4 Sheet {i}", use_container_width=True)

    a4_zip = BytesIO()
    with zipfile.ZipFile(a4_zip, "w") as zipf:
        for path in st.session_state.a4_sheets:
            zipf.write(path, os.path.basename(path))
    st.download_button("📄 Download A4 Sheets (ZIP)", a4_zip.getvalue(),
                       file_name="qr_a4_sheets.zip", mime="application/zip")
