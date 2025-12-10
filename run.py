import os

# ✅ Set any environment variables if needed
# os.environ['PROJ_DATA'] = 'path_to_proj_data'  # Only if your project needs it

from website import create_app

app = create_app()  # ✅ create the Flask app

if __name__ == "__main__":
    # Only enable debug in development
    app.run(debug=True, port=5012)
