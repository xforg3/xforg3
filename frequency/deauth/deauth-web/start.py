import subprocess
import time
import threading
import signal
import sys
import json
import os
import requests

# ===== FUNGSI AMBIL URL NGROK =====
def get_ngrok_url():
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
        data = response.json()
        for tunnel in data['tunnels']:
            if tunnel['proto'] == 'https':
                return tunnel['public_url']
    except Exception as e:
        return None
    return None

# ===== CEK NGROK TERINSTALL =====
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

# ===== MAIN =====
def main():
    print("[*] Menjalankan Flask (app.py) ...")
    
    # Jalankan app.py sebagai subprocess (bukan di-import)
    try:
        flask_process = subprocess.Popen(
            ['python3', 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print("[+] Flask berjalan di background")
    except Exception as e:
        print(f"[-] Gagal jalankan Flask: {e}")
        return

    # Tunggu Flask siap
    print("[*] Menunggu Flask siap...")
    time.sleep(5)

    # Cek ngrok
    ngrok_path = check_ngrok()
    if not ngrok_path:
        print("[-] Ngrok tidak ditemukan!")
        print("[*] Install ngrok: sudo apt install ngrok")
        print("[*] Atau download dari https://ngrok.com/download")
        print("\n[*] Flask tetap berjalan di http://localhost:5000")
        print("[*] Tekan Ctrl+C untuk berhenti.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Matikan Flask...")
            flask_process.terminate()
            sys.exit(0)
        return

    print(f"[*] Menjalankan ngrok dari: {ngrok_path}")
    
    # Jalankan ngrok
    try:
        ngrok_process = subprocess.Popen(
            [ngrok_path, 'http', '5000'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("[+] Ngrok berjalan di background")
    except Exception as e:
        print(f"[-] Gagal jalankan ngrok: {e}")
        flask_process.terminate()
        return

    # Tunggu ngrok siap
    print("[*] Menunggu ngrok siap...")
    time.sleep(4)

    # Ambil URL
    url = get_ngrok_url()
    if url:
        print("\n" + "="*70)
        print("[+] URL PUBLIK (bisa diakses dari mana saja):")
        print(f"    {url}")
        print("="*70)
        print("\n[*] Copy URL di atas untuk diakses dari HP atau luar negeri.")
        print("[*] Tekan Ctrl+C untuk menghentikan semuanya.\n")
    else:
        print("[-] Gagal mendapatkan URL ngrok.")
        print("[*] Cek apakah ngrok sudah di-setup dengan benar.")
        print("[*] Jalankan: ngrok config add-authtoken <TOKEN>")
        print("[*] Flask tetap berjalan di http://localhost:5000")

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
        print("[+] Selesai.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Loop sampai user Ctrl+C
    try:
        while True:
            # Cek apakah flask masih jalan
            if flask_process.poll() is not None:
                print("[-] Flask mati! Exit code:", flask_process.returncode)
                print("[*] Restart otomatis dalam 3 detik...")
                time.sleep(3)
                flask_process = subprocess.Popen(
                    ['python3', 'app.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                print("[+] Flask restart berhasil")
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == '__main__':
    main()
