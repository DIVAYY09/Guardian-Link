import os
import subprocess
from dotenv import load_dotenv
load_dotenv(override=True)
import time
import webbrowser
import threading
import sys
import psutil
import shutil

# Environment Injection
os.environ['PYTHONPATH'] = os.getcwd()

# 1. Disable Bytecode to prevent __pycache__ loops
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

def kill_zombie_processes(ports=[5173, 5174, 5175, 8000, 8001, 8005]):
    """Forcefully kill any process listening on the specified ports."""
    print(f"[*] Cleaning up ports: {ports}...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.net_connections(kind='inet'):
                if conn.laddr.port in ports:
                    try:
                        print(f"    [!] Killing zombie process {proc.info['name']} (PID: {proc.info['pid']}) on port {conn.laddr.port}")
                        proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def check_env():
    print("[*] Checking environment...")
    if not os.path.exists(".env"):
        print("[!] .env file not found!")
        return False
    
    content = ""
    try:
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[!] Info: could not read .env as utf-8 ({e}), trying system default...")
        try:
            with open(".env", "r") as f:
                content = f.read()
        except Exception as e2:
            print(f"[!] Failed to read .env file: {e2}")
            return False

    missing = []
    # Strict check for GOOGLE_API_KEY as per Gemini requirement
    if "GOOGLE_API_KEY" not in content:
        missing.append("GOOGLE_API_KEY")
    # Azure keys are still relevant for Vision/Speech services
    if "AZURE_VISION_KEY" not in content:
        missing.append("AZURE_VISION_KEY")
        
    if missing:
        print(f"[!] Missing keys in .env: {', '.join(missing)}")
        return False
            
    print("[+] Environment check passed.")
    return True

def run_backend():
    print("[*] Starting Backend Server...")
    backend_dir = os.path.join(os.getcwd(), "backend")
    venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
    
    if not os.path.exists(venv_python):
        print(f"[!] Backend venv not found. Trying system python...")
        venv_python = sys.executable

    # Updated command: strict module execution from root
    cmd = [
        venv_python, "-m", "uvicorn", "backend.main:app", 
        "--host", "0.0.0.0",
        "--port", "8005",
        "--workers", "1",
        "--loop", "asyncio",
        "--reload-exclude", "*.wav",
        "--reload-exclude", "backend/static/*",
        "--reload-exclude", "guardianlink_runtime/*"
    ]
    
    try:
        # Set PYTHONPATH to the current working directory (ROOT)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        # Use Popen instead of run to avoid blocking
        process = subprocess.Popen(
            cmd, 
            cwd=os.getcwd(), 
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(f"[BACKEND] {line.rstrip()}")
            
    except Exception as e:
        print(f"[!] Backend failed: {e}")

def run_frontend():
    print("[*] Starting Frontend Application...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    cmd = ["cmd", "/c", "npm", "run", "dev", "--", "--port", "5175"]
    
    try:
        # Use Popen instead of run to avoid blocking
        process = subprocess.Popen(
            cmd, 
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(f"[FRONTEND] {line.rstrip()}")
            
    except Exception as e:
        print(f"[!] Frontend failed: {e}")

def main():
    print("="*40)
    print(" GUARDIAN-LINK LAUNCHER ")
    print("="*40)
    
    if not check_env():
        input("Press Enter to exit...")
        return

    # Cleanup zombie processes before starting
    # Cleanup cache and zombie processes before starting
    print("[*] performing Hard Cache Clean...")
    clean_commands = [
        "rm -rf frontend/node_modules/.vite",
        "rm -rf backend/__pycache__",
        "rm -rf backend/services/__pycache__",
        "rm -rf __pycache__"
    ]
    # Note: On Windows 'rm' might not work in cmd without powershell, using python shutil would be safer but simple is fine for now if running via git bash or similar. 
    # Actually, let's use shutil in python to be OS agnostic and safe.
    import shutil
    
    paths_to_clean = [
        os.path.join("frontend", "node_modules", ".vite"),
        os.path.join("backend", "__pycache__"),
        os.path.join("backend", "services", "__pycache__"),
        "__pycache__",
        # Clean audio artifacts to ensure fresh start
        os.path.join("backend", "static", "audio")
    ]
    
    for p in paths_to_clean:
        full_path = os.path.abspath(p)
        if os.path.exists(full_path):
            print(f"    [-] Removing: {p}")
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
            except OSError as e:
                # Silence access denied errors
                if "Access is denied" in str(e) or getattr(e, 'winerror', 0) == 5:
                    print(f"    [!] Access denied to {p}, skipping...")
                    pass
                else:
                    print(f"    [!] Failed to remove {p}: {e}")
            except Exception as e:
                print(f"    [!] Failed to remove {p}: {e}")

    kill_zombie_processes()

    threading.Thread(target=run_backend, daemon=True).start()
    time.sleep(5)  # Increased wait time for backend initialization
    threading.Thread(target=run_frontend, daemon=True).start()
    time.sleep(5)  # Wait for frontend to start
    
    print("WEBSOCKET LISTENING ON 0.0.0.0:8005 (Localhost Accessible)")
    print("[*] Launching Browser...")
    webbrowser.open("http://localhost:5175")
    
    print("\n[+] System Online. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
