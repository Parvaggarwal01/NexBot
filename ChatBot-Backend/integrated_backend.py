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
from io import BytesIO

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

def call_qa_chain_safely(qa_chain, question):
    """Safely call QA chain without rate limiting"""
    if not qa_chain:
        return "Policy assistant is currently unavailable."

    # Check if qa_chain is a function or has an invoke method
    if callable(qa_chain):
        return qa_chain(question)
    elif hasattr(qa_chain, 'invoke'):
        return qa_chain.invoke(question)
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

def clean_text_for_tts(text):
    """Clean text for better TTS by removing asterisks and markdown"""
    import re
    # Remove asterisks (both single and double)
    text = re.sub(r'\*+', '', text)
    # Remove other markdown formatting
    text = re.sub(r'[_#`~]', '', text)
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def text_to_speech_gtts_with_rate_limit(text, filepath=None, voice_type='female'):
    """gTTS without rate limiting and with voice variants"""
    if not TTS_AVAILABLE:
        print("❌ gTTS not available")
        return None

    # Voice configurations for different avatar types
    # Single US female voice for all avatars (faster, no delay)
    voice_config = {
        'lang': 'en',
        'tld': 'com',  # US English - simple, clear voice
        'slow': False
    }

    # Use the single US voice configuration

    try:
        # Clean text to remove asterisks and markdown
        cleaned_text = clean_text_for_tts(text)
        print(f"🎤 Generating {voice_type} voice TTS for: '{cleaned_text[:50]}...'")
        print(f"📁 Using config: {voice_type} ({voice_config['tld']} variant)")

        tts = gTTS(
            text=cleaned_text,
            lang=voice_config['lang'],
            tld=voice_config['tld'],
            slow=voice_config['slow']
        )

        if filepath:
            # Save to file
            tts.save(filepath)
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✅ {voice_type} voice audio file created: {file_size} bytes")
                return True
            else:
                print("❌ Audio file not created")
                return False
        else:
            # Return bytes for direct use
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.getvalue()
            print(f"✅ {voice_type} voice audio generated: {len(audio_bytes)} bytes")
            return audio_bytes

    except Exception as e:
        print(f"❌ gTTS Error: {e}")
        return None

def text_to_speech_gtts(text, filename, voice_type='female'):
    """Convert text to speech using gTTS with voice variants"""
    filepath = os.path.join(AUDIO_FOLDER, filename)

    print(f"🌐 Generating {voice_type} voice audio with gTTS...")
    if text_to_speech_gtts_with_rate_limit(text, filepath, voice_type):
        print(f"✅ gTTS {voice_type} voice generation successful")
        return filepath

    print(f"❌ gTTS {voice_type} voice generation failed")
    return None

def generate_audio_with_voice_variants(text, voice_type):
    """Generate audio with different voice variants using gTTS"""
    try:
        print(f"🎤 Generating {voice_type} voice TTS for: '{text[:50]}...'")

        # Single US female voice for all avatars (faster, no delay)
        voice_config = {
            'lang': 'en',
            'tld': 'com',  # US English - simple, clear voice
            'slow': False
        }

        config = voice_config
        print(f"📁 Using US female voice ({config['tld']} variant)")        # Create gTTS object
        # Clean text to remove asterisks and markdown
        cleaned_text = clean_text_for_tts(text)
        tts = gTTS(text=cleaned_text, lang=config['lang'], tld=config['tld'], slow=config['slow'])

        # Save to BytesIO buffer
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.read()

        print(f"✅ {voice_type} voice audio generated: {len(audio_bytes)} bytes")
        return base64.b64encode(audio_bytes).decode('utf-8')

    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        return None

