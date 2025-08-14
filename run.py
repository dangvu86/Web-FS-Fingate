import sys
import socket
from app import app

def find_free_port():
    """Find a free port to run the application"""
    for port in range(5000, 5100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    return 5000

if __name__ == '__main__':
    port = find_free_port()
    print(f"\n🚀 Starting FS Fingate Web Application...")
    print(f"📍 Server will be available at:")
    print(f"   - http://localhost:{port}")
    print(f"   - http://127.0.0.1:{port}")
    print(f"   - http://0.0.0.0:{port}")
    print(f"\n💡 If localhost doesn't work, try:")
    print(f"   - Check if Windows Firewall is blocking the connection")
    print(f"   - Try running as Administrator")
    print(f"   - Use http://127.0.0.1:{port} instead")
    print(f"\n🛑 Press Ctrl+C to stop the server\n")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print(f"💡 Try running: python -m flask run --host=0.0.0.0 --port={port}")
        sys.exit(1)