import os
import json
import base64
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")
import time
from threading import Lock
from functools import wraps

# Load environment variables
load_dotenv()

# Global rate limiter
_last_api_call = 0
_api_lock = Lock()
MIN_API_INTERVAL = 3  # 3 seconds between API calls

# Import your existing retriever
import sys
sys.path.append('ChatBot-Backend')
from local_embedding_retriever import get_qa_chain, build_retriever, rebuild_embeddings_cache

# Rate limiting decorator
def rate_limit_api(func):
    """Decorator to rate limit API calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _last_api_call

        with _api_lock:
            now = time.time()
            time_since_last = now - _last_api_call

            if time_since_last < MIN_API_INTERVAL:
                sleep_time = MIN_API_INTERVAL - time_since_last
                print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)

            try:
                result = func(*args, **kwargs)
                _last_api_call = time.time()
                return result
            except Exception as e:
                print(f"🚨 API call failed: {e}")
                _last_api_call = time.time()  # Still update time to prevent spam
                raise e

    return wrapper

@rate_limit_api
def call_qa_chain_safely(qa_chain, message):
    """Safely call QA chain with rate limiting"""
    if not qa_chain:
        return "Policy assistant is currently unavailable."

    # Check if qa_chain is a function or has an invoke method
    if callable(qa_chain):
        return qa_chain(message)
    elif hasattr(qa_chain, 'invoke'):
        return qa_chain.invoke(message)
    else:
        return "QA chain is not properly configured."

# For free TTS - using gTTS (Google Text-to-Speech) - completely free
try:
    from gtts import gTTS
    import tempfile
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# TTS will use gTTS only for better web audio compatibility

# Rate limiting imports
import time
from threading import Lock

# Rate limiting variables
last_request_time = 0
request_lock = Lock()
MIN_REQUEST_INTERVAL = 3  # 3 seconds between requests

# Set environment variables
os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
CORS(app)  # Enable CORS for 3D frontend

UPLOAD_FOLDER = "data"
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Audio storage
AUDIO_FOLDER = "audios"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Initialize QA chain
qa_chain = None
try:
    qa_chain = get_qa_chain()
    print("✅ Policy QA system initialized successfully!")
except Exception as e:
    print(f"⚠️ Failed to initialize QA system: {e}")

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Removed local TTS - using gTTS only for better web compatibility

def text_to_speech_gtts_with_rate_limit(text, filepath, language='en'):
    """gTTS with rate limiting to avoid 429 errors"""
    global last_request_time

    if not TTS_AVAILABLE:
        print("❌ gTTS not available")
        return False

    with request_lock:
        # Ensure minimum interval between requests
        current_time = time.time()
        time_since_last = current_time - last_request_time

        if time_since_last < MIN_REQUEST_INTERVAL:
            wait_time = MIN_REQUEST_INTERVAL - time_since_last
            print(f"⏳ TTS Rate limiting: waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

        try:
            print(f"🎤 Generating TTS for: '{text[:50]}...'")
            print(f"📁 Saving to: {filepath}")

            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(filepath)
            last_request_time = time.time()

            # Verify file was created
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✅ Audio file created: {file_size} bytes")
                return True
            else:
                print("❌ Audio file not created")
                return False

        except Exception as e:
            print(f"❌ gTTS Error: {e}")
            return False

def text_to_speech_gtts(text, filename, language='en'):
    """Convert text to speech using gTTS with rate limiting"""
    filepath = os.path.join(AUDIO_FOLDER, filename)

    print("🌐 Generating audio with gTTS...")
    if text_to_speech_gtts_with_rate_limit(text, filepath, language):
        print("✅ gTTS audio generation successful")
        return filepath

    print("❌ gTTS audio generation failed")
    return None

def get_audio_duration(audio_file):
    """Get actual duration of audio file using ffprobe"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', audio_file
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 3.0  # Default fallback

