import streamlit as st
import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile

# --------------------------
# QR Code Generator Function
# --------------------------
def generate_qr_codes_2(text_list):
    image_buffers = []

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

        buf = BytesIO()
        final_img.save(buf, format="PNG")
        image_buffers.append((text, buf.getvalue()))

    return image_buffers

# --------------------------
# Streamlit UI
# --------------------------
st.set_page_config(page_title="QR Code Generator", page_icon="🧾")
st.title("🧾 Bulk Matric Number QR Code Generator")

st.markdown("Generate multiple QR codes labeled with matric numbers like **DU0001**, **DU0002**, etc.")


start_num = st.number_input("Enter starting matric number (e.g., 1 for DU0001):", min_value=1, value=1)
count = st.number_input("Enter number of matric numbers to generate:", min_value=1, value=5)

matricNumText = st.text_input("Enter matric number(s) separated by commas ", value="1500,1200,608")
matricNumList = [num.strip() for num in matricNumText.split(",") if num.strip()]



if st.button("Generate QR Codes"):
    if matricNumList != []:
        matric_numbers = [f"DU{int(num):04d}" for num in matricNumList]
    else:
        matric_numbers = [f"DU{num:04d}" for num in range(start_num, start_num + count)]
    st.write("Generated Matric Numbers:", matric_numbers)

    image_files = generate_qr_codes_2(matric_numbers)

    # Display images
    st.subheader("Generated QR Codes")
    cols = st.columns(3)
    for i, (name, img_data) in enumerate(image_files):
        with cols[i % 3]:
            st.image(img_data, caption=name, use_container_width=True)    

    # Create ZIP for download
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zipf:
        for name, img_data in image_files:
            safe_name = "".join(c if c.isalnum() else "_" for c in name).strip("_") or f"qr_{name}"
            zipf.writestr(f"{safe_name}.png", img_data)

    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buf.getvalue(),
        file_name="qr_codes.zip",
        mime="application/zip",
    )

import math

