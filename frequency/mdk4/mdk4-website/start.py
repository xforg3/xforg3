#!/usr/bin/env python3
import subprocess
import time
import threading
import signal
import sys
import requests
import os

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"{MAGENTA}{BOLD}{BANNER}{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    print(f"{CYAN}  MDK4 Web Interface - FastAPI + Ngrok{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")

def get_ngrok_url():
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

def check_ngrok():
    ngrok_paths = ['/usr/local/bin/ngrok', '/usr/bin/ngrok', 'ngrok']
    for path in ngrok_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                return path
        except:
            continue
    return None

def setup_ngrok_root():
    token = "3GUfJCOMHBz1k0DzX7AoLRvn2NI_66DEZjqS3wLUrcZUzjwaZ"
    ngrok_path = check_ngrok()
    if not ngrok_path:
        return False
    
    try:
        result = subprocess.run(['sudo', ngrok_path, 'config', 'check'], 
                              capture_output=True, text=True)
        if "Valid configuration" in result.stdout:
            print_status("Ngrok root already configured", "success")
            return True
    except:
        pass
    
    print_status("Setting up ngrok for root...", "info")
    try:
        subprocess.run(['sudo', ngrok_path, 'config', 'add-authtoken', token], check=True)
        print_status("Ngrok root setup complete", "success")
        return True
    except Exception as e:
        print_status(f"Failed to setup ngrok: {e}", "error")
        return False

def print_app_output(process):
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"{CYAN}[FastAPI]{RESET} {line.strip()}")
    except Exception as e:
        print(f"[-] Error reading output: {e}")

def run_app_as_sudo():
    print_status("Starting FastAPI (app.py) with sudo...", "info")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    if not os.path.exists(app_path):
        print_status(f"app.py not found at: {app_path}", "error")
        return None
    
    try:
        app_process = subprocess.Popen(
            ['sudo', 'python3', app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        thread = threading.Thread(target=print_app_output, args=(app_process,))
        thread.daemon = True
        thread.start()
        
        print_status("Waiting for FastAPI to be ready...", "info")
        time.sleep(5)
        
        for i in range(5):
            try:
                response = requests.get('http://localhost:5000/api/interfaces', timeout=2)
                if response.status_code == 200:
                    print_status("FastAPI running at http://localhost:5000", "success")
                    return app_process
            except:
                pass
            time.sleep(1)
            
        print_status("FastAPI might be starting, continuing...", "warning")
        return app_process
        
    except Exception as e:
        print_status(f"Failed to start FastAPI: {e}", "error")
        return None

def main():
    print_banner()
    print_status("Starting MDK4 Web Interface (FastAPI)...", "info")
    
    setup_ngrok_root()
    
    app_process = run_app_as_sudo()
    if not app_process:
        print_status("Failed to start FastAPI!", "error")
        sys.exit(1)
    
    ngrok_path = check_ngrok()
    if not ngrok_path:
        print_status("Ngrok not found!", "error")
        print_status("FastAPI still running at http://localhost:5000", "warning")
        print_status("Press Ctrl+C to stop.", "info")
        
        try:
            while True:
                time.sleep(1)
                if app_process.poll() is not None:
                    print_status("FastAPI stopped!", "error")
                    break
        except KeyboardInterrupt:
            pass
        finally:
            app_process.terminate()
            sys.exit(0)
    
    print_status(f"Running ngrok from: {ngrok_path}", "info")
    
    try:
        ngrok_process = subprocess.Popen(
            [ngrok_path, 'http', '5000'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print_status("Ngrok running in background", "success")
    except Exception as e:
        print_status(f"Failed to run ngrok: {e}", "error")
        app_process.terminate()
        sys.exit(1)
    
    print_status("Waiting for ngrok to be ready...", "info")
    time.sleep(5)
    
    url = get_ngrok_url()
    
    print()
    print(f"{GREEN}{'='*70}{RESET}")
    if url:
        print(f"{MAGENTA}{BOLD}🌐 MDK4 WEB INTERFACE READY{RESET}")
        print(f"{GREEN}{BOLD}   Local URL :{RESET} http://localhost:5000")
        print(f"{GREEN}{BOLD}   Public URL:{RESET} {url}")
        print()
        print(f"{YELLOW}📱 Buka URL di HP atau dari mana saja!{RESET}")
    else:
        print(f"{RED}{BOLD}⚠️ Failed to get ngrok URL{RESET}")
        print(f"{YELLOW}📡 FastAPI running at: http://localhost:5000{RESET}")
    
    print(f"{GREEN}{'='*70}{RESET}")
    print(f"{YELLOW}Press Ctrl+C to stop everything{RESET}\n")
    
    def cleanup(sig, frame):
        print("\n[*] Stopping all processes...")
        try:
            ngrok_process.terminate()
            ngrok_process.wait(timeout=2)
        except:
            pass
        try:
            app_process.terminate()
            app_process.wait(timeout=2)
        except:
            pass
        subprocess.run("sudo pkill -f mdk4", shell=True, check=False)
        print("[+] Cleanup complete.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        while True:
            if app_process.poll() is not None:
                print_status(f"FastAPI stopped! Exit code: {app_process.returncode}", "error")
                print_status("Auto-restarting in 3 seconds...", "warning")
                time.sleep(3)
                app_process = run_app_as_sudo()
                if not app_process:
                    print_status("Failed to restart FastAPI!", "error")
                    break
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == '__main__':
    main()