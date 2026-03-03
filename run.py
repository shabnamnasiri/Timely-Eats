# run.py

# Import the create_app function from app/__init__.py
from app import create_app

# Import socketio if you want to add real-time later
from app.extensions import socketio

# Create the Flask application
app = create_app()

# Run the app with socketio (supports real-time later)
if __name__ == "__main__":
    # debug=True allows automatic reload on code change
    socketio.run(app, debug=True)