#!/usr/bin/env python3
"""
Main Menu - Terminal UI
-----------------------
Menu utama dengan pilihan untuk menjalankan berbagai tools
"""

import sys
import os
import shutil
import subprocess

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
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def print_menu():
    clear_screen()
    cols, rows = get_size()

    options = [
        "1. MDK4 (TERMINAL VERSION)",
        "2. MDK4 (WEB VERSION) 🚀",
        "",
        "0. EXIT"
    ]
    
    col_indent = " " * 6
    separator = "=" * 112
    art_lines = ASCII_ART.splitlines()
    
    total_lines_len = len(art_lines) + 3 + len(options)
    start_row = max(1, (rows // 2) - (total_lines_len // 2) - 2)
    
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
        if opt.startswith("0."):
            color = RED
        elif "🚀" in opt:
            color = MAGENTA
            
        print(f"{col_indent}{color}{BOLD}{opt}{RESET}")

    print(f"{col_indent}{GREEN}{separator}{RESET}")
    print("\n")


def launch_mdk4_terminal():
    """Jalankan MDK4 Terminal Version"""
    clear_screen()
    print(f"{CYAN}[*] Launching MDK4 Terminal Version...{RESET}")
    
    # Cari mdk4-menu.py di direktori yang sama atau subfolder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(script_dir, "mdk4-menu.py"),
        os.path.join(script_dir, "mdk4", "mdk4-menu.py"),
        os.path.join(script_dir, "..", "mdk4", "mdk4-menu.py"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"{GREEN}[+] Found: {path}{RESET}")
            os.execvp(sys.executable, [sys.executable, path])
            return
    
    print(f"{RED}[-] mdk4-menu.py not found!{RESET}")
    print(f"{YELLOW}[!] Make sure mdk4-menu.py exists{RESET}")
    input("\nPress Enter to continue...")
    main()


def launch_mdk4_web():
    """Jalankan MDK4 Web Version (start.py di folder mdk4-website)"""
    clear_screen()
    print(f"{MAGENTA}[*] Launching MDK4 Web Version...{RESET}")
    print(f"{MAGENTA}[*] Starting web server...{RESET}")
    
    # Cari mdk4-website/start.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(script_dir, "mdk4-website", "start.py"),
        os.path.join(script_dir, "..", "mdk4-website", "start.py"),
        os.path.join(os.path.dirname(script_dir), "mdk4-website", "start.py"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"{GREEN}[+] Found: {path}{RESET}")
            print(f"{GREEN}[+] Starting MDK4 Web Interface...{RESET}")
            print(f"{YELLOW}[!] Press Ctrl+C to stop server{RESET}\n")
            
            # Jalankan start.py dengan python3
            os.execvp(sys.executable, [sys.executable, path])
            return
    
    # Kalau tidak ditemukan, coba cari di direktori lain
    print(f"{RED}[-] mdk4-website/start.py not found!{RESET}")
    print(f"{YELLOW}[!] Make sure folder mdk4-website exists with start.py{RESET}")
    print(f"{YELLOW}[!] Structure should be:{RESET}")
    print(f"    ./mdk4-website/")
    print(f"    ./mdk4-website/start.py")
    print(f"    ./mdk4-website/app.py")
    print(f"    ./mdk4-website/templates/index.html")
    
    input("\nPress Enter to continue...")
    main()


def main():
    while True:
        print_menu()
        
        try:
            choice = input(f"      {BOLD}{YELLOW}>> option : {RESET}")
        except (KeyboardInterrupt, EOFError):
            choice = "0"

        if choice.strip() == "1":
            launch_mdk4_terminal()
        elif choice.strip() == "2":
            launch_mdk4_web()
        elif choice.strip() == "0":
            clear_screen()
            print(f"{GREEN}Goodbye!{RESET}")
            sys.exit(0)
        else:
            print(f"      {RED}{BOLD}Pilihan tidak valid!{RESET}")
            import time
            time.sleep(0.6)


if __name__ == "__main__":
    main()