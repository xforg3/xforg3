#!/usr/bin/env python3
"""
bettercap-menu.py - Clean Terminal UI
-------------------------------------
Seluruh fungsi animasi loading, glitch burst, dan penundaan waktu dihapus.
Menu langsung tercetak instan dengan tata letak vertikal tengah yang presisi.
"""

import sys
import os
import shutil

# ---------- ANSI ----------
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

ASCII_ART = r"""
 ___ ___ _____ _____ ___ ___  ___   _   ___ 
| _ ) __|_   _|_   _| __| _ \/ __| /_\ | _ \
| _ \ _|  | |   | | | _||   / (__ / _ \|  _/
|___/___| |_|   |_| |___|_|_\___/_/ \_\_|  """


def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))


def clear_screen():
    """Membersihkan layar terminal."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def quick_print(text, color=CYAN):
    """Cetak teks konfirmasi modul langsung tanpa jeda."""
    print(f"{color}{BOLD}{text}{RESET}")


def launch_ban():
    clear_screen()
    quick_print("LAUNCHING BAN MODULE...", CYAN)
    
    ban_path = os.path.join(os.path.dirname(__file__), "bettercap-ban.py")
    if not os.path.exists(ban_path):
        ban_path = os.path.join(os.path.dirname(__file__), "ban.py")
        
    if os.path.exists(ban_path):
        os.execvp(sys.executable, [sys.executable, ban_path])
    else:
        print(f"      {YELLOW}{BOLD}Ban script not found. Placeholder only.{RESET}")
        sys.exit(1)


def launch_bettercap():
    """Menjalankan sudo bettercap secara otomatis."""
    clear_screen()
    quick_print("LAUNCHING SUDO BETTERCAP...", CYAN)
    try:
        os.execvp("sudo", ["sudo", "bettercap"])
    except FileNotFoundError:
        print(f"      {RED}{BOLD}Error: 'sudo' atau 'bettercap' tidak ditemukan di sistem.{RESET}")
        sys.exit(1)


def show_menu():
    clear_screen()
    _, height = get_size()

    options = [
        "1. BAN",
        "2. NORMAL BETTERCAP",
        "",
        "0. BACK TO MAIN MENU",
        "99. EXIT"
    ]
    
    col_indent = " " * 6
    separator = "=" * 112
    art_lines = ASCII_ART.splitlines()
    
    total_lines_len = len(art_lines) + 3 + len(options)
    start_row = max(1, (height // 2) - (total_lines_len // 2) - 2)
    
    print("\n" * (start_row - 1))
    
    for line in art_lines:
        print(f"{col_indent}{RED}{BOLD}{line}{RESET}")
        
    print()
    print(f"{col_indent}{GREEN}{separator}{RESET}")
    
    for opt in options:
        if not opt:
            print()
            continue
            
        color = CYAN
        if opt.startswith(("0.", "99.")):
            color = RED
            
        print(f"{col_indent}{color}{BOLD}{opt}{RESET}")

    print(f"{col_indent}{GREEN}{separator}{RESET}")
    print("\n")


def main():
    show_menu()
    
    try:
        choice = input(f"      {BOLD}{MAGENTA}>> option :{RESET}")
    except (KeyboardInterrupt, EOFError):
        choice = "0"

    if choice.strip() == "1":
        launch_ban()
    elif choice.strip() == "2":
        launch_bettercap()
    elif choice.strip() == "0":
        parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frequency.py"))
        if not os.path.exists(parent):
            parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frequency.py"))
        os.execvp(sys.executable, [sys.executable, parent])
    elif choice.strip() == "99":
        clear_screen()
        sys.exit(0)
    else:
        print(f"      {RED}{BOLD}Pilihan tidak valid!{RESET}")
        import time
        time.sleep(0.6)


if __name__ == "__main__":
    main()