def create_lipsync_data(audio_file, json_file):
    """Create lip-sync data using Rhubarb or intelligent fallback"""
    try:
        # Convert mp3 to wav if needed
        wav_file = audio_file.replace('.mp3', '.wav')
        subprocess.run([
            'ffmpeg', '-y', '-i', audio_file, wav_file
        ], capture_output=True)

        # Get actual audio duration
        duration = get_audio_duration(wav_file)
        print(f"🎵 Audio duration: {duration:.2f} seconds")

        # Try to use rhubarb if available
        rhubarb_success = False
        try:
            result = subprocess.run([
                '/Users/parvaggarwal/Coding/Chatbot-Edu/bin/rhubarb', '-f', 'json', '-o', json_file, wav_file, '-r', 'phonetic'
            ], capture_output=True, check=True, text=True)
            print("✅ Rhubarb lip-sync generated successfully")
            rhubarb_success = True
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Rhubarb failed: {e}")
            print(f"Rhubarb stderr: {e.stderr}")
            rhubarb_success = False

        # If Rhubarb failed, create intelligent fallback lip-sync data
        if not rhubarb_success:
            print(f"🔄 Creating fallback lip-sync data for {duration:.2f}s")
            # Create more realistic mouth movements based on duration
            mouth_shapes = ["A", "B", "C", "D", "E", "F", "G", "H", "X"]
            cues = []

            # Generate mouth cues every 0.1 seconds for smooth animation
            step = 0.1
            current_time = 0.0
            shape_index = 0

            while current_time < duration:
                next_time = min(current_time + step, duration)
                cue = {
                    "start": round(current_time, 2),
                    "end": round(next_time, 2),
                    "value": mouth_shapes[shape_index % len(mouth_shapes)]
                }
                cues.append(cue)
                current_time = next_time
                shape_index += 1

            simple_lipsync = {
                "metadata": {"duration": duration},
                "mouthCues": cues
            }
            with open(json_file, 'w') as f:
                json.dump(simple_lipsync, f)

        return json_file
    except Exception as e:
        print(f"Lipsync error: {e}")
        return None

