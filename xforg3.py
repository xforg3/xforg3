#!/usr/bin/env python3
"""
xforg3.py - Clean Terminal UI (Menu Only)
------------------------------------
Fungsi login password dan seluruh animasi glitch yang memperlambat performa telah dihapus.
"""

import os
import sys
import shutil

# ---------- ANSI ----------
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
}

ASCII_ART = r"""                                                                            
                      _____         _____         _____         _____    
_____      _____ ____|\    \    ____|\    \    ___|\    \    ___|\    \   
\    \    /    /|    | \    \ /     /\    \  |    |\    \  /    /\    \  
 \    \  /    / |    |______//     /  \    \ |    | |    ||    |  |____| 
  \____\/____/  |    |----'\|     |    |    ||    |/____/ |    |    ____ 
  /    /\    \  |    |_____/|     |    |    ||    |\    \ |    |   |    |
 /    /  \    \ |    |      |\     \  /    /||    | |    ||    |   |_,  |
/____/ /\ \____\|____|      | \_____\/____/ ||____| |____||\ ___\___/  /|
|    |/  \|    ||    |       \ |    ||    | /|    | |    || |   /____ / |
|____|    |____||____|        \|____||____|/ |____| |____| \|___|    | / 
 \(        )/    )/             \(    )/      \(     )/      \( |____|/  
  '        '      '              '    '        '     '        '   )/     
                                                                  '      """


# ================= Util Layar =================

def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))


def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()


# ================= Menu / Tampilan =================

def main_menu():
    """Menu utama polos langsung cetak tanpa jeda."""
    clear_screen()
    _, height = get_size()

    options = [
        "1. TERMINAL",
        "2. WEBSITE",
        "",
        "0. EXIT",
        "99. REGULAR",
    ]
    
    col_indent = " " * 6  # Rata kiri menjorok 6 karakter
    separator = "=" * 112
    
    # Pisahkan ASCII Art menjadi per baris
    art_lines = ASCII_ART.splitlines()
    
    # Hitung posisi vertikal agar menu dan banner tercetak rapi di tengah layar terminal
    total_lines_len = len(art_lines) + 3 + len(options)
    start_row = max(1, (height // 2) - (total_lines_len // 2) - 2)
    
    # Cetak baris kosong untuk menyesuaikan posisi baris vertikal
    print("\n" * (start_row - 1))
    
    # Cetak ASCII Art banner
    for line in art_lines:
        print(f"{col_indent}{COLORS['red']}{BOLD}{line}{RESET}")
        
    print() # Baris kosong pemisah banner dengan menu
    
    # Cetak Garis Pemisah Atas
    print(f"{col_indent}{COLORS['green']}{separator}{RESET}")
    
    # Cetak Pilihan Menu
    for opt in options:
        if not opt:
            print()
            continue
            
        color = COLORS["cyan"]
        if opt in {"0. EXIT", "99. REGULAR"}:
            color = COLORS["red"]
        elif "TERMINAL" in opt or "WEBSITE" in opt:
            color = COLORS["yellow"]
            
        print(f"{col_indent}{color}{BOLD}{opt}{RESET}")

    # Cetak Garis Pemisah Bawah
    print(f"{col_indent}{COLORS['green']}{separator}{RESET}")

    print("\n")
    try:
        choice = input(f"      {COLORS['yellow']}>> option : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"
        
    if choice.strip() == "4":
        return "0"
    return choice.strip()


# ================= Alur Utama =================

def app_loop():
    while True:
        choice = main_menu()
        
        if choice == "1":  # TERMINAL
            clear_screen()
            terminal_path = os.path.join(os.path.dirname(__file__), "terminal", "terminal.py")
            if os.path.exists(terminal_path):
                os.execvp(sys.executable, [sys.executable, terminal_path])
            else:
                print(f"\n{COLORS['red']}[!] Terminal script tidak ditemukan: {terminal_path}{RESET}")
                input("\nTekan Enter untuk kembali...")
                
        elif choice == "2":  # WEBSITE
            clear_screen()
            website_path = os.path.join(os.path.dirname(__file__), "website", "website.py")
            if os.path.exists(website_path):
                os.execvp(sys.executable, [sys.executable, website_path])
            else:
                print(f"\n{COLORS['red']}[!] Website script tidak ditemukan: {website_path}{RESET}")
                input("\nTekan Enter untuk kembali...")
                
        elif choice == "0":
            clear_screen()
            break
            
        elif choice == "99":
            clear_screen()
            # Menjalankan perintah eksternal standar bawaan dari kode lama kamu
            os.system("ls")
            sys.exit(0)
            
        else:
            print(f"      {COLORS['red']}invalid option{RESET}")
            try:
                import time
                time.sleep(0.6)
            except KeyboardInterrupt:
                break


def main():
    try:
        app_loop()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)


if __name__ == "__main__":
    main()