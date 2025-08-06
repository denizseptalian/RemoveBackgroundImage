import streamlit as st
from rembg import remove
from PIL import Image
import numpy as np
from io import BytesIO
import base64
import os
import traceback
import time

# Coba impor onnxruntime, fallback ke onnxruntime-web jika gagal
try:
    import onnxruntime as ort
except ImportError:
    import onnxruntime_web as ort

# Konfigurasi halaman
st.set_page_config(layout="wide", page_title="Image Background Remover")

st.write("## Remove background from your image")
st.write(
    ":dog: Upload an image to remove the background instantly. Download the result from the sidebar. "
    "Powered by [rembg](https://github.com/danielgatis/rembg) :grin:"
)
st.sidebar.write("## Upload and Download :gear:")

# Konfigurasi batas file
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 2000  # Max dimensi pixel

# Fungsi konversi gambar ke byte untuk download
def convert_image(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    return byte_im

# Fungsi resize image dengan mempertahankan rasio
def resize_image(image, max_size):
    width, height = image.size
    if width <= max_size and height <= max_size:
        return image
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    return image.resize((new_width, new_height), Image.LANCZOS)

# Fungsi pemrosesan gambar
def process_image(image_bytes):
    try:
        image = Image.open(BytesIO(image_bytes))
        resized = resize_image(image, MAX_IMAGE_SIZE)
        fixed = remove(resized)  # rembg otomatis gunakan runtime yang tersedia
        return image, fixed
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None, None

# Fungsi utama untuk memproses dan menampilkan gambar
def fix_image(upload):
    try:
        start_time = time.time()
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()

        status_text.text("Loading image...")
        progress_bar.progress(10)

        # Baca gambar
        if isinstance(upload, str):
            if not os.path.exists(upload):
                st.error(f"Default image not found: {upload}")
                return
            with open(upload, "rb") as f:
                image_bytes = f.read()
        else:
            image_bytes = upload.getvalue()

        status_text.text("Processing image...")
        progress_bar.progress(40)

        image, fixed = process_image(image_bytes)
        if image is None or fixed is None:
            return

        progress_bar.progress(80)
        status_text.text("Displaying results...")

        col1, col2 = st.columns(2)
        col1.write("### Original Image :camera:")
        col1.image(image)

        col2.write("### Background Removed :wrench:")
        col2.image(fixed)

        st.sidebar.download_button(
            "Download Result",
            convert_image(fixed),
            "background_removed.png",
            "image/png"
        )

        progress_bar.progress(100)
        status_text.text(f"Completed in {time.time() - start_time:.2f} seconds")

    except Exception:
        st.error("An unexpected error occurred.")
        st.sidebar.error("Failed to process image")
        print(traceback.format_exc())

# UI Upload
my_upload = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

with st.sidebar.expander("ℹ️ Image Guidelines"):
    st.write("""
    - Max size: 10MB
    - Large images auto-resized to 2000px
    - Formats: PNG, JPG, JPEG
    """)

# Jalankan
if my_upload is not None:
    if my_upload.size > MAX_FILE_SIZE:
        st.error(f"File too large! Please upload under {MAX_FILE_SIZE/1024/1024:.1f}MB.")
    else:
        fix_image(upload=my_upload)
else:
    default_images = ["./zebra.jpg", "./wallaby.png"]
    for img_path in default_images:
        if os.path.exists(img_path):
            fix_image(img_path)
            break
    else:
        st.info("Please upload an image to start!")
