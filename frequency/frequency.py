#!/usr/bin/env python3
"""
Clean Loading + Menu - Terminal
---------------------------------
Seluruh animasi loading, glitch burst, screen shake, dan efek penundaan waktu dihapus.
Menu dan banner langsung tercetak instan saat dijalankan.
"""

import os
import sys
import shutil

RESET = "\033[0m"
BOLD = "\033[1m"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J\033[H"

RED = "\033[38;5;196m"
CYAN = "\033[92m"  # Diubah ke \033[92m agar warnanya sama dengan FREQUENCY
GREEN = "\033[92m" # Disamakan juga agar banner sewarna
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


def move(row, col):
    sys.stdout.write(f"\033[{row};{col}H")


def clear():
    sys.stdout.write(CLEAR)


def print_at(row, col, text, color=""):
    if row < 1:
        row = 1
    if col < 1:
        col = 1
    move(row, col)
    sys.stdout.write(f"{color}{text}{RESET}")


def flush():
    sys.stdout.flush()


MENU_OPTIONS = ["BETTERCAP", "DEAUTH", "MDK4"]
LEFT_MARGIN = 5  
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

BETTERCAP_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "bettercap", "bettercap-menu.py"))
AIRCRACK_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "deauth", "deauth-menu.py"))
MDK4_MENU_PATH = os.path.abspath(os.path.join(THIS_DIR, "mdk4", "mdk4-menu.py"))


def draw_ascii_art(start_row=1):
    lines = ASCII_ART.splitlines()
    row = start_row
    for line in lines:
        print_at(row, LEFT_MARGIN, line, GREEN + BOLD)
        row += 1
    return row


def draw_menu():
    clear()

    art_end_row = draw_ascii_art(start_row=2)
    row = art_end_row + 2  
    
    print_at(row, LEFT_MARGIN, "=" * 112, CYAN)
    row += 1
    
    for i, opt in enumerate(MENU_OPTIONS, start=1):
        print_at(row, LEFT_MARGIN, f"{i}. {opt}", CYAN + BOLD)
        row += 1

    row += 1  
    print_at(row, LEFT_MARGIN, "0. BACK TO MAIN MENU", RED + BOLD)
    row += 1
    print_at(row, LEFT_MARGIN, "99. EXIT", RED + BOLD)
    row += 1
    
    print_at(row, LEFT_MARGIN, "=" * 112, CYAN)
    row += 2  

    flush()
    return row


def clean_prompt(row, text=">> option: "):
    print_at(row, LEFT_MARGIN, text, YELLOW + BOLD)
    flush()
    sys.stdout.write(SHOW_CURSOR)
    flush()
    try:
        return input()
    except (KeyboardInterrupt, EOFError):
        return "0"


def launch_bettercap_menu():
    clear()
    os.execvp(sys.executable, [sys.executable, BETTERCAP_MENU_PATH])


def launch_mdk4_menu():
    clear()
    os.execvp(sys.executable, [sys.executable, MDK4_MENU_PATH])


def return_to_main_menu():
    clear()
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
    clear()
    sys.exit(0)


def main():
    try:
        row = draw_menu()
        choice = clean_prompt(row + 1)
        
        if choice.strip() == "1":
            launch_bettercap_menu()
        elif choice.strip() == "2":
            clear()
            os.execvp(sys.executable, [sys.executable, AIRCRACK_MENU_PATH])
        elif choice.strip() == "3":
            launch_mdk4_menu()
        elif choice.strip() == "0":
            return_to_main_menu()
        elif choice.strip() == "99":
            exit_program()
        else:
            print(f"\nPilihan salah atau tidak terdaftar: {choice}")
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        flush()


if __name__ == "__main__":
    main()