#!/usr/bin/env python3
"""
start.py - MDK4 Web Version Launcher
-----------------------------------
Menjalankan Flask web server untuk MDK4 (tanpa ngrok)
Akses dari perangkat lain di WiFi yang sama via IP
"""

import subprocess
import time
import signal
import sys
import os
import socket

# Warna
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

# ASCII Banner
BANNER = r"""
██████╗ ██╗  ██╗██╗  ██╗    ██╗    ██╗███████╗██████╗ 
██╔══██╗██║  ██║╚██╗██╔╝    ██║    ██║██╔════╝██╔══██╗
██║  ██║███████║ ╚███╔╝     ██║ █╗ ██║█████╗  ██████╔╝
██║  ██║██╔══██║ ██╔██╗     ██║███╗██║██╔══╝  ██╔══██╗
██████╔╝██║  ██║██╔╝ ██╗    ╚███╔███╔╝███████╗██████╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝     ╚══╝╚══╝ ╚══════╝╚═════╝ 
"""

def print_status(msg, status="info"):
    if status == "info":
        print(f"{CYAN}[*]{RESET} {msg}")
    elif status == "success":
        print(f"{GREEN}[+]{RESET} {msg}")
    elif status == "error":
        print(f"{RED}[-]{RESET} {msg}")
    elif status == "warning":
        print(f"{YELLOW}[!]{RESET} {msg}")
    elif status == "web":
        print(f"{MAGENTA}[🌐]{RESET} {msg}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"{MAGENTA}{BOLD}{BANNER}{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    print(f"{CYAN}  MDK4 Web Interface - Flask (Local Network){RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")

def get_local_ip():
    """Dapatkan IP lokal untuk akses dari perangkat lain"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"

def run_flask_as_sudo():
    """Jalankan Flask dengan sudo (karena butuh akses root)"""
    print_status("Starting Flask (app.py) with sudo...", "info")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    if not os.path.exists(app_path):
        print_status(f"app.py not found at: {app_path}", "error")
        return None
    
    try:
        flask_process = subprocess.Popen(
            ['sudo', 'python3', app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        time.sleep(3)
        
        try:
            import requests
            response = requests.get('http://localhost:5000', timeout=2)
            if response.status_code == 200:
                print_status("Flask running at http://localhost:5000", "success")
                return flask_process
        except:
            pass
            
        print_status("Flask starting (wait a few more seconds)...", "warning")
        time.sleep(3)
        return flask_process
        
    except Exception as e:
        print_status(f"Failed to start Flask: {e}", "error")
        return None

def main():
    print_banner()
    print_status("Starting MDK4 Web Interface...", "info")
    print()
    
    local_ip = get_local_ip()
    
    flask_process = run_flask_as_sudo()
    if not flask_process:
        print_status("Failed to start Flask!", "error")
        sys.exit(1)
    
    print()
    print(f"{GREEN}{'='*70}{RESET}")
    print(f"{MAGENTA}{BOLD}🌐 MDK4 WEB INTERFACE READY{RESET}")
    print(f"{GREEN}{BOLD}   Local URL   :{RESET} http://localhost:5000")
    print(f"{GREEN}{BOLD}   Network URL :{RESET} http://{local_ip}:5000")
    print()
    print(f"{YELLOW}📱 Buka di HP atau perangkat lain dalam WiFi yang sama:{RESET}")
    print(f"{CYAN}   http://{local_ip}:5000{RESET}")
    print()
    print(f"{YELLOW}💡 Tips:{RESET}")
    print(f"   - Pastikan perangkat terhubung ke WiFi yang sama")
    print(f"   - Matikan firewall jika perlu: sudo ufw disable")
    print(f"   - CTRL+Click URL di atas untuk buka di browser")
    print(f"{GREEN}{'='*70}{RESET}")
    print(f"{YELLOW}Press Ctrl+C to stop server{RESET}\n")
    
    def cleanup(sig, frame):
        print("\n[*] Stopping Flask...")
        try:
            flask_process.terminate()
            flask_process.wait(timeout=2)
        except:
            pass
        subprocess.run("sudo pkill -9 -f mdk4", shell=True, check=False)
        print("[+] Cleanup complete.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        while True:
            if flask_process.poll() is not None:
                print_status(f"Flask stopped! Exit code: {flask_process.returncode}", "error")
                print_status("Auto-restarting in 3 seconds...", "warning")
                time.sleep(3)
                flask_process = run_flask_as_sudo()
                if not flask_process:
                    print_status("Failed to restart Flask!", "error")
                    break
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == '__main__':
    main()