# i_spy_streamlit_app.py

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import random
import io
import math
import os

# ─── 1) Page configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="I Spy Worksheet",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ─── 2) App header ──────────────────────────────────────────────────────────────
st.title("🕵️ I Spy Worksheet Generator")
st.markdown(
    """
    1. Upload up to 20 images (PNG/JPG) as your icons.  
    2. Choose how many total icons you want on the worksheet.  
    3. Click **Generate Worksheet** to create your puzzle and download it!
    """
)

# ─── 3) File uploader ──────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    label="1. Upload your icons",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"You’ve uploaded {len(uploaded_files)} file(s).")
    cols = st.columns(5)
    for idx, img_file in enumerate(uploaded_files):
        img = Image.open(img_file)
        cols[idx % 5].image(img, use_container_width=True)

    # Load original icons
    original_icons = [Image.open(f).convert("RGBA") for f in uploaded_files]

    # ─── 4) Total count input ────────────────────────────────────────────────────
    total_count = st.number_input(
        label="2. Total number of icons on the worksheet",
        min_value=1, max_value=200, value=50, step=5
    )

    # ─── 5) Generate Worksheet ───────────────────────────────────────────────────
    if st.button("Generate Worksheet"):
        # A4 canvas at 300 DPI: 2480x3508 px
        WIDTH, HEIGHT = 2480, 3508
        canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
        draw = ImageDraw.Draw(canvas)

        # --- Title as image (scaled) ---
        title_height = 0
        title_path = os.path.join(os.getcwd(), "title.png")
        if os.path.exists(title_path):
            title_img = Image.open(title_path).convert("RGBA")
            max_w = int(WIDTH * 0.576)
            w, h = title_img.size
            scale = max_w / w
            new_w, new_h = int(w * scale), int(h * scale)
            title_resized = title_img.resize((new_w, new_h), Image.LANCZOS)
            x = (WIDTH - new_w) // 2
            y = 20
            canvas.paste(title_resized, (x, y), title_resized)
            title_height = new_h + y
        else:
            title_height = 80

        # --- Draw placement border (20% shrink) ---
        margin = 100
        top_offset = title_height + 10
        bottom_offset = HEIGHT - 1000  # moved up to fit legend
        left_offset = margin
        right_offset = WIDTH - margin
        area_w = right_offset - left_offset
        area_h = bottom_offset - top_offset
        shrink_w = area_w * 0.8
        shrink_h = area_h * 0.8
        left = int(left_offset + (area_w - shrink_w) / 2)
        top = int(top_offset + (area_h - shrink_h) / 2)
        right = int(left + shrink_w)
        bottom = int(top + shrink_h)
        draw.rectangle([left, top, right, bottom], outline="black", width=5)

        # --- Progress bar ---
        progress_bar = st.progress(0)
        status_text = st.empty()

        # --- Place icons without overlap ---
        placed = []
        MIN_ICON, MAX_ICON = 150, 350
        count = 0
        while count < total_count:
            icon = random.choice(original_icons)
            size = random.randint(MIN_ICON, MAX_ICON)
            icon_s = icon.resize((size, size), Image.LANCZOS)
            icon_r = icon_s.rotate(random.uniform(0, 360), expand=True)
            iw, ih = icon_r.size
            for _ in range(50):
                x = random.randint(left, right - iw)
                y = random.randint(top, bottom - ih)
                box = (x, y, x + iw, y + ih)
                overlap = any(
                    box[0] < bx[2] and box[2] > bx[0] and box[1] < bx[3] and box[3] > bx[1]
                    for bx in placed
                )
                if not overlap:
                    placed.append(box)
                    canvas.paste(icon_r, (x, y), icon_r)
                    count += 1
                    progress_bar.progress(count / total_count)
                    status_text.text(f"Placing icons: {count}/{total_count}")
                    break
        status_text.text("Placement complete!")

        # --- Legend header image ---
        legend_image_height = 0
        legend_img_path = os.path.join(os.getcwd(), "Count and Write.png")
        if os.path.exists(legend_img_path):
            try:
                legend_hdr = Image.open(legend_img_path).convert("RGBA")
                max_w2 = int(WIDTH * 0.8)
                w2, h2 = legend_hdr.size
                scale2 = max_w2 / w2
                new_w2, new_h2 = int(w2 * scale2), int(h2 * scale2)
                legend_hdr = legend_hdr.resize((new_w2, new_h2), Image.LANCZOS)
                x2 = (WIDTH - new_w2) // 2
                y2 = bottom + 20
                canvas.paste(legend_hdr, (x2, y2), legend_hdr)
                legend_image_height = new_h2 + 20
            except Exception:
                legend_image_height = 0

        # --- Legend icons & boxes (no title) ---
        ICON = 180  # legend icon size
        pad = 45   # padding between legend icons
        per_row = min(len(original_icons), 5)
        total_w = per_row * ICON + (per_row - 1) * pad
        start_x = (WIDTH - total_w) / 2
        # first row, positioned below legend image
        y1 = bottom + legend_image_height + 20
        yb1 = y1 + ICON + 10
        # second row
        y2 = yb1 + ICON + 40
        yb2 = y2 + ICON + 10
        for i, icon in enumerate(original_icons):
            col = i % per_row
            row = i // per_row
            x0 = int(start_x + col * (ICON + pad))
            img_small = icon.resize((ICON, ICON), Image.LANCZOS)
            if row == 0:
                canvas.paste(img_small, (x0, int(y1)), img_small)
                draw.rectangle([x0, int(yb1), x0 + ICON, int(yb1) + ICON], outline="black", width=3)
            else:
                canvas.paste(img_small, (x0, int(y2)), img_small)
                draw.rectangle([x0, int(yb2), x0 + ICON, int(yb2) + ICON], outline="black", width=3)

                                        # --- Display & download ---        # --- Watermark image ---
        wm_path = os.path.join(os.getcwd(), "watermark.png")
        if os.path.exists(wm_path):
            wm_img = Image.open(wm_path).convert("RGBA")
            # scale watermark to 10% of page width
            max_wm = int(WIDTH * 0.1)
            w_wm, h_wm = wm_img.size
            wm_scale = max_wm / w_wm
            wm_img = wm_img.resize((int(w_wm * wm_scale), int(h_wm * wm_scale)), Image.LANCZOS)
            wm_w, wm_h = wm_img.size
            # position bottom-right
            x_wm = WIDTH - wm_w - 40
            y_wm = HEIGHT - wm_h - 40
            canvas.paste(wm_img, (x_wm, y_wm), wm_img)
        
        buf = io.BytesIO()
        canvas.save(buf, format="PNG", dpi=(300,300))
        buf.seek(0)
        st.image(canvas, use_container_width=True)
        st.download_button(
            label="📥 Download Worksheet as PNG (A4, 300dpi)",
            data=buf,
            file_name="i_spy_worksheet_a4.png",
            mime="image/png"
        )
