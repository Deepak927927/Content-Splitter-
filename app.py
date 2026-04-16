import streamlit as st
import re
import zipfile
import io

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(page_title="Smart Content Processor", layout="centered")
st.title("📚 Smart Content Processing Platform")

st.markdown("Upload files to generate structured worksheets with answers & solutions.")

# ---------------- FILE UPLOAD ---------------- #

file1 = st.file_uploader("📘 Upload SYNOPSIS + WORKSHEET file", type=["md"])
file2 = st.file_uploader("🧾 Upload SOLUTIONS file", type=["md"])

# ---------------- CLEAN FUNCTION ---------------- #

def clean_content(content):
    content = re.sub(r'<\s*header\s*>.*?<\s*/\s*header\s*>', '', content, flags=re.DOTALL)
    content = re.sub(r'<\s*footer\s*>.*?<\s*/\s*footer\s*>', '', content, flags=re.DOTALL)
    content = re.sub(r'<\s*page_number\s*>.*?<\s*/\s*page_number\s*>', '', content, flags=re.DOTALL)
    content = re.sub(r'<\s*img\s*>.*?<\s*/\s*img\s*>', '', content, flags=re.DOTALL)

    content = re.sub(r'Narayana Group of Schools', '', content)
    content = re.sub(r'VII.*?e-Techno_Text Book', '', content)

    content = re.sub(r'\r\n', '\n', content)
    content = re.sub(r'\n\s*\n+', '\n\n', content)

    return content

# ---------------- REMOVE CUQ ---------------- #

def remove_cuq_sections(content):
    content = re.sub(
        r'\*\*CUQ:?[\s\S]*?(?=\n[A-Z][A-Z ]+\n|JEE|WORKSHEET|\Z)',
        '',
        content,
        flags=re.DOTALL
    )
    return content

# ---------------- ZIP FUNCTION ---------------- #

def create_zip(files_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for filename, content in files_dict.items():
            zf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer

# ---------------- SPLIT SYNOPSIS ---------------- #

def split_synopsis(content):
    pattern = r'(# SYNOPSIS \d+)'
    parts = re.split(pattern, content)

    synopsis_dict = {}
    worksheet_dict = {}

    for i in range(1, len(parts), 2):
        title = parts[i]
        body = parts[i+1]

        num = re.search(r'\d+', title).group()

        split_ws = re.split(r'(WORKSHEET\s*-?\s*\d+)', body, maxsplit=1)

        if len(split_ws) > 1:
            synopsis = split_ws[0]
            worksheet = split_ws[1] + split_ws[2]
        else:
            synopsis = body
            worksheet = ""

        # Remove examples
        synopsis = re.sub(
            r'\*\*Example:.*?(?=\n\*\*|\n[A-Z#]|WORKSHEET|\Z)',
            '',
            synopsis,
            flags=re.DOTALL
        )

        synopsis_dict[f"synopsis_{num}.md"] = title + synopsis

        if worksheet:
            worksheet_dict[f"worksheet_{num}.md"] = worksheet

    return synopsis_dict, worksheet_dict

# ---------------- SPLIT SOLUTIONS ---------------- #

def split_solutions(content):
    pattern = r'(WORKSHEET\s*-?\s*\d+|Worksheet\s*-?\s*\d+|WS\s*-?\s*\d+)'
    parts = re.split(pattern, content)

    solution_dict = {}

    for i in range(1, len(parts), 2):
        title = parts[i]
        body = parts[i+1]

        num_match = re.search(r'\d+', title)
        if not num_match:
            continue

        num = num_match.group()

        solution_dict[f"solution_{num}.md"] = body

    return solution_dict

# ---------------- SMART MAPPING ---------------- #

def attach_keys_and_solutions(worksheet_text, solution_text):

    # Extract keys
    key_pattern = r'(\d+)\)\s*([^\n]+)'
    keys = dict(re.findall(key_pattern, solution_text))

    # Extract solutions
    sol_pattern = r'(\d+)\.\s*(.*?)(?=\n\d+\.|\Z)'
    solutions = dict(re.findall(sol_pattern, solution_text, flags=re.DOTALL))

    # Extract questions
    q_pattern = r'(\d+\..*?)(?=\n\d+\.|\Z)'
    questions = re.findall(q_pattern, worksheet_text, flags=re.DOTALL)

    final_output = ""

    for q in questions:
        num_match = re.match(r'(\d+)\.', q.strip())
        if not num_match:
            continue

        num = num_match.group(1)

        final_output += q.strip() + "\n"

        if num in keys:
            final_output += f"\nKey: {keys[num]}\n"

        if num in solutions:
            final_output += f"\nSolution:\n{solutions[num].strip()}\n"

        final_output += "\n" + "-"*40 + "\n\n"

    return final_output

# ---------------- MERGE FUNCTION ---------------- #

def merge_worksheet_solutions(worksheet_dict, solution_dict):
    merged = {}

    for key in worksheet_dict:
        num = re.search(r'\d+', key).group()

        worksheet_content = worksheet_dict[key]
        solution_content = solution_dict.get(f"solution_{num}.md", "")

        smart_output = attach_keys_and_solutions(
            worksheet_content,
            solution_content
        )

        merged[f"worksheet_{num}_smart.md"] = smart_output

    return merged

# ---------------- MAIN PROCESS ---------------- #

if file1 and file2:

    content1 = clean_content(file1.read().decode("utf-8"))
    content2 = clean_content(file2.read().decode("utf-8"))

    # ❌ REMOVE CUQ
    content1 = remove_cuq_sections(content1)
    content2 = remove_cuq_sections(content2)

    if st.button("🚀 Process Smart Mapping"):

        synopsis_dict, worksheet_dict = split_synopsis(content1)
        solution_dict = split_solutions(content2)

        merged_dict = merge_worksheet_solutions(worksheet_dict, solution_dict)

        final_files = {}
        final_files.update(synopsis_dict)
        final_files.update(merged_dict)

        zip_file = create_zip(final_files)

        st.success(f"✅ {len(final_files)} files created successfully!")

        st.download_button(
            label="⬇ Download Smart Output (ZIP)",
            data=zip_file,
            file_name="smart_output.zip",
            mime="application/zip"
        )

else:
    st.info("📌 Upload both files to proceed.")