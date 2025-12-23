from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run with improved reload settings
    app.run(
        debug=True,
        port=8501,
        use_reloader=True,
        reloader_type='stat'  # Use stat-based reloader instead of watchdog to avoid threading issues
    )