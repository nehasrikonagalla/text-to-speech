import os
import io
# Ensure PyPDF2 is imported with correct capitalization
import PyPDF2 
from flask import Flask, render_template_string, request

# --- FLASK SETUP ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- CORE LOGIC FUNCTION ---
def extract_text_from_pdf(pdf_file_stream):
    """Extracts text from an uploaded PDF file stream."""
    try:
        # Use PyPDF2 with correct capitalization here
        reader = PyPDF2.PdfReader(pdf_file_stream) 
        text = ""
        for page in reader.pages:
            extracted_page_text = page.extract_text()
            if extracted_page_text:
                text += extracted_page_text + "\n\n"
        
        if not text.strip():
            return "Error: PDF contains no readable text."
        
        return text.strip()
    except NameError:
        # If this happens, it confirms the case-sensitivity issue or a missing import
        return "Critical Error: PyPDF2 module name is undefined."
    except Exception as e:
        return f"Error reading PDF: {e}"


# --- EMBEDDED HTML TEMPLATE (No Changes Needed Here) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Document Reader (Embedded Flask App)</title>
    <style>
        /* CSS from your beautiful design */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 50px 0;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            background: linear-gradient(135deg, #e0f7fa 0%, #b3e5fc 100%);
        }
        .container {
            width: 850px;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            overflow: hidden;
            border: 1px solid #ddd;
        }
        .control-frame {
            padding: 15px 10px;
            background-color: #f5f5f5;
            display: flex;
            align-items: center;
            border-bottom: 1px solid #eee;
        }
        .app-button {
            padding: 8px 15px;
            margin-right: 10px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            color: white;
            transition: background-color 0.2s, opacity 0.2s;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .app-button:hover:not(:disabled) {
            opacity: 0.9;
        }
        .app-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background-color: #888 !important;
        }
        .status-label {
            font-size: 11px;
            font-style: italic;
            color: gray;
            margin-left: 20px;
        }
        .text-area {
            height: 400px;
            padding: 20px;
            font-family: 'Consolas', monospace; 
            font-size: 14px;
            line-height: 1.6;
            border: none;
            resize: none;
            width: 100%;
            box-sizing: border-box;
            background-color: white;
            white-space: pre-wrap; 
            overflow-y: scroll;
        }
        .file-upload input[type="file"] {
            display: none;
        }
    </style>
</head>
<body>

<div class="container">
    <div class="control-frame">
        
        <form method="POST" enctype="multipart/form-data" action="/" style="display: flex; align-items: center;">
            <label for="pdf_file" class="app-button" style="background-color: #4a7a8c; cursor: pointer;">
                📂 Upload PDF
            </label>
            <input type="file" name="file" id="pdf_file" accept=".pdf" onchange="this.form.submit()">
            
            <span style="font-size: 12px; margin-left: 10px; color: #555;">
                {% if filename %}
                    Loaded: {{ filename }}
                {% else %}
                    No file selected.
                {% endif %}
            </span>
        </form>
        
        <button id="speak-btn" class="app-button" style="background-color: #007bff;" disabled>🎤 Speak Document</button>
        <button id="stop-btn" class="app-button" style="background-color: #dc3545;" disabled>⏹️ Stop Reading</button>

        <span id="status-label" class="status-label">
            {% if filename %}
                Status: {{ filename }} Loaded.
            {% else %}
                Status: Upload a PDF to begin.
            {% endif %}
        </span>

    </div>

    <div id="text-output" class="text-area">
        {{ text }}
    </div>
</div>

<script>
    // --- JAVASCRIPT FOR TEXT-TO-SPEECH ---
    const synth = window.speechSynthesis;
    const textOutput = document.getElementById('text-output');
    const speakBtn = document.getElementById('speak-btn');
    const stopBtn = document.getElementById('stop-btn');
    const statusLabel = document.getElementById('status-label');
    
    const PLACEHOLDER_TEXT = "Upload a PDF to see the extracted text here.";

    function checkTextAndEnable() {
        const textContent = textOutput.textContent.trim();
        
        if (textContent.length > 0 && textContent !== PLACEHOLDER_TEXT && !textContent.startsWith("Error")) {
            speakBtn.disabled = false;
        } else {
            speakBtn.disabled = true;
        }
    }
    
    window.onload = checkTextAndEnable;
    

    function startSpeaking() {
        if (!synth) {
            alert('Your browser does not support the Web Speech API.');
            return;
        }

        const text = textOutput.innerText;
        if (!text || text.trim() === '' || text.trim() === PLACEHOLDER_TEXT) {
            statusLabel.innerText = "Error: No valid text to speak.";
            statusLabel.style.color = "red";
            return;
        }

        if (synth.speaking) {
            synth.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(text);
        
        utterance.rate = 0.9; 
        utterance.volume = 1; 
        
        utterance.onstart = function() {
            speakBtn.disabled = true;
            stopBtn.disabled = false;
            statusLabel.innerText = "Status: Reading in progress...";
            statusLabel.style.color = "#005a00";
        };
        
        utterance.onend = function() {
            speakBtn.disabled = false;
            stopBtn.disabled = true;
            statusLabel.innerText = "Status: Reading finished.";
            statusLabel.style.color = "gray";
        };
        
        synth.speak(utterance);
    }

    function stopSpeaking() {
        if (synth.speaking) {
            synth.cancel();
            speakBtn.disabled = false;
            stopBtn.disabled = true;
            statusLabel.innerText = "Status: Reading stopped.";
            statusLabel.style.color = "red";
        }
    }

    // Attach event listeners to buttons
    speakBtn.addEventListener('click', startSpeaking);
    stopBtn.addEventListener('click', stopSpeaking);

</script>

</body>
</html>
"""


# --- WEB ROUTE ---
@app.route('/', methods=['GET', 'POST'])
def upload_and_process():
    extracted_text = "Upload a PDF to see the extracted text here."
    filename = None
    
    if request.method == 'POST':
        if 'file' not in request.files:
            extracted_text = "No file part in the request."
        else:
            file = request.files['file']
            
            if file.filename == '':
                extracted_text = "No selected file."
            elif file and file.filename.endswith('.pdf'):
                filename = file.filename
                
                file_stream = io.BytesIO(file.read())
                extracted_text = extract_text_from_pdf(file_stream)
            else:
                extracted_text = "Invalid file type. Please upload a PDF (.pdf)."

    # Render the HTML template string, passing variables to Jinja
    return render_template_string(HTML_TEMPLATE, 
                                  text=extracted_text, 
                                  filename=filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
    print("----------------------------------------------------------------------")
    print("Web App is running! Open your browser and go to: http://127.0.0.1:5000/")
    print("----------------------------------------------------------------------")
    app.run(debug=True)