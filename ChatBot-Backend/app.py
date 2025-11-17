from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
from local_embedding_retriever import get_qa_chain, build_retriever, rebuild_embeddings_cache
from dotenv import load_dotenv

# Set environment variable to avoid tokenizers warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv()


app = Flask(__name__)
app.secret_key = "your_secret_key_here"

UPLOAD_FOLDER = "data"
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

qa_chain = get_qa_chain()

# ------------------ Helper ------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ USER CHAT ------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query", "")
    if not query:
        return jsonify({"answer": "Please enter a question."})
    answer = qa_chain(query)
    return jsonify({"answer": answer})

# ------------------ ADMIN AUTH ------------------
@app.route("/admin")
def admin_login():
    return render_template("admin_login.html")

@app.route("/admin/login", methods=["POST"])
def admin_login_post():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == "admin" and password == "admin123":  # change this
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html", error="Invalid credentials")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ------------------ ADMIN DASHBOARD ------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    files = os.listdir(UPLOAD_FOLDER)
    return render_template("admin_dashboard.html", files=files)

@app.route("/admin/upload", methods=["POST"])
def upload_file():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    file = request.files["file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for("admin_dashboard"))
    return "Invalid file type", 400

@app.route("/admin/rebuild", methods=["POST"])
def rebuild_index():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    global qa_chain
    rebuild_embeddings_cache()  # Clear old embeddings cache
    qa_chain = get_qa_chain()  # Rebuild with new embeddings
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
