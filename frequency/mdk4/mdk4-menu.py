#!/usr/bin/env python3
"""
mdk4-menu.py - Clean Terminal UI
---------------------------------
Seluruh fungsi animasi loading, glitch burst, dan penundaan waktu dihapus.
Menu langsung tercetak instan dengan layout presisi di tengah terminal.
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
$$\       $$\ $$$$$$$\  $$\   $$\ $$\   $$\       $$\       $$\ $$$$$$$$\ $$\   $$\ $$\   $$\ 
$$$\     $$$ |$$  __$$\ $$ | $$  |$$ |  $$ |      $$$\     $$$ |$$  _____|$$$\  $$ |$$ |  $$ |
$$$$\   $$$$ |$$ |  $$ |$$ |$$  / $$ |  $$ |      $$$$\   $$$$ |$$ |      $$$$\ $$ |$$ |  $$ |
$$\$$\$$ $$ |$$ |  $$ |$$$$$  /  $$$$$$$$ |      $$\$$\$$ $$ |$$$$$\    $$ $$\$$ |$$ |  $$ |
$$ \$$$  $$ |$$ |  $$ |$$  $$<   \_____$$ |      $$ \$$$  $$ |$$  __|   $$ \$$$$ |$$ |  $$ |
$$ | \$  /$$ |$$ |  $$ |$$ |\$$\        $$ |      $$ | \$  /$$ |$$ |      $$ |\$$$ |$$ |  $$ |
$$ |  \_/  $$ |$$$$$$$  |$$ | \$$\       $$ |      $$ |  \_/  $$ |$$$$$$$$\ $$ | \$$ |\$$$$$$  |
\__|       \__|\_______/ \__|  \__|      \__|      \__|       \__|\________|\__|  \__| \______/ """


def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))


def clear_screen():
    """Membersihkan layar terminal."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def quick_print(text, color=CYAN):
    """Cetak teks langsung tanpa animasi."""
    print(f"{color}{BOLD}{text}{RESET}")


def launch_authdos():
    clear_screen()
    quick_print("LAUNCHING MDK4 AUTH DOS...", CYAN)
    
    auth_path = os.path.join(os.path.dirname(__file__), "mdk4-authdos.py")
    if os.path.exists(auth_path):
        os.execvp(sys.executable, [sys.executable, auth_path])
        
    print(f"      {YELLOW}{BOLD}MDK4 authdos script not found. Placeholder only.{RESET}")
    sys.exit(1)


def launch_beacon():
    clear_screen()
    quick_print("LAUNCHING MDK4 BEACON...", CYAN)
    
    beacon_path = os.path.join(os.path.dirname(__file__), "mdk4-beacon.py")
    if os.path.exists(beacon_path):
        os.execvp(sys.executable, [sys.executable, beacon_path])
        
    print(f"      {YELLOW}{BOLD}MDK4 beacon script not found. Placeholder only.{RESET}")
    sys.exit(1)


def launch_deauth():
    clear_screen()
    quick_print("LAUNCHING MDK4 DEAUTH...", CYAN)
    
    deauth_path = os.path.join(os.path.dirname(__file__), "mdk4-deauth.py")
    if os.path.exists(deauth_path):
        os.execvp(sys.executable, [sys.executable, deauth_path])
        
    print(f"      {YELLOW}{BOLD}MDK4 deauth script not found. Placeholder only.{RESET}")
    sys.exit(1)


def show_menu():
    clear_screen()
    _, height = get_size()

    options = [
        "1. MDK4 AUTH DOS",
        "2. MDK4 BEACON",
        "3. MDK4 DEAUTH",
        "",
        "0. BACK TO MAIN MENU",
        "99. EXIT"
    ]
    
    col_indent = " " * 6  # Rata kiri menjorok 6 karakter
    separator = "=" * 112
    art_lines = ASCII_ART.splitlines()
    
    # Hitung posisi vertikal agar presisi di tengah layar terminal
    total_lines_len = len(art_lines) + 3 + len(options)
    start_row = max(1, (height // 2) - (total_lines_len // 2) - 2)
    
    # Cetak spasi kosong vertikal bagian atas
    print("\n" * (start_row - 1))
    
    # Cetak ASCII Art banner (Warna RED)
    for line in art_lines:
        print(f"{col_indent}{RED}{BOLD}{line}{RESET}")
        
    print()  # Baris kosong pemisah banner dengan menu
    
    # Cetak Garis Pemisah Atas (Warna GREEN)
    print(f"{col_indent}{GREEN}{separator}{RESET}")
    
    # Cetak Pilihan Menu (Warna CYAN & RED)
    for opt in options:
        if not opt:
            print()
            continue
            
        color = CYAN
        if opt.startswith(("0.", "99.")):
            color = RED
            
        print(f"{col_indent}{color}{BOLD}{opt}{RESET}")

    # Cetak Garis Pemisah Bawah (Warna GREEN)
    print(f"{col_indent}{GREEN}{separator}{RESET}")
    print("\n")


def main():
    show_menu()
    
    try:
        choice = input(f"      {BOLD}{YELLOW}>> option : {RESET}")
    except (KeyboardInterrupt, EOFError):
        choice = "0"

    if choice.strip() == "1":
        launch_authdos()
    elif choice.strip() == "2":
        launch_beacon()
    elif choice.strip() == "3":
        launch_deauth()
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