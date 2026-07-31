#!/usr/bin/env python3
"""
deauth-menu.py - Clean Terminal UI
---------------------------------
Menu untuk DEAUTH
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
    print(f"\n{COLORS['magenta']}{BOLD}╔{'═' * BOX_WIDTH}╗{RESET}")

def draw_box_bottom():
    print(f"{COLORS['magenta']}{BOLD}╚{'═' * BOX_WIDTH}╝{RESET}")

def draw_box_title(title: str):
    """Cetak baris judul dalam box, padding dihitung otomatis
    biar sisi kanan box selalu nyambung rapi."""
    inner = f" {title}"
    pad = BOX_WIDTH - len(inner)
    if pad < 0:
        inner = inner[:BOX_WIDTH]
        pad = 0
    print(
        f"{COLORS['magenta']}{BOLD}║{RESET}"
        f"{COLORS['cyan']}{BOLD}{inner}{RESET}"
        f"{' ' * pad}"
        f"{COLORS['magenta']}{BOLD}║{RESET}"
    )

# ================= Menu Deauth =================

def deauth_menu():
    """Menu utama deauth - Rata Kiri"""
    clear_screen()

    # Header - Rata Kiri
    draw_box_top()
    draw_box_title("DEAUTH MENU")
    draw_box_bottom()

    print()

    # Menu Options - Rata Kiri
    print(f"  {COLORS['yellow']}{BOLD}[1]{RESET} {COLORS['green']}DEAUTH{RESET}")
    print()
    print(f"  {COLORS['yellow']}{BOLD}[0]{RESET} {COLORS['red']}BACK TO FREQUENCY{RESET}")
    print(f"  {COLORS['yellow']}{BOLD}[99]{RESET} {COLORS['red']}EXIT{RESET}")

    print()
    # Garis pemisah yang menyambung
    terminal_width = shutil.get_terminal_size().columns
    line_length = min(terminal_width - 4, 40)  # Max 40 karakter
    print(f"  {COLORS['cyan']}{BOLD}{'=' * line_length}{RESET}")
    print()

    # Input
    try:
        choice = input(f"  {COLORS['yellow']}>> option : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"

    return choice.strip()

# ================= Eksekusi =================

def launch_deauth():
    """Menjalankan deauth.py"""
    clear_screen()
    deauth_path = os.path.join(os.path.dirname(__file__), "deauth.py")
    
    if os.path.exists(deauth_path):
        os.execvp(sys.executable, [sys.executable, deauth_path])
    else:
        print(f"\n  {COLORS['red']}[✗] deauth.py tidak ditemukan: {deauth_path}{RESET}")
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
        choice = deauth_menu()

        if choice == "1":  # DEAUTH
            launch_deauth()
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