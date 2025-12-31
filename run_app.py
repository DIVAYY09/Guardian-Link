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
import stat

# Environment Injection
os.environ['PYTHONPATH'] = os.getcwd()
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def kill_zombie_processes(ports=[5173, 5174, 5175, 8000, 8001, 8005]):
    """Forcefully kill any process listening on the specified ports."""
    print(f"[*] Cleaning up ports: {ports}...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # CRITICAL FIX: Ignore System Idle Process (PID 0)
            if proc.info['pid'] == 0:
                continue
                
            for conn in proc.net_connections(kind='inet'):
                if conn.laddr.port in ports:
                    try:
                        print(f"    [!] Killing process {proc.info['name']} (PID: {proc.info['pid']}) on port {conn.laddr.port}")
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
    except:
        with open(".env", "r") as f:
            content = f.read()

    missing = []
    if "GOOGLE_API_KEY" not in content:
        missing.append("GOOGLE_API_KEY")
        
    if missing:
        print(f"[!] Warning: Missing keys in .env: {', '.join(missing)}. Some features will be disabled.")
            
    print("[+] Environment check passed.")
    return True

def run_backend():
    print("[*] Starting Backend Server...")
    backend_dir = os.path.join(os.getcwd(), "backend")
    venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
    
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    # Run uvicorn as a module from the root directory
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
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        process = subprocess.Popen(
            cmd, 
            cwd=os.getcwd(), 
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Read output line by line
        for line in process.stdout:
            print(f"[BACKEND] {line.rstrip()}")
            
    except Exception as e:
        print(f"[!] Backend failed: {e}")

def run_frontend():
    print("[*] Starting Frontend Application...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    cmd = ["cmd", "/c", "npm", "run", "dev", "--", "--port", "5175"]
    
    try:
        process = subprocess.Popen(
            cmd, 
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(f"[FRONTEND] {line.rstrip()}")
            
    except Exception as e:
        print(f"[!] Frontend failed: {e}")

def main():
    print("="*40)
    print(" GUARDIAN-LINK LAUNCHER ")
    print("="*40)
    
    check_env()

    print("[*] Performing Cache Clean...")
    
    paths_to_clean = [
        os.path.join("frontend", "node_modules", ".vite"),
        os.path.join("backend", "__pycache__"),
        os.path.join("backend", "services", "__pycache__"),
        "__pycache__"
    ]
    
    for p in paths_to_clean:
        full_path = os.path.abspath(p)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                shutil.rmtree(full_path, onerror=on_rm_error)
            else:
                try:
                    os.remove(full_path)
                except:
                    pass

    kill_zombie_processes()

    threading.Thread(target=run_backend, daemon=True).start()
    time.sleep(3) 
    threading.Thread(target=run_frontend, daemon=True).start()
    time.sleep(5) 
    
    print("WEBSOCKET LISTENING ON 0.0.0.0:8005 (Localhost Accessible)")
    print("[*] Launching Browser...")
    webbrowser.open("http://localhost:5175")
    
    print("\n[+] System Online. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        # Don't try to kill PID 0 here either
        kill_zombie_processes()
        sys.exit(0)

if __name__ == "__main__":
    main()