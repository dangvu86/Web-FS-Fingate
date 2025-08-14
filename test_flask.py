try:
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return '<h1>Flask is working!</h1>'
    
    print("Flask imported successfully!")
    print("Starting test server...")
    app.run(host='0.0.0.0', port=8000, debug=True)
    
except ImportError as e:
    print(f"Flask import error: {e}")
except Exception as e:
    print(f"Other error: {e}")