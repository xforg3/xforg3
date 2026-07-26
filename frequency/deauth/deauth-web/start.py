#!/usr/bin/env python3
import subprocess
import time
import signal
import sys
import os
import requests

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_status(msg, status="info"):
    if status == "info":
        print(f"{CYAN}[*]{RESET} {msg}")
    elif status == "success":
        print(f"{GREEN}[+]{RESET} {msg}")
    elif status == "error":
        print(f"{RED}[-]{RESET} {msg}")
    elif status == "warning":
        print(f"{YELLOW}[!]{RESET} {msg}")

def check_dependencies():
    """Cek dependencies yang dibutuhkan"""
    deps = {
        'mdk4': 'sudo apt install mdk4 -y',
        'aircrack-ng': 'sudo apt install aircrack-ng -y',
        'iwconfig': 'sudo apt install wireless-tools -y'
    }
    
    missing = []
    for cmd, install in deps.items():
        try:
            subprocess.run(['which', cmd], capture_output=True, check=True)
            print_status(f"{cmd} OK", "success")
        except:
            print_status(f"{cmd} MISSING", "error")
            missing.append(install)
    
    if missing:
        print_status("Install missing packages:", "warning")
        for m in missing:
            print(f"  {m}")
        return False
    return True

def install_mdk4():
    """Auto install MDK4"""
    try:
        subprocess.run(['which', 'mdk4'], capture_output=True, check=True)
        return True
    except:
        print_status("Installing MDK4...", "info")
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=False, capture_output=True)
            subprocess.run(['sudo', 'apt', 'install', 'mdk4', '-y'], check=True, capture_output=True)
            print_status("MDK4 installed!", "success")
            return True
        except:
            print_status("Failed to install MDK4", "error")
            return False

def check_ngrok():
    """Cek ngrok"""
    try:
        subprocess.run(['which', 'ngrok'], capture_output=True, check=True)
        return True
    except:
        return False

def get_ngrok_url():
    """Ambil URL ngrok"""
    for i in range(10):
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
            if response.status_code == 200:
                data = response.json()
                for tunnel in data['tunnels']:
                    if tunnel['proto'] == 'https':
                        return tunnel['public_url']
        except:
            pass
        time.sleep(1)
    return None

def run_flask():
    """Jalankan Flask dengan sudo"""
    print_status("Starting Flask (app.py)...", "info")
    
    try:
        process = subprocess.Popen(
            ['sudo', 'python3', 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Tunggu Flask siap
        time.sleep(3)
        
        # Cek apakah berjalan
        try:
            response = requests.get('http://localhost:5000', timeout=2)
            if response.status_code == 200:
                print_status("Flask running on http://localhost:5000", "success")
                return process
        except:
            pass
        
        print_status("Flask starting...", "warning")
        time.sleep(3)
        return process
        
    except Exception as e:
        print_status(f"Failed to start Flask: {e}", "error")
        return None

def run_ngrok():
    """Jalankan ngrok"""
    if not check_ngrok():
        print_status("ngrok not found", "warning")
        return None
    
    print_status("Starting ngrok...", "info")
    try:
        process = subprocess.Popen(
            ['ngrok', 'http', '5000'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        
        url = get_ngrok_url()
        if url:
            print("\n" + "="*70)
            print(f"{GREEN}{BOLD}[+] PUBLIC URL:{RESET}")
            print(f"{GREEN}{BOLD}    {url}{RESET}")
            print("="*70)
            print("\n[*] Copy URL untuk akses dari luar")
        else:
            print_status("Failed to get ngrok URL", "error")
        
        return process
    except Exception as e:
        print_status(f"Failed to start ngrok: {e}", "error")
        return None

def cleanup(flask_process, ngrok_process):
    """Cleanup semua proses"""
    print("\n[*] Cleaning up...")
    
    # Matikan deauth
    subprocess.run("sudo pkill -f 'mdk4'", shell=True, check=False)
    subprocess.run("sudo pkill -f 'aireplay-ng'", shell=True, check=False)
    
    # Matikan Flask
    if flask_process:
        try:
            flask_process.terminate()
            flask_process.wait(timeout=2)
        except:
            pass
    
    # Matikan ngrok
    if ngrok_process:
        try:
            ngrok_process.terminate()
            ngrok_process.wait(timeout=2)
        except:
            pass
    
    print("[+] Cleanup complete.")

def main():
    print_status("NODE_01 - DEAUTH CONTROLLER", "info")
    print_status("=" * 40, "info")
    
    # Cek dependencies
    print_status("Checking dependencies...", "info")
    if not check_dependencies():
        print_status("Install missing dependencies and try again", "error")
        sys.exit(1)
    
    # Install MDK4
    if not install_mdk4():
        print_status("MDK4 required! Install manually: sudo apt install mdk4", "error")
        sys.exit(1)
    
    # Jalankan Flask
    flask_process = run_flask()
    if not flask_process:
        sys.exit(1)
    
    # Jalankan ngrok
    ngrok_process = run_ngrok()
    
    print("\n[*] Local: http://localhost:5000")
    print("[*] Press Ctrl+C to stop\n")
    
    # Signal handler
    def signal_handler(sig, frame):
        cleanup(flask_process, ngrok_process)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Monitor
    try:
        while True:
            if flask_process.poll() is not None:
                print_status("Flask crashed! Restarting...", "warning")
                time.sleep(3)
                flask_process = run_flask()
                if not flask_process:
                    print_status("Failed to restart Flask!", "error")
                    break
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == '__main__':
    main()