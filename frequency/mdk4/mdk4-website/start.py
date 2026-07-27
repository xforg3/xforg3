#!/usr/bin/env python3
"""
start.py - MDK4 Web Version Launcher
-----------------------------------
1. Pilih interface dulu (interaktif)
2. Setup monitor mode
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

# Warna
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
    """Cari semua interface wireless"""
    try:
        result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        interfaces = []
        for line in lines:
            if "no wireless extensions" in line or not line.strip():
                continue
            if not line.startswith(" "):
                iface = line.split()[0]
                # Skip ethernet, loopback
                if iface not in ["lo", "eth0", "eth1", "enp0s3", "enp0s8", "docker0"]:
                    interfaces.append(iface)
        return interfaces
    except Exception as e:
        print_status(f"Error finding interfaces: {e}", "error")
        return []

def is_monitor_mode(iface):
    """Cek apakah interface dalam mode monitor"""
    try:
        result = subprocess.run(["iwconfig", iface], capture_output=True, text=True, timeout=3)
        return "Mode:Monitor" in result.stdout
    except:
        return False

def get_interface_info(iface):
    """Dapatkan info tambahan tentang interface"""
    info = {
        "name": iface,
        "monitor": is_monitor_mode(iface),
        "phy": "?"
    }
    
    # Coba dapatkan PHY
    try:
        result = subprocess.run(["iw", "dev", iface, "info"], capture_output=True, text=True, timeout=2)
        for line in result.stdout.split('\n'):
            if "wiphy" in line:
                info["phy"] = line.strip()
                break
    except:
        pass
    
    return info

def select_interface_interactive():
    """Tampilkan menu interaktif untuk pilih interface"""
    clear_screen()
    print_banner()
    
    print(f"{BOLD}{CYAN}📡 WIRELESS INTERFACE SELECTION{RESET}")
    print(f"{GREEN}{'='*50}{RESET}\n")
    
    # Scan interfaces
    print_status("Scanning wireless interfaces...", "info")
    interfaces = find_wireless_interfaces()
    
    if not interfaces:
        print_status("No wireless interfaces found!", "error")
        print_status("Please plug in WiFi adapter and try again.", "warning")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Tampilkan daftar interface dengan info
    print(f"\n{BOLD}Available interfaces:{RESET}\n")
    print(f"  {'No':<4} {'Interface':<15} {'Mode':<12} {'PHY'}")
    print(f"  {GREEN}{'-'*50}{RESET}")
    
    interface_list = []
    for idx, iface in enumerate(interfaces, 1):
        info = get_interface_info(iface)
        mode = f"{GREEN}Monitor{RESET}" if info["monitor"] else f"{YELLOW}Managed{RESET}"
        phy = info["phy"][:20] if info["phy"] != "?" else "?"
        print(f"  {CYAN}{idx:<4}{RESET} {iface:<15} {mode:<12} {phy}")
        interface_list.append(iface)
    
    print(f"  {GREEN}{'-'*50}{RESET}")
    
    # Pilihan
    print(f"\n  {BOLD}Options:{RESET}")
    print(f"  {CYAN}0{RESET}  Exit")
    print(f"  {CYAN}r{RESET}  Refresh interfaces")
    print(f"  {CYAN}m{RESET}  Create monitor mode from selected interface")
    
    while True:
        try:
            choice = input(f"\n{BOLD}{YELLOW}Select interface number (1-{len(interface_list)}): {RESET}").strip()
            
            if choice.lower() == '0':
                print_status("Exiting...", "info")
                sys.exit(0)
            elif choice.lower() == 'r':
                return select_interface_interactive()
            elif choice.lower() == 'm':
                print_status("You can create monitor mode in the web interface", "info")
                print_status("Or manually: sudo airmon-ng start <interface>", "info")
                continue
            
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(interface_list):
                    selected = interface_list[num - 1]
                    return selected
                else:
                    print_status(f"Please enter number between 1 and {len(interface_list)}", "error")
            else:
                print_status("Invalid input! Enter number or 0 to exit.", "error")
                
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted, exiting...{RESET}")
            sys.exit(0)

# ====================== MONITOR MODE SETUP ======================

def setup_monitor_mode(interface):
    """Setup monitor mode untuk interface yang dipilih"""
    clear_screen()
    print_banner()
    
    print(f"{BOLD}{CYAN}📡 SETUP MONITOR MODE{RESET}")
    print(f"{GREEN}{'='*50}{RESET}\n")
    
    # Cek apakah udah monitor
    if is_monitor_mode(interface):
        print_status(f"Interface {interface} is already in monitor mode! ✅", "success")
        return interface
    
    print_status(f"Interface: {interface} is in MANAGED mode", "warning")
    print_status(f"Creating monitor mode on {interface}...", "info")
    
    try:
        # Kill interfering processes
        print_status("Killing interfering processes...", "info")
        subprocess.run(["sudo", "airmon-ng", "check", "kill"], check=False, timeout=5)
        
        # Start monitor mode
        result = subprocess.run(
            ["sudo", "airmon-ng", "start", interface],
            capture_output=True, text=True, timeout=10
        )
        
        # Cari nama interface monitor baru
        monitor_iface = None
        for line in result.stdout.split('\n'):
            if "monitor mode enabled on" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "on" and i+1 < len(parts):
                        monitor_iface = parts[i+1].strip()
                        break
        
        if monitor_iface:
            print_status(f"✅ Monitor mode created: {monitor_iface}", "success")
            time.sleep(1)
            return monitor_iface
        
        # Fallback: cari interface yang berakhir "mon"
        interfaces = find_wireless_interfaces()
        for iface in interfaces:
            if iface.endswith("mon") and iface != interface:
                print_status(f"✅ Found monitor interface: {iface}", "success")
                return iface
        
        print_status("Failed to find monitor interface!", "error")
        print_status(f"Try manually: sudo airmon-ng start {interface}", "info")
        return None
        
    except Exception as e:
        print_status(f"Error creating monitor mode: {e}", "error")
        return None

# ====================== NGROK FUNCTIONS ======================

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

# ====================== RUN APP ======================

def print_app_output(process):
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"{CYAN}[FastAPI]{RESET} {line.strip()}")
    except Exception as e:
        pass

def run_app_with_interface(interface):
    """Jalankan FastAPI dengan interface yang sudah dipilih"""
    print_status(f"Starting FastAPI with interface: {interface}", "info")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    if not os.path.exists(app_path):
        print_status(f"app.py not found at: {app_path}", "error")
        return None
    
    # 🔥 Set environment variable biar app.py tau interface yang dipilih
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

# ====================== MAIN ======================

def main():
    # 1. Pilih interface
    selected_interface = select_interface_interactive()
    print_status(f"Selected interface: {selected_interface}", "success")
    
    # 2. Setup monitor mode
    monitor_iface = setup_monitor_mode(selected_interface)
    if not monitor_iface:
        print_status("Failed to setup monitor mode!", "error")
        print_status("You can still continue, but scan may not work properly.", "warning")
        monitor_iface = selected_interface
    
    # 3. Setup ngrok
    setup_ngrok_root()
    
    # 4. Jalankan app
    app_process = run_app_with_interface(monitor_iface)
    if not app_process:
        print_status("Failed to start FastAPI!", "error")
        sys.exit(1)
    
    # 5. Jalankan ngrok
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
    print(f"{MAGENTA}{BOLD}🌐 MDK4 WEB INTERFACE READY{RESET}")
    print(f"{GREEN}{BOLD}   Interface  :{RESET} {monitor_iface}")
    print(f"{GREEN}{BOLD}   Local URL  :{RESET} http://localhost:5000")
    if url:
        print(f"{GREEN}{BOLD}   Public URL :{RESET} {url}")
    else:
        print(f"{RED}{BOLD}   Public URL :{RESET} Failed to get ngrok URL")
    
    print()
    if url:
        print(f"{YELLOW}📱 Buka URL di HP atau dari mana saja!{RESET}")
    else:
        print(f"{YELLOW}📱 Buka di HP (WiFi yang sama):{RESET}")
        # Dapatkan IP lokal
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            print(f"{CYAN}   http://{ip}:5000{RESET}")
        except:
            pass
    
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
        
        # Stop monitor mode
        print(f"[*] Stopping monitor mode on {monitor_iface}...")
        subprocess.run(["sudo", "airmon-ng", "stop", monitor_iface], check=False, timeout=3)
        subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False, timeout=3)
        
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
                app_process = run_app_with_interface(monitor_iface)
                if not app_process:
                    print_status("Failed to restart FastAPI!", "error")
                    break
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == '__main__':
    main()