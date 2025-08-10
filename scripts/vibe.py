#!/usr/bin/env python3
"""
vibe.py – press ⏎ → speak → Whisper-medium → GPT-4o → writes gpt_code_v#.py
"""
import os, tempfile, numpy as np, sounddevice as sd, soundfile as sf
import whisper, openai, glob                                    # ← openai-whisper here
# ---------- settings ----------
RATE      = 16_000     # Hz
MAX_SEC   = 45         # max record length
MODEL_ID  = "medium"   # whisper model size (140 MB, downloads first run)
openai.api_key = os.getenv("OPENAI_API_KEY")
# ------------------------------

def get_next_filename():
    """Get filename based on user input for what they're building"""
    print("\n💾 What are you building? (e.g., 'draft_state', 'espn_players', 'team_analyzer')")
    description = input("Brief description: ").strip().lower().replace(" ", "_")
    
    if not description:
        # Fallback to version numbers if no description
        return f"gpt_code_v{get_next_version()}.py"
    
    # Check if this description already exists
    existing_files = glob.glob(f"*{description}*.py")
    if existing_files:
        # Add version number to existing description
        version = len([f for f in existing_files if description in f]) + 1
        return f"{description}_v{version}.py"
    else:
        return f"{description}.py"

def get_next_version():
    """Find the next version number for gpt_code_v#.py files (fallback)"""
    existing_files = glob.glob("gpt_code_v*.py")
    if not existing_files:
        return 1
    
    # Extract version numbers from filenames
    versions = []
    for filename in existing_files:
        try:
            # Extract number from gpt_code_v#.py
            version_str = filename.replace("gpt_code_v", "").replace(".py", "")
            versions.append(int(version_str))
        except ValueError:
            continue
    
    return max(versions) + 1 if versions else 1

def record() -> str:
    print("▶︎  Recording…  (Ctrl-C to stop early)")
    frames = []
    try:
        with sd.InputStream(samplerate=RATE, channels=1, dtype="int16",
                            callback=lambda d, *_: frames.extend(d[:, 0])):
            sd.sleep(MAX_SEC * 1000)
    except KeyboardInterrupt:
        print("⏹  Stopped by user.")
    wav = tempfile.mktemp(suffix=".wav")
    sf.write(wav, np.asarray(frames, np.int16), RATE)
    return wav

def main() -> None:
    input("Press Enter to start talking…")
    wav = record()
    import warnings
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
    
    text = whisper.load_model(MODEL_ID).transcribe(wav)["text"]
    print("\n📝  Transcript:\n", text)
    
    reply = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a code generator. Return ONLY executable Python code with NO markdown fences, NO explanations, NO comments. Just raw Python code that can be executed directly."},
            {"role": "user", "content": text}
        ],
        temperature=0.2
    ).choices[0].message.content
    
    # Strip markdown fences if they exist
    if reply.startswith("```python"):
        reply = reply[9:]  # Remove ```python
    if reply.startswith("```"):
        reply = reply[3:]   # Remove ```
    if reply.endswith("```"):
        reply = reply[:-3]  # Remove trailing ```
    reply = reply.strip()   # Remove extra whitespace
    
    print("\n🤖  GPT reply:\n", reply)
    
    # Save with descriptive name
    filename = get_next_filename()
    
    with open(filename, "w") as f:
        f.write(reply)
    
    print(f"\n💾  Saved GPT code to {filename}")

if __name__ == "__main__":
    main()