def audio_file_to_base64(filepath):
    """Convert audio file to base64"""
    try:
        with open(filepath, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

def read_json_transcript(filepath):
    """Read lipsync JSON data"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return {"metadata": {"duration": 2.0}, "mouthCues": []}

# ------------------ POLICY MANAGEMENT ROUTES (Original) ------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    # Support both 'query' and 'message' for backward compatibility
    query = request.json.get("query") or request.json.get("message", "")
    if not query:
        return jsonify({"answer": "Please enter a question."})

    if qa_chain:
        answer = qa_chain(query)
        return jsonify({"answer": answer, "response": answer})  # Return both for compatibility
    else:
        return jsonify({"answer": "Policy system not available. Please contact administrator."})

# Fast text-only endpoint for chat mode (no audio/lip-sync processing)
@app.route("/chat-text", methods=["POST", "OPTIONS"])
def chat_text():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message.strip():
            return jsonify({'error': 'Please enter a question.'}), 400

        print(f"📝 Text chat request: {message[:50]}...")

        # Use the rate-limited wrapper
        response = call_qa_chain_safely(qa_chain, message)

        print(f"✅ Response generated successfully")

        return jsonify({
            'response': response,
            'message': response,
            'mode': 'text-only'
        })

    except Exception as e:
        print(f"❌ Text chat error: {e}")
        return jsonify({
            'response': "I'm experiencing technical difficulties. Please try again in a moment.",
            'message': "I'm experiencing technical difficulties. Please try again in a moment.",
            'mode': 'text-only'
        }), 500

# ------------------ ADMIN ROUTES ------------------
@app.route("/admin")
def admin_login():
    return render_template("admin_login.html")

@app.route("/admin/login", methods=["POST"])
def admin_login_post():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == "admin" and password == "admin123":
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html", error="Invalid credentials")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

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
    rebuild_embeddings_cache()
    qa_chain = get_qa_chain()
    return redirect(url_for("admin_dashboard"))

# ------------------ 3D AVATAR API ROUTES ------------------
@app.route("/chat", methods=["POST"])
def chat_3d():
    """3D Avatar chat endpoint - integrates with policy QA system"""
    user_message = request.json.get("message", "")

    # Default welcome message if no message provided
    if not user_message:
        return jsonify({
            "messages": [
                {
                    "text": "Hello! I'm your Educational Policy Assistant. How can I help you today?",
                    "audio": audio_file_to_base64(os.path.join(AUDIO_FOLDER, "intro_0.wav")) if os.path.exists(os.path.join(AUDIO_FOLDER, "intro_0.wav")) else "",
                    "lipsync": read_json_transcript(os.path.join(AUDIO_FOLDER, "intro_0.json")),
                    "facialExpression": "smile",
                    "animation": "Talking_1"
                },
                {
                    "text": "I can help you understand attendance policies, CARE guidelines, and certification requirements.",
                    "audio": audio_file_to_base64(os.path.join(AUDIO_FOLDER, "intro_1.wav")) if os.path.exists(os.path.join(AUDIO_FOLDER, "intro_1.wav")) else "",
                    "lipsync": read_json_transcript(os.path.join(AUDIO_FOLDER, "intro_1.json")),
                    "facialExpression": "default",
                    "animation": "Talking_0"
                }
            ]
        })

    # Check if QA system is available
    if not qa_chain:
        return jsonify({
            "messages": [
                {
                    "text": "I apologize, but the policy system is currently unavailable. Please try again later.",
                    "audio": "",
                    "lipsync": {"metadata": {"duration": 2.0}, "mouthCues": []},
                    "facialExpression": "sad",
                    "animation": "Talking_0"
                }
            ]
        })

    try:
        # Get answer from your policy QA system (rate-limited)
        print(f"🎭 3D chat request: {user_message[:50]}...")
        policy_answer = call_qa_chain_safely(qa_chain, user_message)
        print(f"✅ 3D response generated successfully")

        # Determine appropriate facial expression and animation based on content
        facial_expression = "default"
        animation = "Talking_0"

        # Simple sentiment analysis for expressions
        if any(word in policy_answer.lower() for word in ["sorry", "apologize", "error", "problem"]):
            facial_expression = "sad"
            animation = "Talking_1"
        elif any(word in policy_answer.lower() for word in ["great", "excellent", "perfect", "congratulations"]):
            facial_expression = "smile"
            animation = "Talking_2"
        elif "not found" in policy_answer.lower() or "couldn't find" in policy_answer.lower():
            facial_expression = "surprised"
            animation = "Talking_1"

        # Split long responses into shorter messages (for better 3D presentation)
        messages = []
        sentences = policy_answer.split('. ')

        # Group sentences into messages (max 2 sentences per message)
        for i in range(0, len(sentences), 2):
            message_text = '. '.join(sentences[i:i+2])
            if message_text and not message_text.endswith('.'):
                message_text += '.'

            # Generate audio for this message part
            audio_filename = f"message_{i//2}.mp3"
            audio_filepath = text_to_speech_gtts(message_text, audio_filename)

            # Generate lipsync data
            lipsync_file = os.path.join(AUDIO_FOLDER, f"message_{i//2}.json")
            if audio_filepath:
                create_lipsync_data(audio_filepath, lipsync_file)

            messages.append({
                "text": message_text,
                "audio": audio_file_to_base64(audio_filepath) if audio_filepath else "",
                "lipsync": read_json_transcript(lipsync_file),
                "facialExpression": facial_expression,
                "animation": animation
            })

            # Limit to 3 messages maximum
            if len(messages) >= 3:
                break

        # If no messages created, create a default one
        if not messages:
            messages = [{
                "text": policy_answer,
                "audio": "",
                "lipsync": {"metadata": {"duration": 2.0}, "mouthCues": []},
                "facialExpression": facial_expression,
                "animation": animation
            }]

        return jsonify({"messages": messages})

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "messages": [
                {
                    "text": "I encountered an error processing your question. Please try again.",
                    "audio": "",
                    "lipsync": {"metadata": {"duration": 2.0}, "mouthCues": []},
                    "facialExpression": "sad",
                    "animation": "Talking_0"
                }
            ]
        })

# ------------------ UTILITY ROUTES ------------------
@app.route("/audios/<filename>")
def serve_audio(filename):
    """Serve audio files"""
    try:
        audio_path = os.path.join(AUDIO_FOLDER, filename)
        if os.path.exists(audio_path):
            # Determine mimetype based on file extension
            if filename.endswith('.mp3'):
                mimetype = 'audio/mpeg'
            elif filename.endswith('.wav'):
                mimetype = 'audio/wav'
            else:
                mimetype = 'audio/mpeg'  # Default to mp3
            return send_file(audio_path, mimetype=mimetype)
        else:
            print(f"⚠️ Audio file not found: {audio_path}")
            return "Audio file not found", 404
    except Exception as e:
        print(f"Error serving audio: {e}")
        return "Error serving audio", 500

@app.route("/voices")
def get_voices():
    """Return available TTS voices info"""
    return jsonify({
        "voices": [
            {"id": "gtts-en", "name": "Google TTS English"},
            {"id": "gtts-en-uk", "name": "Google TTS British"},
            {"id": "gtts-en-us", "name": "Google TTS American"}
        ]
    })

@app.route('/debug-api', methods=['GET'])
def debug_api():
    """Debug API status and test a simple call"""
    try:
        import google.generativeai as genai

        # Test a very simple API call
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Simple test
        response = model.generate_content("Hello")

        return jsonify({
            'status': 'success',
            'api_working': True,
            'test_response': response.text[:100],
            'current_model': 'gemini-2.0-flash',
            'rate_limit_interval': MIN_API_INTERVAL
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'api_working': False,
            'error': str(e),
            'error_type': type(e).__name__
        })

@app.route('/status', methods=['GET'])
def status():
    """Check system status"""
    global _last_api_call

    current_time = time.time()
    time_since_last = current_time - _last_api_call

    return jsonify({
        'status': 'online',
        'last_api_call': _last_api_call,
        'time_since_last_call': time_since_last,
        'rate_limit_interval': MIN_API_INTERVAL,
        'ready_for_call': time_since_last >= MIN_API_INTERVAL,
        'qa_chain_available': qa_chain is not None
    })

if __name__ == "__main__":
    # Install gTTS if not available
    if not TTS_AVAILABLE:
        print("📦 Installing gTTS for free text-to-speech...")
        try:
            subprocess.check_call(["pip", "install", "gtts"])
            print("✅ gTTS installed successfully!")
        except:
            print("⚠️ Please install gTTS manually: pip install gtts")

    app.run(host="0.0.0.0", port=5001, debug=True)