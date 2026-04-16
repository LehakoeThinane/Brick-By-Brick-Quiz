import requests
import io
from docx import Document

url = "https://raw.githubusercontent.com/LehakoeThinane/Brick-By-Brick-Quiz/main/ARCHITEKT_PRD_v1_Brick-By-Brick%20App.docx"
response = requests.get(url)
response.raise_for_status()

# Load document from memory
doc = Document(io.BytesIO(response.content))

# Extract all text and print
full_text = []
for para in doc.paragraphs:
    if para.text.strip():
        full_text.append(para.text.strip())

with open("prd_text.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(full_text))

