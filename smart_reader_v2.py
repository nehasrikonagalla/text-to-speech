import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import PyPDF2
import os
import pyttsx3
import threading

# --- GLOBAL VARIABLES & ENGINE SETUP ---

tts_engine = None
speaking_thread = None # Initialize as None

DEFAULT_VOLUME = 0.9

def print_available_voices(engine):
    """Prints all available voice IDs and names to the console."""
    if engine:
        voices = engine.getProperty('voices')
        print("\n--- Available TTS Voices ---")
        for i, voice in enumerate(voices):
            print(f"Index {i}: ID='{voice.id}' | Name='{voice.name}' | Gender='{voice.gender}'")
        print("----------------------------\n")

# Function to update the volume (needed for the slider)
def set_tts_volume(vol):
    """Updates the pyttsx3 volume property based on the slider value."""
    if tts_engine:
        # Convert the slider value (0-10) to the required float range (0.0-1.0)
        new_volume = float(vol) / 10.0 
        tts_engine.setProperty('volume', new_volume)


try:
    tts_engine = pyttsx3.init()
    
    print_available_voices(tts_engine) 
    
    # --- VOICE OPTIMIZATION ---
    voices = tts_engine.getProperty('voices')
    
    if len(voices) > 1:
        try:
            tts_engine.setProperty('voice', voices[1].id) 
        except Exception:
            pass
            
    tts_engine.setProperty('rate', 150)
    tts_engine.setProperty('volume', DEFAULT_VOLUME) 
    
except Exception as e:
    messagebox.showerror("TTS Error", f"Failed to initialize TTS engine: {e}")
    tts_engine = None


# --- CORE LOGIC FUNCTIONS ---

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                extracted_page_text = page.extract_text()
                if extracted_page_text:
                    text += extracted_page_text + "\n\n"
            return text
    except Exception as e:
        messagebox.showerror("File Error", f"Could not read PDF: {e}")
        return None

def open_file():
    """Opens file dialog, extracts text, and displays it."""
    global speaking_thread
    stop_speaking()

    filepath = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
    )
    
    if not filepath:
        return

    document_text = extract_text_from_pdf(filepath)
    
    if document_text:
        text_area.delete('1.0', tk.END) 
        text_area.insert(tk.INSERT, document_text)
        status_label.config(text=f"Loaded: {os.path.basename(filepath)}")
        
        speak_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED) 


def start_speaking_thread():
    """Starts the TTS function in a separate thread."""
    global speaking_thread
    
    if tts_engine is None:
        messagebox.showwarning("TTS Warning", "Text-to-Speech engine is not available.")
        return

    # FIX: Check if the thread is None OR if it is not currently alive
    # This allows a new thread to be created after the old one is finished/stopped.
    if speaking_thread is not None and speaking_thread.is_alive():
        return
    
    text_to_speak = text_area.get('1.0', tk.END).strip() 
    
    if not text_to_speak:
        messagebox.showinfo("Speech Info", "Document is empty.")
        return

    # Create and start a NEW thread
    speaking_thread = threading.Thread(target=tts_run, args=(text_to_speak,))
    speaking_thread.start()
    status_label.config(text="Status: Reading document...")
    speak_button.config(text="Reading...", state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)


def tts_run(text):
    """The function that actually handles the TTS speaking (runs in a separate thread)."""
    global speaking_thread
    tts_engine.say(text)
    tts_engine.runAndWait()
    
    # FIX 1: Reset the thread to None when reading finishes naturally
    speaking_thread = None
    
    # Reset buttons when reading finishes naturally
    root.after(0, lambda: [speak_button.config(text="Speak Document", state=tk.NORMAL), 
                            status_label.config(text="Status: Reading finished."),
                            stop_button.config(state=tk.DISABLED)])


def stop_speaking():
    """Stops the TTS engine and resets states."""
    global speaking_thread
    # Check if the thread is alive before calling stop
    if tts_engine and (speaking_thread and speaking_thread.is_alive()):
        tts_engine.stop()
        
        # FIX 2: Reset the thread to None after manual stop
        speaking_thread = None

        status_label.config(text="Status: Reading stopped.")
        speak_button.config(text="Speak Document", state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)


# --- GUI SETUP ---

root = tk.Tk()
root.title("Smart Document Reader (v7: Stable Reading & Volume)")
root.geometry("850x600")

# 1. Top Control Frame
control_frame = tk.Frame(root, pady=10)
control_frame.pack(side=tk.TOP, fill=tk.X)

# Button to open file
open_button = tk.Button(control_frame, text="Open PDF Document", command=open_file, font=("Arial", 12, "bold"))
open_button.pack(padx=10, side=tk.LEFT)

# Button to start speaking
speak_button = tk.Button(control_frame, text="Speak Document", command=start_speaking_thread, font=("Arial", 12), state=tk.DISABLED)
speak_button.pack(padx=10, side=tk.LEFT)

# Button to stop speaking
stop_button = tk.Button(control_frame, text="Stop Reading", command=stop_speaking, font=("Arial", 12), state=tk.DISABLED)
stop_button.pack(padx=10, side=tk.LEFT)

# Volume Label
volume_label = tk.Label(control_frame, text="Volume:", font=("Arial", 12))
volume_label.pack(padx=10, side=tk.LEFT)

# Volume Slider (Scale)
volume_slider = tk.Scale(
    control_frame, 
    from_=0, to=10, 
    orient=tk.HORIZONTAL, 
    length=100, 
    command=set_tts_volume,
    showvalue=False,
    resolution=1
)
# Set the initial slider position to the default volume (0.9 * 10 = 9)
volume_slider.set(DEFAULT_VOLUME * 10)
volume_slider.pack(padx=0, side=tk.LEFT)


# Status Label
status_label = tk.Label(control_frame, text="No document loaded. Load PDF to start.", fg="gray")
status_label.pack(padx=10, side=tk.LEFT)

# 2. Main Text Display Area
text_area = scrolledtext.ScrolledText(
    root, 
    wrap=tk.WORD, 
    font=("Times New Roman", 14),
    padx=10,
    pady=10
)
text_area.pack(expand=True, fill=tk.BOTH)

root.mainloop()