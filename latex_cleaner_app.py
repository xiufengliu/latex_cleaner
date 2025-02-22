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
    page_title="Latex Cleaner",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "http://xiufengliu.github.io",
        'About': "RE App, Developed by Xiufeng Liu"
    }
)

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
    deep_clean = st.checkbox("Deep Clean (keep only title, abstract, and main text)")
    output_format = st.radio("Choose output format:", ["LaTeX", "TXT", "HTML"])

    if st.button("Submit"):
        try:
            # Create temporary directories if they don't exist
            if not os.path.exists(TMP_DIR):
                os.makedirs(TMP_DIR)
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            # Write the input LaTeX to a temporary file
            with open(os.path.join(TMP_DIR, 'input.tex'), 'w') as f:
                f.write(latex_content)

            # Run the initial cleaning with arxiv_latex_cleaner
            args = make_args(input_folder=TMP_DIR, use_external_tikz=None)
            run_arxiv_cleaner(args)

            # Read the cleaned LaTeX and remove excessive newlines
            with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'r') as f:
                cleaned_latex = f.read()
                cleaned_latex = re.sub(r'\n{3,}', '\n', cleaned_latex)

            # Apply deep cleaning if selected
            if deep_clean:
                patterns = [r'\\appendix', r'\\bibliography\{', r'\\begin\{thebibliography\}']
                lines = cleaned_latex.split('\n')
                truncate_line = None
                for i, line in enumerate(lines):
                    if any(re.search(pattern, line) for pattern in patterns):
                        truncate_line = i
                        break
                if truncate_line is not None:
                    cleaned_latex = '\n'.join(lines[:truncate_line]) + '\n\\end{document}'

            # Write the final cleaned LaTeX to the output file
            with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'w') as f:
                f.write(cleaned_latex)

            # Process based on selected output format
            if output_format == "LaTeX":
                st.text_area("Cleaned LaTeX:", value=cleaned_latex, height=400)
                st.download_button(label="Download", data=cleaned_latex, file_name="paper.tex", mime="text/plain")

            elif output_format == "TXT":
                subprocess.run(['pandoc', '-s', os.path.join(OUTPUT_DIR, 'input.tex'), '-o', os.path.join(OUTPUT_DIR, 'output.txt')])
                with open(os.path.join(OUTPUT_DIR, 'output.txt'), 'r') as f:
                    plain_text = f.read()
                st.text_area("Cleaned Text:", value=plain_text, height=400)
                st.download_button(label="Download", data=plain_text, file_name="paper.txt", mime="text/plain")

            elif output_format == "HTML":
                # Modify LaTeX for HTML conversion
                with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'r') as f:
                    tex_content = f.read()
                tex_content = tex_content.replace('\\begin{abstract}', '\\section{Abstract}')
                tex_content = tex_content.replace('\\end{abstract}', '')
                with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'w') as f:
                    f.write(tex_content)
                subprocess.run(['pandoc', '-s', os.path.join(OUTPUT_DIR, 'input.tex'), '-o', os.path.join(OUTPUT_DIR, 'output.html'), '--mathjax'])
                with open(os.path.join(OUTPUT_DIR, 'output.html'), 'r') as f:
                    html_text = f.read()
                st.text_area("Cleaned HTML:", value=html_text, height=400)
                st.download_button(label="Download", data=html_text, file_name="paper.html", mime="text/html")

        except Exception as e:
            st.write("An error occurred:", str(e))

        finally:
            # Clean up temporary directories
            clean_temp_dirs([TMP_DIR, OUTPUT_DIR])