import sys
import os
from simple_app import app

if __name__ == '__main__':
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    
    # Check if running in production (Render sets PORT env var)
    is_production = 'PORT' in os.environ
    
    if is_production:
        print(f"\nStarting FS Fingate Web Application in PRODUCTION mode...")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    else:
        print(f"\nStarting FS Fingate Web Application in DEVELOPMENT mode...")
        print(f"Server will be available at:")
        print(f"   - http://localhost:{port}")
        print(f"   - http://127.0.0.1:{port}")
        print(f"   - http://0.0.0.0:{port}")
        print(f"\nPress Ctrl+C to stop the server\n")
        
        try:
            app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
        except Exception as e:
            print(f"\nError starting server: {e}")
            sys.exit(1)