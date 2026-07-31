#!/usr/bin/env python3
import subprocess
import time
import threading
import signal
import sys
import json
import os
import requests

# Warna
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

def get_ngrok_url():
    """Ambil URL ngrok dari API"""
    for i in range(10):  # Coba 10 kali
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
    """Cek apakah ngrok terinstall"""
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
    """Setup ngrok authtoken untuk root"""
    token = "3GUfJCOMHBz1k0DzX7AoLRvn2NI_66DEZjqS3wLUrcZUzjwaZ"
    ngrok_path = check_ngrok()
    if not ngrok_path:
        return False
    
    # Cek apakah sudah ada token untuk root
    try:
        result = subprocess.run(['sudo', ngrok_path, 'config', 'check'], 
                              capture_output=True, text=True)
        if "Valid configuration" in result.stdout:
            print_status("Ngrok root sudah terkonfigurasi", "success")
            return True
    except:
        pass
    
    # Setup token untuk root
    print_status("Setup ngrok untuk root...", "info")
    try:
        subprocess.run(['sudo', ngrok_path, 'config', 'add-authtoken', token], check=True)
        print_status("Ngrok root berhasil di-setup", "success")
        return True
    except Exception as e:
        print_status(f"Gagal setup ngrok root: {e}", "error")
        return False

def run_flask_as_sudo():
    """Jalankan Flask dengan sudo (karena butuh akses root)"""
    print_status("Menjalankan Flask (app.py) dengan sudo...", "info")
    
    try:
        # Jalankan Flask dengan sudo
        flask_process = subprocess.Popen(
            ['sudo', 'python3', 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Tunggu sebentar
        time.sleep(3)
        
        # Cek apakah Flask berjalan
        try:
            response = requests.get('http://localhost:5000', timeout=2)
            if response.status_code == 200:
                print_status("Flask berjalan di http://localhost:5000", "success")
                return flask_process
        except:
            pass
            
        print_status("Flask berjalan (tunggu beberapa detik lagi)...", "warning")
        time.sleep(3)
        return flask_process
        
    except Exception as e:
        print_status(f"Gagal jalankan Flask: {e}", "error")
        return None

def main():
    print_status("Starting Deauth Web Interface...", "info")
    
    # Setup ngrok untuk root
    setup_ngrok_root()
    
    # Jalankan Flask
    flask_process = run_flask_as_sudo()
    if not flask_process:
        print_status("Gagal menjalankan Flask!", "error")
        sys.exit(1)
    
    # Jalankan ngrok
    ngrok_path = check_ngrok()
    if not ngrok_path:
        print_status("Ngrok tidak ditemukan!", "error")
        print_status("Flask tetap berjalan di http://localhost:5000", "warning")
        print_status("Tekan Ctrl+C untuk berhenti.", "info")
        
        try:
            while True:
                time.sleep(1)
                if flask_process.poll() is not None:
                    print_status("Flask mati!", "error")
                    break
        except KeyboardInterrupt:
            pass
        finally:
            flask_process.terminate()
            sys.exit(0)
    
    print_status(f"Menjalankan ngrok dari: {ngrok_path}", "info")
    
    try:
        # Jalankan ngrok (tanpa sudo karena config sudah di-setup)
        ngrok_process = subprocess.Popen(
            [ngrok_path, 'http', '5000'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print_status("Ngrok berjalan di background", "success")
    except Exception as e:
        print_status(f"Gagal jalankan ngrok: {e}", "error")
        flask_process.terminate()
        sys.exit(1)
    
    # Tunggu ngrok siap
    print_status("Menunggu ngrok siap...", "info")
    time.sleep(5)
    
    # Ambil URL
    url = get_ngrok_url()
    if url:
        print("\n" + "="*70)
        print(f"{GREEN}{BOLD}[+] URL PUBLIK (bisa diakses dari mana saja):{RESET}")
        print(f"{GREEN}{BOLD}    {url}{RESET}")
        print("="*70)
        print("\n[*] Copy URL di atas untuk diakses dari HP atau luar negeri.")
        print("[*] Tekan Ctrl+C untuk menghentikan semuanya.\n")
    else:
        print_status("Gagal mendapatkan URL ngrok.", "error")
        print_status("Coba jalankan manual:", "warning")
        print_status("  Terminal 1: sudo python3 app.py", "info")
        print_status("  Terminal 2: ngrok http 5000", "info")
        print_status("Flask tetap berjalan di http://localhost:5000", "info")
    
    # Cleanup saat Ctrl+C
    def cleanup(sig, frame):
        print("\n[*] Matikan semua proses...")
        try:
            ngrok_process.terminate()
            ngrok_process.wait(timeout=2)
        except:
            pass
        try:
            flask_process.terminate()
            flask_process.wait(timeout=2)
        except:
            pass
        # Matikan juga sisa proses
        subprocess.run("sudo pkill -f 'aireplay-ng'", shell=True, check=False)
        subprocess.run("sudo pkill -f 'airodump-ng'", shell=True, check=False)
        print("[+] Selesai.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Loop sampai user Ctrl+C
    try:
        while True:
            # Cek apakah flask masih jalan
            if flask_process.poll() is not None:
                print_status(f"Flask mati! Exit code: {flask_process.returncode}", "error")
                print_status("Restart otomatis dalam 3 detik...", "warning")
                time.sleep(3)
                flask_process = run_flask_as_sudo()
                if not flask_process:
                    print_status("Gagal restart Flask!", "error")
                    break
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == '__main__':
    main()