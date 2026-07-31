#!/usr/bin/env python3
"""
terminal.py - Terminal Menu dengan 2 Opsi
---------------------------------------
Menu untuk mengakses FREQUENCY dan SOSIALS
"""

import os
import sys
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
}

ASCII_ART = r"""
   ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     
   ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     
      ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     
      ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     
      ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
      ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
                                                                      
   ███╗   ███╗███████╗███╗   ██╗██╗   ██╗                          
   ████╗ ████║██╔════╝████╗  ██║██║   ██║                          
   ██╔████╔██║█████╗  ██╔██╗ ██║██║   ██║                          
   ██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║   ██║                          
   ██║ ╚═╝ ██║███████╗██║ ╚████║╚██████╔╝                          
   ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝                           
"""

# ================= Util =================

def get_size():
    return shutil.get_terminal_size(fallback=(80, 24))

def clear_screen():
    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def print_centered(text, color=RESET, bold=False):
    """Mencetak teks di tengah layar"""
    width = get_size().columns
    style = BOLD if bold else ""
    print(f"{style}{color}{text.center(width)}{RESET}")

# ================= Menu Terminal =================

def terminal_menu():
    """Menu utama terminal dengan 2 opsi"""
    clear_screen()
    width = get_size().columns
    
    # Header
    print("\n" * 2)
    print_centered("═" * 60, COLORS["green"])
    print_centered(" TERMINAL MENU ", COLORS["yellow"], True)
    print_centered("═" * 60, COLORS["green"])
    
    # ASCII Art
    for line in ASCII_ART.splitlines():
        if line.strip():
            print_centered(line, COLORS["purple"])
    
    print()
    print_centered("═" * 60, COLORS["green"])
    
    # Menu Options
    print_centered("", COLORS["cyan"])
    print_centered(" 1. FREQUENCY ", COLORS["cyan"], True)
    print_centered(" 2. SOSIALS ", COLORS["cyan"], True)
    print_centered("", COLORS["cyan"])
    print_centered(" 0. BACK ", COLORS["red"], True)
    
    print_centered("═" * 60, COLORS["green"])
    print()
    
    # Input
    try:
        choice = input(f"{COLORS['yellow']}>> pilihan : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"
    
    return choice.strip()

# ================= Menu Sosials =================

def sosials_menu():
    """Menu untuk SOSIALS"""
    clear_screen()
    width = get_size().columns
    
    print("\n" * 3)
    print_centered("═" * 50, COLORS["green"])
    print_centered(" SOSIALS MENU ", COLORS["yellow"], True)
    print_centered("═" * 50, COLORS["green"])
    
    print_centered("", COLORS["cyan"])
    print_centered(" 🌐 SOSIALS MODULE ", COLORS["cyan"], True)
    print_centered("", COLORS["cyan"])
    
    print_centered(" [1] Social Media Scanner ", COLORS["green"])
    print_centered(" [2] Social Media Analysis ", COLORS["green"])
    print_centered(" [3] Export Data ", COLORS["green"])
    print_centered("", COLORS["cyan"])
    print_centered(" [0] Back ", COLORS["red"], True)
    
    print_centered("═" * 50, COLORS["green"])
    print()
    
    try:
        choice = input(f"{COLORS['yellow']}>> pilihan : {RESET}")
    except (KeyboardInterrupt, EOFError):
        return "0"
    
    return choice.strip()

# ================= Eksekusi Script =================

def run_frequency_script():
    """Menjalankan script frequency dari folder frequency/frequency.py"""
    script_path = os.path.join(os.path.dirname(__file__), "frequency", "frequency.py")
    
    if os.path.exists(script_path):
        print(f"\n{COLORS['green']}[✓] Menjalankan: {script_path}{RESET}")
        time.sleep(1)
        os.execvp(sys.executable, [sys.executable, script_path])
        return True
    else:
        print(f"\n{COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        print(f"{COLORS['yellow']}Pastikan file berada di: {script_path}{RESET}")
        input("\nTekan Enter untuk kembali...")
        return False

def run_sosials_script():
    """Menjalankan script sosials dari folder sosials/sosials.py"""
    script_path = os.path.join(os.path.dirname(__file__), "sosials", "sosials.py")
    
    if os.path.exists(script_path):
        print(f"\n{COLORS['green']}[✓] Menjalankan: {script_path}{RESET}")
        time.sleep(1)
        os.execvp(sys.executable, [sys.executable, script_path])
        return True
    else:
        print(f"\n{COLORS['red']}[✗] Script tidak ditemukan: {script_path}{RESET}")
        print(f"{COLORS['yellow']}Pastikan file berada di: {script_path}{RESET}")
        input("\nTekan Enter untuk kembali...")
        return False

# ================= Main App =================

def app_loop():
    """Loop utama aplikasi"""
    while True:
        choice = terminal_menu()
        
        if choice == "1":  # FREQUENCY - langsung jalankan script
            clear_screen()
            print(f"\n{COLORS['green']}[+] Starting FREQUENCY...{RESET}\n")
            time.sleep(1)
            if run_frequency_script():
                return  # Script akan menggantikan proses
            # Jika return False, lanjutkan loop
                    
        elif choice == "2":  # SOSIALS
            while True:
                sos_choice = sosials_menu()
                
                if sos_choice == "0":
                    break
                elif sos_choice == "1":
                    clear_screen()
                    print(f"\n{COLORS['green']}[+] Starting Social Media Scanner...{RESET}\n")
                    time.sleep(1)
                    if run_sosials_script():
                        return  # Script akan menggantikan proses
                    # Jika return False, lanjutkan loop
                elif sos_choice == "2":
                    clear_screen()
                    print(f"\n{COLORS['green']}[+] Starting Social Media Analysis...{RESET}\n")
                    time.sleep(1)
                    input("\nTekan Enter untuk kembali...")
                elif sos_choice == "3":
                    clear_screen()
                    print(f"\n{COLORS['green']}[+] Exporting Data...{RESET}\n")
                    time.sleep(1)
                    input("\nTekan Enter untuk kembali...")
                else:
                    print(f"\n{COLORS['red']}[!] Pilihan tidak valid!{RESET}")
                    time.sleep(1)
                    
        elif choice == "0":  # BACK
            clear_screen()
            print(f"\n{COLORS['green']}[+] Kembali ke menu utama...{RESET}")
            time.sleep(0.5)
            break
            
        else:
            print(f"\n{COLORS['red']}[!] Pilihan tidak valid!{RESET}")
            time.sleep(1)

def main():
    try:
        app_loop()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n{COLORS['yellow']}[!] Program dihentikan oleh user{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()