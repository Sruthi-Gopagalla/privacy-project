from flask import Flask, render_template, request
import spacy
import re
import os
from docx import Document
import PyPDF2

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Load NLP model
# Load NLP model safely (for Render)
try:
    nlp = spacy.load("en_core_web_sm")
except:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Create upload folder if not exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")


def extract_text_from_file(file_path):
    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif file_path.endswith(".pdf"):
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
        return text

    return ""


def privacy_transform(text):
    doc = nlp(text)
    transformed_text = text

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            transformed_text = transformed_text.replace(ent.text, "[NAME]")
        elif ent.label_ == "GPE":
            transformed_text = transformed_text.replace(ent.text, "[LOCATION]")
        elif ent.label_ == "ORG":
            transformed_text = transformed_text.replace(ent.text, "[ORGANIZATION]")
        elif ent.label_ == "DATE":
            transformed_text = transformed_text.replace(ent.text, "[DATE]")

    transformed_text = re.sub(r"\b[6-9]\d{9}\b", "[PHONE]", transformed_text)
    transformed_text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[EMAIL]", transformed_text)

    return transformed_text


@app.route("/", methods=["GET", "POST"])
def home():
    original_text = ""
    transformed_text = ""

    if request.method == "POST":

        # If text submitted
        if "text" in request.form and request.form["text"]:
            original_text = request.form["text"]
            transformed_text = privacy_transform(original_text)

        # If file uploaded
        if "file" in request.files:
            file = request.files["file"]

            if file.filename != "":
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(file_path)

                original_text = extract_text_from_file(file_path)
                transformed_text = privacy_transform(original_text)

    return render_template("index.html",
                           original_text=original_text,
                           transformed_text=transformed_text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)