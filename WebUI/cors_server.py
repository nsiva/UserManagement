#!/usr/bin/env python3
"""
Simple HTTP server with CORS headers for testing CSS themes
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🌐 CORS-enabled server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {httpd.server_address}")
        print(f"🎨 CSS available at: http://localhost:{PORT}/TEST_THEME.css")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()