import streamlit as st
import os
import shutil
import subprocess
import re
from arxiv_latex_cleaner.arxiv_latex_cleaner import run_arxiv_cleaner

# Helper function to create arguments for arxiv_latex_cleaner
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

# Clean up temporary directories
def clean_temp_dirs(directories):
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)

# Extract preamble and main content for deep clean
def deep_clean_latex(latex_code):
    """
    Extracts the preamble and main content from cleaned LaTeX code, excluding appendices and bibliographies.

    Args:
        latex_code (str): The cleaned LaTeX code after running arxiv_latex_cleaner.

    Returns:
        tuple: (preamble, main_content)
            - preamble: The extracted preamble (before \begin{document}).
            - main_content: The extracted main content (after \begin{document}, up to appendices/bibliography).
    """
    # Find \begin{document}
    begin_doc_match = re.search(r'\\begin\{document\}', latex_code)
    if not begin_doc_match:
        return "", latex_code  # No preamble, treat all as content

    preamble = latex_code[:begin_doc_match.start()].strip()
    content_start = begin_doc_match.end()

    # Find \end{document}
    end_doc_match = re.search(r'\\end\{document\}', latex_code[content_start:])
    if end_doc_match:
        content_end = content_start + end_doc_match.start()
    else:
        content_end = len(latex_code)

    # Find the earliest occurrence of \appendix, \bibliography, or \begin{thebibliography}
    patterns = [r'\\appendix', r'\\bibliography\{', r'\\begin\{thebibliography\}']
    min_pos = content_end
    for pattern in patterns:
        match = re.search(pattern, latex_code[content_start:content_end])
        if match:
            min_pos = min(min_pos, content_start + match.start())

    main_content = latex_code[content_start:min_pos].strip()

    return preamble, main_content

# Streamlit app configuration
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

    # Input LaTeX code
    latex_content = st.text_area("Paste your LaTeX code here:", height=400)

    # Deep clean option
    deep_clean = st.checkbox("Deep Clean (extract only main content)")

    # Output format selection
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

            if deep_clean:
                preamble, main_content = deep_clean_latex(cleaned_latex)
            else:
                main_content = cleaned_latex  # Use the full cleaned document

            if output_format == "LaTeX":
                # Display and provide download for main content (no preamble)
                st.text_area("Cleaned LaTeX (Main Content):", value=main_content, height=400)
                st.download_button(
                    label="Download",
                    data=main_content,
                    file_name="paper_main_content.tex",
                    mime="text/plain"
                )
            else:
                # For TXT and HTML, reconstruct a full document with preamble if deep_clean is True
                if deep_clean:
                    latex_for_conversion = preamble + '\\begin{document}\n' + main_content + '\n\\end{document}'
                else:
                    latex_for_conversion = cleaned_latex

                # Write the LaTeX for conversion to 'input.tex'
                with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'w') as f:
                    f.write(latex_for_conversion)

                if output_format == "TXT":
                    subprocess.run([
                        'pandoc',
                        '-s',
                        os.path.join(OUTPUT_DIR, 'input.tex'),
                        '-o',
                        os.path.join(OUTPUT_DIR, 'output.txt')
                    ])
                    with open(os.path.join(OUTPUT_DIR, 'output.txt'), 'r') as f:
                        plain_text = f.read()
                    st.text_area("Cleaned Text:", value=plain_text, height=400)
                    st.download_button(
                        label="Download",
                        data=plain_text,
                        file_name="paper.txt",
                        mime="text/plain"
                    )

                elif output_format == "HTML":
                    # Modify LaTeX for HTML conversion (e.g., replace abstract environment)
                    with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'r') as f:
                        tex_content = f.read()
                    tex_content = tex_content.replace('\\begin{abstract}', '\\section{Abstract}')
                    tex_content = tex_content.replace('\\end{abstract}', '')
                    with open(os.path.join(OUTPUT_DIR, 'input.tex'), 'w') as f:
                        f.write(tex_content)
                    # Run Pandoc conversion
                    subprocess.run([
                        'pandoc',
                        '-s',
                        os.path.join(OUTPUT_DIR, 'input.tex'),
                        '-o',
                        os.path.join(OUTPUT_DIR, 'output.html'),
                        '--mathjax'
                    ])
                    with open(os.path.join(OUTPUT_DIR, 'output.html'), 'r') as f:
                        html_text = f.read()
                    st.text_area("Cleaned HTML:", value=html_text, height=400)
                    st.download_button(
                        label="Download",
                        data=html_text,
                        file_name="paper.html",
                        mime="text/html"
                    )

        except Exception as e:
            st.write("An error occurred:", str(e))

        finally:
            # Clean up temporary directories
            clean_temp_dirs([TMP_DIR, OUTPUT_DIR])