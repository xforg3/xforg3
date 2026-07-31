#!/usr/bin/env python3
"""
frequency.py - Frequency Menu
---------------------------------
Menu untuk mengakses BETTERCAP, DEAUTH, MDK4, dan AIRGEDDON
"""

import os
import sys
import shutil
import time

# ---------- ANSI ----------
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "purple": "\033[95m",
    "white": "\033[97m",
    "magenta": "\033[35m",
}

BOX_WIDTH = 44  # lebar isi box (di antara ╔...╗)

# ================= Util =================

def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def draw_box_top():
    print(f"\n{COLORS['yellow']}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")

def draw_box_bottom():
    print(f"{COLORS['yellow']}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def draw_box_title(title: str):
    """Cetak baris judul dalam box, padding dihitung otomatis
    biar sisi kanan box selalu nyambung rapi."""
    inner = f" {title}"
    pad = BOX_WIDTH - len(inner)
    if pad < 0:
        inner = inner[:BOX_WIDTH]
        pad = 0
    print(
        f"{COLORS['yellow']}{BOLD}║{RESET}"
        f"{COLORS['magenta']}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{COLORS['yellow']}{BOLD}║{RESET}"
    )

# ================= Menu Frequency =================

def frequency_menu():
    """Menu utama frequency dengan 4 opsi - Rata Kiri"""
    clear_screen()

    # Header - Rata Kiri
    draw_box_top()
    draw_box_title("FREQUENCY MENU")
    draw_box_bottom()

    print()

    # Menu Options - Rata Kiri
    print(f"  {COLORS['cyan']}{BOLD}[1]{RESET} {COLORS['green']}BETTERCAP{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[2]{RESET} {COLORS['green']}DEAUTH{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[3]{RESET} {COLORS['green']}MDK4{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[4]{RESET} {COLORS['green']}AIRGEDDON{RESET}")
    print()
    print(f"  {COLORS['cyan']}{BOLD}[0]{RESET} {COLORS['red']}BACK TO MAIN MENU{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[99]{RESET} {COLORS['red']}EXIT{RESET}")

    print()
    # Garis pemisah yang menyambung
    terminal_width = shutil.get_terminal_size().columns
    line_length = min(terminal_width - 4, 40)  # Max 40 karakter
    print(f"  {COLORS['yellow']}{BOLD}{'=' * line_length}{RESET}")
    print()

    # Input
    try:
        choice = input(f"  {COLORS['yellow']}>> option : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"

    if choice.strip() == "4":
        return "0"
    return choice.strip()

# ================= Eksekusi Script =================

def launch_bettercap():
    """Menjalankan bettercap-menu.py"""
    script_path = os.path.join(os.path.dirname(__file__), "bettercap", "bettercap-menu.py")
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_deauth():
    """Menjalankan deauth-menu.py"""
    script_path = os.path.join(os.path.dirname(__file__), "deauth", "deauth-menu.py")
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_mdk4():
    """Menjalankan mdk4-menu.py"""
    script_path = os.path.join(os.path.dirname(__file__), "mdk4", "mdk4-menu.py")
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_airgeddon():
    """Menjalankan Airgeddon dengan sudo"""
    print(f"\n  {COLORS['green']}[+] Menjalankan Airgeddon...{RESET}\n")
    try:
        os.execvp("sudo", ["sudo", "airgeddon"])
    except FileNotFoundError:
        print(f"  {COLORS['red']}[✗] Airgeddon tidak ditemukan!{RESET}")
        print(f"  {COLORS['yellow']}Install Airgeddon dengan:{RESET}")
        print(f"  {COLORS['cyan']}git clone https://github.com/v1s1t0r1sh3r3/airgeddon.git{RESET}")
        print(f"  {COLORS['cyan']}cd airgeddon && sudo bash airgeddon.sh{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def return_to_main_menu():
    """Kembali ke xforg3.py di parent directory"""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "xforg3.py")
    
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] xforg3.py tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def exit_program():
    clear_screen()
    sys.exit(0)

# ================= Main App =================

def app_loop():
    """Loop utama aplikasi"""
    while True:
        choice = frequency_menu()

        if choice == "1":  # BETTERCAP
            launch_bettercap()
        elif choice == "2":  # DEAUTH
            launch_deauth()
        elif choice == "3":  # MDK4
            launch_mdk4()
        elif choice == "4":  # AIRGEDDON
            launch_airgeddon()
            input("\n  Tekan Enter untuk kembali...")
        elif choice == "0":  # BACK TO MAIN MENU
            return_to_main_menu()
            return
        elif choice == "99":  # EXIT
            exit_program()
        else:
            print(f"\n  {COLORS['red']}[!] Pilihan tidak valid!{RESET}")
            time.sleep(1)

def main():
    try:
        app_loop()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n  {COLORS['yellow']}[!] Program dihentikan oleh user{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()