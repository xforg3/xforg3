#!/usr/bin/env python3
import time
import sys
import os
import shutil
import subprocess

# Warna Terminal
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"  
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"


def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))


def clear_screen():
    """Membersihkan layar terminal."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def quick_print(text, color=CYAN):
    print(f"{color}{BOLD}{text}{RESET}")


def launch_aireplay_ng():
    clear_screen()
    quick_print("LAUNCHING AIREPLAY-NG...", CYAN)
    
    aireplay_path = os.path.join(os.path.dirname(__file__), "deauth.py")
    if os.path.exists(aireplay_path):
        os.execvp(sys.executable, [sys.executable, aireplay_path])
    
    print(f"      {YELLOW}{BOLD}AIREPLAY-NG script not found. Placeholder only.{RESET}")
    time.sleep(0.5)


def launch_deauth_web():
    """Menjalankan deauth-web dari folder deauth-web/start.py dengan sudo"""
    clear_screen()
    quick_print("LAUNCHING DEAUTH WEB INTERFACE...", MAGENTA)
    
    # Path ke folder deauth-web dan start.py
    script_dir = os.path.dirname(__file__)
    deauth_web_dir = os.path.join(script_dir, "deauth-web")
    start_script = os.path.join(deauth_web_dir, "start.py")
    
    # Cek apakah folder dan file exist
    if os.path.exists(start_script):
        quick_print(f"Starting deauth-web from: {start_script}", CYAN)
        time.sleep(1)
        
        # Jalankan dengan sudo python3
        try:
            # Pindah ke direktori deauth-web terlebih dahulu
            os.chdir(deauth_web_dir)
            # Jalankan dengan sudo
            subprocess.run(["sudo", "python3", "start.py"])
        except Exception as e:
            print(f"      {RED}{BOLD}Error running deauth-web: {e}{RESET}")
            time.sleep(2)
        finally:
            # Kembali ke direktori script
            os.chdir(script_dir)
    else:
        print(f"      {RED}{BOLD}deauth-web/start.py not found at: {start_script}{RESET}")
        print(f"      {YELLOW}{BOLD}Please make sure deauth-web folder exists in the same directory.{RESET}")
        time.sleep(2)


def show_menu():
    clear_screen()
    _, height = get_size()

    # ASCII Art Menu
    ascii_art = r"""
 _ .-') _     ('-.   ('-.                  .-') _    ('-. .-.       _   .-')       ('-.       .-') _             
( (  OO) )  _(  OO) ( OO ).-.             (  OO) )  ( OO )  /      ( '.( OO )_  _(  OO)     ( OO ) )            
 \     .'_ (,------./ . --. / ,--. ,--.  /     '._ ,--. ,--.       ,--.   ,--.)(,------.,--./ ,--,' ,--. ,--.   
 ,`'--..._) |  .---'| \-.  \  |  | |  |  |'--...__)|  | |  |       |   `.'   |  |  .---'|   \ |  |\ |  | |  |   
 |  |  \  ' |  |   .-'-'  |  | |  | | .-')'--.  .--'|   .|  |       |         |  |  |    |    \|  | )|  | | .-') 
 |  |   ' |(|  '--.\| |_.'  | |  |_|( OO )  |  |   |       |       |  |'.'|  | (|  '--. |  .     |/ |  |_|( OO )
 |  |   / : |  .--' |  .-.  | |  | | `-' /  |  |   |  .-.  |       |  |   |  |  |  .--' |  |\    |  |  | | `-' /
 |  '--'  / |  `---.|  | |  |('  '-'(_.-'   |  |   |  | |  |       |  |   |  |  |  `---.|  | \   | ('  '-'(_.-' 
 `-------'  `------'`--' `--'  `-----'      `--'   `--' `--'       `--'   `--'  `------'`--'  `--'   `-----'    """

    options = [
        "1. DEAUTH",
        "2. DEAUTH (BUT IN WEBSITE)",
        "",
        "0. BACK TO MAIN MENU",
        "99. EXIT"
    ]
    
    col_indent = " " * 6  # Spasi kiri menjorok 6 karakter agar sama dengan xforg3.py
    separator = "=" * 112
    art_lines = ascii_art.splitlines()
    
    # Hitung posisi tengah vertikal
    total_lines_len = len(art_lines) + 3 + len(options)
    start_row = max(1, (height // 2) - (total_lines_len // 2) - 2)
    
    # Cetak spasi atas layar
    print("\n" * (start_row - 1))
    
    # Cetak ASCII banner
    for line in art_lines:
        print(f"{col_indent}{RED}{line}{RESET}")
        
    # Garis pembatas atas
    print(f"{col_indent}{GREEN}{separator}{RESET}")
    
    # Cetak Menu Pilihan
    for opt in options:
        if not opt:
            print()
            continue
            
        color = CYAN
        if opt.startswith(("0.", "99.")):
            color = RED
        elif opt.startswith("2."):
            color = MAGENTA  # Warna khusus untuk opsi deauth web
            
        print(f"{col_indent}{color}{BOLD}{opt}{RESET}")
        
    # Garis pembatas bawah
    print(f"{col_indent}{GREEN}{separator}{RESET}")
    print("\n")


def main():
    while True:  # Loop agar bisa kembali ke menu setelah deauth-web selesai
        show_menu()
        try:
            choice = input(f"      {BOLD}{YELLOW}>> option : {RESET}")
        except (KeyboardInterrupt, EOFError):
            choice = "0"

        if choice.strip() == "1":
            launch_aireplay_ng()
            break  # Exit setelah menjalankan aireplay
        elif choice.strip() == "2":
            launch_deauth_web()
            # Setelah selesai, kembali ke menu utama (loop)
            continue
        elif choice.strip() == "0":
            parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frequency.py"))
            if not os.path.exists(parent):
                parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frequency.py"))
            os.execvp(sys.executable, [sys.executable, parent])
            break
        elif choice.strip() == "99":
            clear_screen()
            sys.exit(0)
        else:
            print(f"      {RED}{BOLD}Pilihan tidak valid!{RESET}")
            time.sleep(0.6)


if __name__ == "__main__":
    main()