#!/usr/bin/env python3
"""
Main Menu - Terminal UI
-----------------------
Menu utama dengan pilihan untuk menjalankan berbagai tools MDK4
"""

import sys
import os
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
        f"{COLORS['cyan']}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{COLORS['yellow']}{BOLD}║{RESET}"
    )

# ================= Menu MDK4 =================

def mdk4_menu():
    """Menu utama MDK4 - Rata Kiri"""
    clear_screen()

    # Header - Rata Kiri
    draw_box_top()
    draw_box_title("MDK4 MENU")
    draw_box_bottom()

    print()

    # Menu Options - Rata Kiri
    print(f"  {COLORS['cyan']}{BOLD}[1]{RESET} {COLORS['green']}MDK4 DEAUTH{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[2]{RESET} {COLORS['green']}MDK4 BEACON FLOOD{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[3]{RESET} {COLORS['green']}MDK4 AUTH DOS{RESET}")
    print()
    print(f"  {COLORS['cyan']}{BOLD}[0]{RESET} {COLORS['red']}BACK TO FREQUENCY{RESET}")
    print(f"  {COLORS['cyan']}{BOLD}[99]{RESET} {COLORS['red']}EXIT{RESET}")

    print()
    # Garis pemisah yang menyambung
    terminal_width = shutil.get_terminal_size().columns
    line_length = min(terminal_width - 4, 40)  # Max 40 karakter
    print(f"  {COLORS['green']}{BOLD}{'=' * line_length}{RESET}")
    print()

    # Input
    try:
        choice = input(f"  {COLORS['yellow']}>> option : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"

    return choice.strip()

# ================= Eksekusi =================

def launch_deauth():
    """Jalankan MDK4 Deauth (mdk4-deauth.py)"""
    clear_screen()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(script_dir, "mdk4-deauth.py")
    
    if os.path.exists(target_file):
        os.execvp(sys.executable, [sys.executable, target_file])
    else:
        print(f"\n  {COLORS['red']}[✗] mdk4-deauth.py tidak ditemukan: {target_file}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_beacon():
    """Jalankan MDK4 Beacon (mdk4-beacon.py)"""
    clear_screen()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(script_dir, "mdk4-beacon.py")
    
    if os.path.exists(target_file):
        os.execvp(sys.executable, [sys.executable, target_file])
    else:
        print(f"\n  {COLORS['red']}[✗] mdk4-beacon.py tidak ditemukan: {target_file}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def launch_authdos():
    """Jalankan MDK4 Auth DOS (mdk4-authdos.py)"""
    clear_screen()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(script_dir, "mdk4-authdos.py")
    
    if os.path.exists(target_file):
        os.execvp(sys.executable, [sys.executable, target_file])
    else:
        print(f"\n  {COLORS['red']}[✗] mdk4-authdos.py tidak ditemukan: {target_file}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def return_to_frequency():
    """Kembali ke frequency.py di parent directory"""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frequency.py")
    
    if os.path.exists(script_path):
        os.execvp(sys.executable, [sys.executable, script_path])
    else:
        print(f"\n  {COLORS['red']}[✗] frequency.py tidak ditemukan: {script_path}{RESET}")
        input("\n  Tekan Enter untuk kembali...")

def exit_program():
    clear_screen()
    sys.exit(0)

# ================= Main App =================

def app_loop():
    """Loop utama aplikasi"""
    while True:
        choice = mdk4_menu()

        if choice == "1":  # MDK4 DEAUTH
            launch_deauth()
        elif choice == "2":  # MDK4 BEACON FLOOD
            launch_beacon()
        elif choice == "3":  # MDK4 AUTH DOS
            launch_authdos()
        elif choice == "0":  # BACK TO FREQUENCY
            return_to_frequency()
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