#!/usr/bin/env python3
"""
Clean Loading + Menu - Terminal
---------------------------------
Seluruh animasi loading, glitch burst, screen shake, dan efek penundaan waktu dihapus.
Menu dan banner langsung tercetak instan saat dijalankan dengan kalkulasi posisi tengah.
"""

import os
import sys
import shutil

RESET = "\033[0m"
BOLD = "\033[1m"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J\033[H"

RED = "\033[38;5;196m"
CYAN = "\033[92m"  
GREEN = "\033[96m"  
YELLOW = "\033[93m"

ASCII_ART = r""" (    (                          )           )  
 )\ ) )\ )      (             ( /(   (    ( /(  
(()/((()/((  ( )\      (  (   )\())  )\   )\()) 
 /(_))/(_))\ )((_)    )\ )\ ((_)\ (((_) ((_)\  
(_))_(_))((_|(_)_  _ ((_|(_) _((_))\_____ ((_) 
| |_ | _ \ __/ _ \| | | | __| \| ((/ __\ \ / / 
| __||   / _| (_) | |_| | _|| .` || (__ \ V /  
|_|  |_|_\___\__\_\\___/|___|_|\_| \___| |_|"""


def get_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()


MENU_OPTIONS = ["BETTERCAP", "DEAUTH", "MDK4", "AIRGEDDON"]
col_indent = " " * 6  # Spasi kiri menjorok 6 karakter agar sama dengan xforg3.py
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

BETTERCAP_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "bettercap", "bettercap-menu.py"))
AIRCRACK_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "deauth", "deauth-menu.py"))
MDK4_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "mdk4", "mdk4-menu.py"))


def draw_menu():
    """Tampilkan banner dan menu rapi di tengah terminal menggunakan mekanik xforg3.py."""
    clear_screen()
    _, height = get_size()
    
    options = []
    for i, opt in enumerate(MENU_OPTIONS, start=1):
        options.append(f"{i}. {opt}")
    options.extend(["", "0. BACK TO MAIN MENU", "99. EXIT"])

    art_lines = ASCII_ART.splitlines()
    separator = "=" * 112
    
    # Hitung posisi vertikal tengah (Banner + 2 Garis Pemisah + Pilihan Menu)
    total_lines_len = len(art_lines) + 3 + len(options)
    start_row = max(1, (height // 2) - (total_lines_len // 2) - 2)
    
    # Memberikan space baris kosong di bagian atas
    print("\n" * (start_row - 1))
    
    # Cetak ASCII Art banner
    for line in art_lines:
        print(f"{col_indent}{RED}{BOLD}{line}{RESET}")
        
    print() # Baris kosong pemisah
    
    # Garis pembatas atas menu
    print(f"{col_indent}{CYAN}{separator}{RESET}")
    
    # Cetak Pilihan Menu
    for opt in options:
        if not opt:
            print()
            continue
            
        color = GREEN
        if opt.startswith(("0.", "99.")):
            color = RED
        elif "AIRGEDDON" in opt:
            color = YELLOW  # Warna khusus untuk Airgeddon
            
        print(f"{col_indent}{color}{BOLD}{opt}{RESET}")

    # Garis pembatas bawah menu
    print(f"{col_indent}{CYAN}{separator}{RESET}")
    print("\n")


def clean_prompt():
    sys.stdout.write(f"      {YELLOW}{BOLD}>> option : {RESET}")
    sys.stdout.write(SHOW_CURSOR)
    sys.stdout.flush()
    try:
        return input()
    except (KeyboardInterrupt, EOFError):
        return "0"


def launch_bettercap_menu():
    clear_screen()
    os.execvp(sys.executable, [sys.executable, BETTERCAP_MENU_PATH])


def launch_mdk4_menu():
    clear_screen()
    os.execvp(sys.executable, [sys.executable, MDK4_MENU_PATH])


def launch_airgeddon():
    """Menjalankan Airgeddon dengan sudo"""
    clear_screen()
    print(f"{GREEN}Menjalankan Airgeddon...{RESET}\n")
    
    # Cek apakah airgeddon terinstall
    try:
        # Jalankan sudo airgeddon
        os.execvp("sudo", ["sudo", "airgeddon"])
    except FileNotFoundError:
        print(f"{RED}Airgeddon tidak ditemukan!{RESET}")
        print(f"{YELLOW}Install Airgeddon dengan:{RESET}")
        print(f"{CYAN}git clone https://github.com/v1s1t0r1sh3r3/airgeddon.git{RESET}")
        print(f"{CYAN}cd airgeddon && sudo bash airgeddon.sh{RESET}")
        input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")
        return


def return_to_main_menu():
    clear_screen()
    path_options = [
        "/home/kali/xforg3/xforg3.py",                                    
        os.path.abspath(os.path.join(THIS_DIR, "xforg3.py")),             
        os.path.abspath(os.path.join(THIS_DIR, "..", "xforg3.py")),       
        os.path.abspath(os.path.join(THIS_DIR, "..", "..", "xforg3.py"))  
    ]
    
    xforg3_path = None
    for path in path_options:
        if os.path.exists(path):
            xforg3_path = path
            break

    if xforg3_path:
        os.execvp(sys.executable, [sys.executable, xforg3_path])
    else:
        print(f"\n{RED}[!] Eror: File xforg3.py tidak ditemukan di sistem.{RESET}")
        input("\nTekan Enter untuk kembali...")


def exit_program():
    clear_screen()
    sys.exit(0)


def main():
    try:
        draw_menu()
        choice = clean_prompt()
        
        if choice.strip() == "1":
            launch_bettercap_menu()
        elif choice.strip() == "2":
            clear_screen()
            os.execvp(sys.executable, [sys.executable, AIRCRACK_MENU_PATH])
        elif choice.strip() == "3":
            launch_mdk4_menu()
        elif choice.strip() == "4":
            launch_airgeddon()
        elif choice.strip() == "0":
            return_to_main_menu()
        elif choice.strip() == "99":
            exit_program()
        else:
            print(f"      {RED}invalid option{RESET}")
            import time
            time.sleep(0.6)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()


if __name__ == "__main__":
    main()