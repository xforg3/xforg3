#!/usr/bin/env python3
"""
start.py - MDK4 Web Version Launcher
-----------------------------------
1. Pilih interface wireless (interaktif)
2. Setup monitor mode via airmon-ng
3. Jalankan FastAPI + Ngrok
"""

import subprocess
import time
import threading
import signal
import sys
import requests
import os
import re

# Warna ANSI
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

# ====================== INTERFACE FUNCTIONS ======================

def find_wireless_interfaces():
    """Cari semua interface wireless murni (mengabaikan lo, eth, docker, dll)"""
    interfaces = set()
    
    # Method 1: iw dev
    try:
        result = subprocess.run(["iw", "dev"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("Interface"):
                parts = line.split()
                if len(parts) > 1:
                    interfaces.add(parts[1])
    except Exception:
        pass
    
    # Method 2: iwconfig fallback
    try:
        result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            if "no wireless extensions" in line or not line.strip():
                continue
            if not line.startswith(" "):
                iface = line.split()[0]
                interfaces.add(iface)
    except Exception:
        pass

    # Verifikasi akhir untuk memastikan interface benar-benar wireless
    verified_ifaces = []
    for iface in sorted(list(interfaces)):
        # Abaikan interface non-wireless biasa
        if iface in ["lo", "eth0", "eth1", "docker0"]:
            continue
        
        try:
            res = subprocess.run(["iwconfig", iface], capture_output=True, text=True, timeout=2)
            if "no wireless extensions" not in res.stdout:
                verified_ifaces.append(iface)
        except Exception:
            pass

    return verified_ifaces

def is_monitor_mode(iface):
    """Cek apakah interface berada dalam Mode:Monitor"""
    try:
        result = subprocess.run(["iwconfig", iface], capture_output=True, text=True, timeout=3)
        return "Mode:Monitor" in result.stdout
    except Exception:
        return False

def get_interface_info(iface):
    """Dapatkan informasi detail interface (mode, state, PHY)"""
    info = {
        "name": iface,
        "monitor": is_monitor_mode(iface),
        "phy": "?",
        "state": "unknown"
    }
    
    # Ambil info PHY
    try:
        result = subprocess.run(["iw", "dev", iface, "info"], capture_output=True, text=True, timeout=2)
        for line in result.stdout.split('\n'):
            if "wiphy" in line:
                info["phy"] = line.strip()
            if "type" in line:
                mode_type = line.split()[-1]
                if mode_type == "monitor":
                    info["monitor"] = True
    except Exception:
        pass
    
    # Ambil state dari ip link
    try:
        result = subprocess.run(["ip", "link", "show", iface], capture_output=True, text=True, timeout=2)
        if "state UP" in result.stdout or "<UP" in result.stdout:
            info["state"] = "UP"
        elif "state DOWN" in result.stdout:
            info["state"] = "DOWN"
    except Exception:
        pass
    
    return info

def select_interface_interactive():
    """Tampilkan menu interaktif untuk memilih interface"""
    print_banner()
    print(f"{BOLD}{CYAN}📡 WIRELESS INTERFACE SELECTION{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")
    
    print_status("Scanning wireless interfaces...", "info")
    interfaces = find_wireless_interfaces()
    
    if not interfaces:
        print_status("No wireless interfaces found!", "error")
        print_status("Please connect a Wi-Fi adapter and try again.", "warning")
        print_status("Check manually with: ip link && iw dev", "info")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print(f"\n{BOLD}Available interfaces:{RESET}\n")
    print(f"  {'No':<4} {'Interface':<18} {'Mode':<12} {'State':<8} {'PHY'}")
    print(f"  {GREEN}{'-'*70}{RESET}")
    
    interface_list = []
    for idx, iface in enumerate(interfaces, 1):
        info = get_interface_info(iface)
        mode = f"{GREEN}Monitor{RESET}" if info["monitor"] else f"{YELLOW}Managed{RESET}"
        state = f"{GREEN}UP{RESET}" if info["state"] == "UP" else f"{RED}DOWN{RESET}"
        phy = info["phy"][:20] if info["phy"] != "?" else "?"
        print(f"  {CYAN}{idx:<4}{RESET} {iface:<18} {mode:<12} {state:<8} {phy}")
        interface_list.append(iface)
    
    print(f"  {GREEN}{'-'*70}{RESET}")
    
    print(f"\n  {BOLD}Options:{RESET}")
    print(f"  {CYAN}0{RESET}  Exit")
    print(f"  {CYAN}r{RESET}  Refresh interfaces")
    print(f"  {CYAN}m{RESET}  Manual monitor mode info")
    
    while True:
        try:
            choice = input(f"\n{BOLD}{YELLOW}Select interface number (1-{len(interface_list)}): {RESET}").strip()
            
            if choice.lower() == '0':
                print_status("Exiting...", "info")
                sys.exit(0)
            elif choice.lower() == 'r':
                return select_interface_interactive()
            elif choice.lower() == 'm':
                print_status("Manual setup command: sudo airmon-ng start <interface>", "info")
                continue
            
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(interface_list):
                    return interface_list[num - 1]
                else:
                    print_status(f"Please enter a number between 1 and {len(interface_list)}", "error")
            else:
                print_status("Invalid input!", "error")
                
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted, exiting...{RESET}")
            sys.exit(0)

# ====================== MONITOR MODE SETUP ======================

def setup_monitor_mode(interface):
    """Setup monitor mode pada interface"""
    print_banner()
    print(f"{BOLD}{CYAN}📡 SETUP MONITOR MODE{RESET}")
    print(f"{GREEN}{'='*50}{RESET}\n")
    
    if is_monitor_mode(interface):
        print_status(f"Interface {interface} is already in monitor mode! ✅", "success")
        return interface
    
    print_status(f"Interface {interface} is in MANAGED mode", "warning")
    print_status(f"Enabling monitor mode on {interface}...", "info")
    
    try:
        print_status("Killing interfering processes (airmon-ng check kill)...", "info")
        subprocess.run(["sudo", "airmon-ng", "check", "kill"], check=False, timeout=10)
        
        result = subprocess.run(
            ["sudo", "airmon-ng", "start", interface],
            capture_output=True, text=True, timeout=15
        )
        
        # Cari nama interface monitor yang terbentuk
        monitor_iface = None
        for line in result.stdout.split('\n'):
            if "monitor mode enabled on" in line or "monitor mode vif enabled on" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part in ["on", "for"] and i + 1 < len(parts):
                        monitor_iface = parts[i+1].strip("]")
                        break
        
        if monitor_iface:
            print_status(f"✅ Monitor mode enabled: {monitor_iface}", "success")
            time.sleep(1)
            return monitor_iface
        
        # Fallback check
        current_ifaces = find_wireless_interfaces()
        for iface in current_ifaces:
            if iface.endswith("mon") or is_monitor_mode(iface):
                print_status(f"✅ Active monitor interface found: {iface}", "success")
                return iface
        
        print_status("Failed to verify monitor mode automatically.", "error")
        return interface
        
    except Exception as e:
        print_status(f"Error enabling monitor mode: {e}", "error")
        return interface

# ====================== NGROK & APP FUNCTIONS ======================

def check_ngrok():
    ngrok_paths = ['/usr/local/bin/ngrok', '/usr/bin/ngrok', 'ngrok']
    for path in ngrok_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return path
        except Exception:
            continue
    return None

def setup_ngrok_root():
    token = "3GUfJCOMHBz1k0DzX7AoLRvn2NI_66DEZjqS3wLUrcZUzjwaZ"
    ngrok_path = check_ngrok()
    if not ngrok_path:
        return False
    
    try:
        result = subprocess.run(['sudo', ngrok_path, 'config', 'check'], capture_output=True, text=True)
        if "Valid configuration" in result.stdout:
            print_status("Ngrok root already configured", "success")
            return True
    except Exception:
        pass
    
    print_status("Setting up ngrok token for root...", "info")
    try:
        subprocess.run(['sudo', ngrok_path, 'config', 'add-authtoken', token], check=True)
        print_status("Ngrok setup complete", "success")
        return True
    except Exception as e:
        print_status(f"Failed to setup ngrok authtoken: {e}", "error")
        return False

def get_ngrok_url():
    for _ in range(10):
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
            if response.status_code == 200:
                data = response.json()
                for tunnel in data.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        return tunnel.get('public_url')
        except Exception:
            pass
        time.sleep(1)
    return None

def print_app_output(process):
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"{CYAN}[FastAPI]{RESET} {line.strip()}")
    except Exception:
        pass

def run_app_with_interface(interface):
    print_status(f"Starting FastAPI server with interface: {interface}", "info")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    if not os.path.exists(app_path):
        print_status(f"app.py not found at: {app_path}", "error")
        return None
    
    env = os.environ.copy()
    env["MDK4_INTERFACE"] = interface
    
    try:
        app_process = subprocess.Popen(
            ['sudo', 'python3', app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        
        thread = threading.Thread(target=print_app_output, args=(app_process,))
        thread.daemon = True
        thread.start()
        
        print_status("Waiting for FastAPI to initialize...", "info")
        time.sleep(3)
        return app_process
        
    except Exception as e:
        print_status(f"Failed to launch app.py: {e}", "error")
        return None

# ====================== MAIN EXECUTION ======================

def main():
    # 1. Select Interface
    selected_interface = select_interface_interactive()
    print_status(f"Selected interface: {selected_interface}", "success")
    
    # 2. Setup Monitor Mode
    monitor_iface = setup_monitor_mode(selected_interface)
    
    # 3. Setup Ngrok Auth
    setup_ngrok_root()
    
    # 4. Run App
    app_process = run_app_with_interface(monitor_iface)
    if not app_process:
        print_status("Cannot proceed without FastAPI app. Exiting.", "error")
        sys.exit(1)
    
    # 5. Run Ngrok
    ngrok_path = check_ngrok()
    ngrok_process = None
    url = None
    
    if ngrok_path:
        try:
            ngrok_process = subprocess.Popen(
                [ngrok_path, 'http', '5000'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print_status("Ngrok process started", "success")
            time.sleep(3)
            url = get_ngrok_url()
        except Exception as e:
            print_status(f"Failed to start Ngrok: {e}", "error")
    else:
        print_status("Ngrok binary not found! Running in local-only mode.", "warning")

    # Display Information Banner
    print()
    print(f"{GREEN}{'='*70}{RESET}")
    print(f"{MAGENTA}{BOLD}🌐 MDK4 WEB INTERFACE READY{RESET}")
    print(f"{GREEN}{BOLD}   Interface  :{RESET} {monitor_iface}")
    print(f"{GREEN}{BOLD}   Local URL  :{RESET} http://localhost:5000")
    if url:
        print(f"{GREEN}{BOLD}   Public URL :{RESET} {url}")
    print(f"{GREEN}{'='*70}{RESET}")
    print(f"{YELLOW}Press Ctrl+C to exit and cleanup{RESET}\n")

    # Cleanup Handler
    def cleanup(sig, frame):
        print("\n[*] Shutting down services...")
        if ngrok_process:
            try:
                ngrok_process.terminate()
            except Exception:
                pass
        if app_process:
            try:
                app_process.terminate()
            except Exception:
                pass
        
        print(f"[*] Stopping monitor mode on {monitor_iface}...")
        subprocess.run(["sudo", "airmon-ng", "stop", monitor_iface], check=False, timeout=5)
        subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False, timeout=5)
        subprocess.run("sudo pkill -f mdk4", shell=True, check=False)
        
        print("[+] Cleanup complete. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Monitor App Loop
    try:
        while True:
            if app_process.poll() is not None:
                print_status("FastAPI process exited unexpectedly.", "error")
                break
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == '__main__':
    main()