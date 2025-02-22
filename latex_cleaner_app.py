import streamlit as st
import os
import shutil
import subprocess
import re
import time
from arxiv_latex_cleaner.arxiv_latex_cleaner import run_arxiv_cleaner

def make_args(input_folder, resize_images=False, im_size=500, compress_pdf=False, pdf_im_resolution=500, images_allowlist=None, commands_to_delete=None, use_external_tikz=None, keep_bib=False):
    if images_allowlist is None:
        images_allowlist = {}
    if commands_to_delete is None:
        commands_to_delete = []
    args = {
        'input_folder': input_folder,
        'resize_images': resize_images,
        'im_size': im_size,
        'compress_pdf': compress_pdf,
        'pdf_im_resolution': pdf_im_resolution,
        'images_allowlist': images_allowlist,
        'commands_to_delete': commands_to_delete,
        'use_external_tikz': use_external_tikz,
        'keep_bib': keep_bib
    }
    return args

def clean_temp_dirs(directories):
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)

def show_progress_bar(duration):
    with st.spinner('Converting...'):
        progress_bar = st.progress(0)
        for i in range(1, 101):
            progress_bar.progress(i)
            time.sleep(duration / 100.0)

st.set_page_config(
    page_title="Latex cleaner",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "http://xiufengliu.github.io",
        'About': "RE App, Developed by Xiufeng Liu"
    }
)

if 'cleaned_latex' not in st.session_state:
    st.session_state.cleaned_latex = ''

st.title("LaTeX Cleaner")
st.write("""
    Simplify and clean your LaTeX documents.
    Choose the service below to get started.
""")
st.markdown("""
    Looking to clean your BibTeX references?
    Try the [BibTeX Cleaner](https://flamingtempura.github.io/bibtex-tidy/).
""")
st.write("---")

with st.expander("LaTeX Cleaner", expanded=True):
    BASE_DIR = "/opt/app/latex_cleaner"
    TMP_DIR = os.path.join(BASE_DIR, 'tmp_latex_project')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'tmp_latex_project_arXiv')

    latex_content = st.text_area("Paste your LaTeX code here:", height=400)
    action = st.radio("Choose an action:", ["Clean LaTeX", "Convert to TXT", "Convert to HTML"])

    if st.button("Submit"):
        try:
            if not os.path.exists(TMP_DIR):
                os.makedirs(TMP_DIR)
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            with open(os.path.join(TMP_DIR, 'input.tex'), 'w') as f:
                f.write(latex_content)

            args = make_args(input_folder=TMP_DIR, use_external_tikz=None)
            run_arxiv_cleaner(args)

            with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'r') as f:
                cleaned_latex = f.read()
                cleaned_latex = re.sub(r'\n{3,}', '\n', cleaned_latex)
                st.session_state.cleaned_latex = cleaned_latex
            


            if action == "Convert to TXT":
                subprocess.run(['pandoc', '-s', os.path.join(OUTPUT_DIR, 'input.tex'), '-o', os.path.join(OUTPUT_DIR, 'output.txt')])
                with open(os.path.join(OUTPUT_DIR, 'output.txt'), 'r') as f:
                    plain_text = f.read()
                st.text_area("Cleaned Text:", value=plain_text, height=400)
                
                st.download_button(label="Download", data=plain_text, file_name="paper.txt", mime="text/plain")

            elif action == "Convert to HTML":
                    # Step 1: Read the LaTeX file
                with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'r') as f:
                    tex_content = f.read()
                # Step 2: Replace the abstract environment with the section command
                tex_content = tex_content.replace('\\begin{abstract}', '\\section{Abstract}')
                tex_content = tex_content.replace('\\end{abstract}', '')               
                # Write the modified content back to the LaTeX file
                with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'w') as f:
                    f.write(tex_content)
                # Step 3: Run Pandoc conversion
                subprocess.run(['pandoc', '-s', os.path.join(OUTPUT_DIR, 'input.tex'), '-o', os.path.join(OUTPUT_DIR, 'output.html'), '--mathjax'])         
                with open(os.path.join(OUTPUT_DIR, 'output.html'), 'r') as f:
                    html_text = f.read()
                st.text_area("Cleaned HTML:", value=html_text, height=400)
                st.download_button(label="Download", data=html_text, file_name="paper.html", mime="text/html")

            else:
                st.text_area("Cleaned LaTeX:", value=st.session_state.cleaned_latex, height=400)
                st.download_button(label="Download", data=st.session_state.cleaned_latex, file_name="paper.tex", mime="text/plain")

        except Exception as e:
            st.write("An error occurred:", str(e))

        finally:
            clean_temp_dirs([TMP_DIR, OUTPUT_DIR])

