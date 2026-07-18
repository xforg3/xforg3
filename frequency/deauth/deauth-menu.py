#!/usr/bin/env python3
import time
import sys
import os

# Warna Terminal
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"  # Menggunakan ini untuk warna tosca/hijau aqua
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"


def clear():
    """Membersihkan layar terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def quick_print(text, color=CYAN):
    """Cetak teks langsung tanpa animasi."""
    print(f"{color}{BOLD}{text}{RESET}")


def launch_aireplay_ng():
    clear()
    quick_print("LAUNCHING AIREPLAY-NG...", CYAN)
    
    aireplay_path = os.path.join(os.path.dirname(__file__), "deauth.py")
    if os.path.exists(aireplay_path):
        os.execvp(sys.executable, [sys.executable, aireplay_path])
    
    print(f"{YELLOW}{BOLD}AIREPLAY-NG script not found. Placeholder only.{RESET}")
    time.sleep(0.5)


def show_menu():
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
 `-------'  `------'`--' `--'  `-----'      `--'   `--' `--'       `--'   `--'  `------'`--'  `--'   `-----'    
"""
    print(f"{CYAN}{ascii_art}{RESET}")
    print(f"{GREEN}{'=' * 112}{RESET}")
    # Diganti ke CYAN + BOLD agar identik dengan FREQUENCY
    print(f"{GREEN}{BOLD}1. DEAUTH{RESET}")    
    print(f"")    
    print(f"{RED}{BOLD}0. BACK TO MAIN MENU{RESET}")
    print(f"{RED}{BOLD}99. EXIT{RESET}")
    print(f"{CYAN}{'=' * 112}{RESET}")


def main():
    clear()
    show_menu()
    choice = input(f"{BOLD}{MAGENTA}chose your option > {RESET}")

    if choice.strip() == "1":
        launch_aireplay_ng()
    elif choice.strip() == "0":
        parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frequency.py"))
        if not os.path.exists(parent):
            parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frequency.py"))
        os.execvp(sys.executable, [sys.executable, parent])
    elif choice.strip() == "99":
        clear()
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}Pilihan tidak valid!{RESET}")


if __name__ == "__main__":
    main()