def generate_simple_lipsync(text):
    """Generate simple lipsync data for text"""
    # Estimate duration based on text length (roughly 150 words per minute)
    word_list = text.split()
    word_count = len(word_list)
    duration = max(1.0, word_count / 2.5)  # Minimum 1 second, roughly 150 WPM

    # Generate basic mouth cues based on text content
    mouth_cues = []
    current_time = 0.0
    time_per_word = duration / max(1, word_count)

    # Simple vowel/consonant mapping for basic lipsync
    vowel_visemes = ['A', 'E', 'I', 'O', 'U']  # Open mouth shapes
    consonant_visemes = ['B', 'F', 'G', 'H', 'X']  # Various consonant shapes

    for i, word in enumerate(word_list):
        word_duration = time_per_word * 0.8  # Leave some gap between words
        cue_duration = word_duration / max(1, len(word))

        for j, char in enumerate(word.lower()):
            if char.isalpha():
                # Choose viseme based on character
                if char in 'aeiou':
                    viseme = vowel_visemes[ord(char) % len(vowel_visemes)]
                else:
                    viseme = consonant_visemes[ord(char) % len(consonant_visemes)]

                mouth_cues.append({
                    "start": current_time,
                    "end": current_time + cue_duration,
                    "value": viseme
                })
                current_time += cue_duration

        # Add a small pause between words
        current_time += time_per_word * 0.2

    return {
        "metadata": {"duration": duration},
        "mouthCues": mouth_cues
    }

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
        voice_type = data.get('voice_type', 'female')  # New parameter for voice type

        if not message.strip():
            return jsonify({'error': 'Please enter a question.'}), 400

        print(f"📝 Text chat request ({voice_type} voice): {message[:50]}...")

        # Quick test responses for hello/test
        if message.lower().strip() in ['test', 'hello', 'hi']:
            return jsonify({
                'response': "Hello! I'm your Educational Policy Assistant. I'm working properly. How can I help you with policy questions?",
                'message': "Hello! I'm your Educational Policy Assistant. I'm working properly. How can I help you with policy questions?",
                'mode': 'text-only',
                'voice_type': voice_type
            })

        # Use the rate-limited wrapper
        response = call_qa_chain_safely(qa_chain, message)

        print(f"✅ Response generated successfully")

        return jsonify({
            'response': response,
            'message': response,
            'mode': 'text-only',
            'voice_type': voice_type
        })

    except Exception as e:
        print(f"❌ Text chat error: {e}")
        return jsonify({
            'response': "I'm experiencing technical difficulties. Please try again in a moment.",
            'message': "I'm experiencing technical difficulties. Please try again in a moment.",
            'mode': 'text-only',
            'voice_type': voice_type
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
    """3D Avatar chat endpoint with voice variants"""
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        voice_type = data.get("voice_type", "female")  # New parameter for voice type

        print(f"🎭 3D chat request ({voice_type} voice): {user_message[:50]}...")

        # Default welcome message if no message provided
        if not user_message:
            welcome_text = "Hello! I'm your Educational Policy Assistant. How can I help you today?"
            welcome_audio = generate_audio_with_voice_variants(welcome_text, voice_type)

            return jsonify({
                "message": welcome_text,
                "audio": welcome_audio or "",
                "animation": "Talking_1",
                "lipsync": generate_simple_lipsync(welcome_text),
                "voice_type": voice_type
            })

        # Check if QA system is available
        if not qa_chain:
            error_text = "I apologize, but the policy system is currently unavailable. Please try again later."
            error_audio = generate_audio_with_voice_variants(error_text, voice_type)

            return jsonify({
                "message": error_text,
                "audio": error_audio or "",
                "animation": "Talking_0",
                "lipsync": generate_simple_lipsync(error_text),
                "voice_type": voice_type
            })

        # Get answer from policy QA system
        policy_answer = call_qa_chain_safely(qa_chain, user_message)
        print(f"✅ 3D response generated successfully")

        # Generate audio with specified voice type
        response_audio = generate_audio_with_voice_variants(policy_answer, voice_type)

        # Determine appropriate animation based on content
        animation = "Talking_0"
        if any(word in policy_answer.lower() for word in ["sorry", "apologize", "error", "problem"]):
            animation = "Talking_1"
        elif any(word in policy_answer.lower() for word in ["great", "excellent", "perfect", "congratulations"]):
            animation = "Talking_2"
        elif "not found" in policy_answer.lower() or "couldn't find" in policy_answer.lower():
            animation = "Talking_1"

        return jsonify({
            "message": policy_answer,
            "audio": response_audio or "",
            "animation": animation,
            "lipsync": generate_simple_lipsync(policy_answer),
            "voice_type": voice_type
        })

    except Exception as e:
        print(f"❌ 3D Chat error: {e}")
        error_text = "I encountered an error processing your question. Please try again."
        voice_type = request.json.get("voice_type", "female") if request.json else "female"
        error_audio = generate_audio_with_voice_variants(error_text, voice_type)

        return jsonify({
            "message": error_text,
            "audio": error_audio or "",
            "animation": "Talking_0",
            "lipsync": generate_simple_lipsync(error_text),
            "voice_type": voice_type
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
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Simple test
        response = model.generate_content("Hello")

        return jsonify({
            'status': 'success',
            'api_working': True,
            'test_response': response.text[:100],
            'current_model': 'gemini-2.5-flash',
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