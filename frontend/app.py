"""
Flask Frontend for Gym Workout RAG System
Modern, scalable architecture with blueprints
"""

from flask import Flask, render_template
from api import api_bp
from utils import ServerManager


def create_app():
    """
    Application factory pattern for Flask app.
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Main routes
    @app.route('/')
    def index():
        """Render the main page."""
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """Frontend health check."""
        return {
            "status": "healthy",
            "service": "frontend",
            "version": "2.0.0"
        }
    
    return app


def main():
    """Main entry point for the application."""
    print("\n" + "=" * 60)
    print("  Gym Workout RAG - Starting Servers")
    print("=" * 60 + "\n")
    
    # Initialize server manager
    server_manager = ServerManager()
    
    # Start FastAPI backend
    server_manager.start_server()
    
    # Create Flask app
    app = create_app()
    
    print("\n" + "=" * 60)
    print("🌐 Starting Flask frontend server...")
    print(f"📍 Frontend: http://localhost:7500")
    print(f"📍 Backend API: {server_manager.fastapi_url}")
    print("\n💡 Press Ctrl+C to stop both servers")
    print("=" * 60 + "\n")
    
    try:
        app.run(debug=True, port=7500, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        server_manager.stop_server()
        print("✅ Shutdown complete")


if __name__ == '__main__':
    main()

# Made with Bob
