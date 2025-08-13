import http.server
import socketserver
import webbrowser
import os
import sys
from urllib.parse import urlparse, parse_qs
import json
import tempfile
import zipfile
from io import BytesIO
import pandas as pd
from bs4 import BeautifulSoup
import gdown

class SimpleHTMLServer:
    def __init__(self, port=8080):
        self.port = port
        self.handler = self.create_handler()
    
    def create_handler(self):
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    with open('templates/index.html', 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Replace Flask endpoints with simple HTML forms
                        content = content.replace('/upload', '/upload')
                        content = content.replace('/download_drive', '/download_drive')
                        self.wfile.write(content.encode())
                else:
                    super().do_GET()
            
            def do_POST(self):
                if self.path == '/upload':
                    self.handle_upload()
                elif self.path == '/download_drive':
                    self.handle_drive_download()
                else:
                    self.send_error(404)
            
            def handle_upload(self):
                # Simple response for now
                response = {'message': 'Upload functionality - please use Flask version'}
                self.send_json_response(response)
            
            def handle_drive_download(self):
                # Simple response for now  
                response = {'message': 'Drive download functionality - please use Flask version'}
                self.send_json_response(response)
            
            def send_json_response(self, data):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
        
        return CustomHandler
    
    def start(self):
        try:
            with socketserver.TCPServer(("", self.port), self.handler) as httpd:
                print(f"🌐 Alternative server started at http://localhost:{self.port}")
                print(f"📂 Serving from: {os.getcwd()}")
                print(f"🛑 Press Ctrl+C to stop")
                
                # Try to open browser
                try:
                    webbrowser.open(f'http://localhost:{self.port}')
                except:
                    pass
                
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    server = SimpleHTMLServer()
    server.start()