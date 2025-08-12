# app.py

import streamlit as st
from PIL import Image
import io
import os
from analyze_pcb import analyze_pcb_image

# Check if the data directory exists, if not run setup
if not os.path.exists('data'):
    import setup
    setup.create_directory_structure()
    setup.create_sample_dataset()
    setup.create_dummy_images()
    setup.create_dummy_models()

# --- Streamlit Application Layout ---
st.set_page_config(
    page_title="PCB Analysis Tool",
    page_icon="",
    layout="centered"
)

st.title("PCB Analysis Tool")
st.markdown("Upload a PCB image and select the analysis type.")

st.sidebar.header("Analysis Options")
analysis_option = st.sidebar.radio(
    "Choose analysis type:",
    options=[
        "1. Check Certification & Quality Check",
        "2. Quality Check Required",
        "3. Certification Needed"
    ],
    index=0 # Default to the first option
)

# Convert string option to integer for the function
if "1." in analysis_option:
    selected_option_int = 1
elif "2." in analysis_option:
    selected_option_int = 2
elif "3." in analysis_option:
    selected_option_int = 3
else:
    selected_option_int = 0 # Fallback

uploaded_file = st.file_uploader("Choose a PCB image...", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    # Display the uploaded image
    st.subheader("Uploaded PCB Image:")
    image_bytes = uploaded_file.getvalue()
    st.image(image_bytes, caption=uploaded_file.name, use_column_width=True)

    st.subheader("Analysis Results:")
    with st.spinner("Analyzing PCB image..."):
        # Perform analysis using the analyze_pcb_image function
        results = analyze_pcb_image(image_bytes, selected_option_int)

        if selected_option_int == 1:
            st.write(f"**Quality Check Required:** {results['quality_check_required']}")
            st.write(f"**Certification Needed:** {results['certification_needed']}")
        elif selected_option_int == 2:
            st.write(f"**Quality Check Required:** {results['quality_check_required']}")
        elif selected_option_int == 3:
            st.write(f"**Certification Needed:** {results['certification_needed']}")

        st.markdown(f"---")
        st.write(f"**Details:**")
        st.info(results['details'])

else:
    st.info("Please upload a PCB image to start the analysis.")

st.markdown("---")
st.caption("Developed for Mefron by your PCB analysis assistant.")
