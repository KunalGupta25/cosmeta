import os
from flask import Flask
from models import db, User, ReadingProgress, UserPreference, TeamMember, ContactMessage, SiteSettings
from sqlalchemy import inspect, text

def create_app():
    app = Flask(__name__)
    
    # Try to connect to PostgreSQL using the Aiven connection string
    try:
        import psycopg2
        # Get the connection string from environment variables
        conn_string = os.getenv('DATABASE_URL')
        # Test the connection
        conn = psycopg2.connect(conn_string)
        conn.close()
        # If successful, use this connection string
        app.config['SQLALCHEMY_DATABASE_URI'] = conn_string
        print("Successfully connected to PostgreSQL database.")
    except Exception as e:
        print(f"Warning: Could not connect to PostgreSQL database. Using SQLite instead. Error: {e}")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cosmeta.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def check_and_update_columns():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Check User table
        user_columns = [column['name'] for column in inspector.get_columns('user')]
        
        # Add missing columns to User table
        missing_columns = []
        if 'display_name' not in user_columns:
            missing_columns.append("ADD COLUMN display_name VARCHAR(120)")
        if 'bio' not in user_columns:
            missing_columns.append("ADD COLUMN bio TEXT")
        if 'last_login' not in user_columns:
            missing_columns.append("ADD COLUMN last_login TIMESTAMP DEFAULT NOW()")
        if 'theme_preference' not in user_columns:
            missing_columns.append("ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'system'")
        
        if missing_columns:
            alter_user_sql = f"ALTER TABLE \"user\" {', '.join(missing_columns)};"
            print(f"Executing: {alter_user_sql}")
            db.session.execute(text(alter_user_sql))
            db.session.commit()
            print("User table updated successfully.")
        
        # Check ReadingProgress table
        reading_progress_columns = [column['name'] for column in inspector.get_columns('reading_progress')]
        
        # Add missing columns to ReadingProgress table
        missing_columns = []
        if 'completed' not in reading_progress_columns:
            missing_columns.append("ADD COLUMN completed BOOLEAN DEFAULT FALSE")
        if 'created_at' not in reading_progress_columns:
            missing_columns.append("ADD COLUMN created_at TIMESTAMP DEFAULT NOW()")
        if 'updated_at' not in reading_progress_columns:
            missing_columns.append("ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()")
        
        if missing_columns:
            alter_reading_progress_sql = f"ALTER TABLE reading_progress {', '.join(missing_columns)};"
            print(f"Executing: {alter_reading_progress_sql}")
            db.session.execute(text(alter_reading_progress_sql))
            db.session.commit()
            print("ReadingProgress table updated successfully.")
        
        # Create UserPreference table if it doesn't exist
        if not inspector.has_table('user_preference'):
            print("Creating UserPreference table...")
            UserPreference.__table__.create(db.engine)
            print("UserPreference table created successfully.")
        
        # Create TeamMember table if it doesn't exist
        if not inspector.has_table('team_member'):
            print("Creating TeamMember table...")
            TeamMember.__table__.create(db.engine)
            print("TeamMember table created successfully.")
        
        # Create ContactMessage table if it doesn't exist
        if not inspector.has_table('contact_message'):
            print("Creating ContactMessage table...")
            ContactMessage.__table__.create(db.engine)
            print("ContactMessage table created successfully.")
        
        # Create SiteSettings table if it doesn't exist
        if not inspector.has_table('site_settings'):
            print("Creating SiteSettings table...")
            SiteSettings.__table__.create(db.engine)
            print("SiteSettings table created successfully.")
            
            # Create default site settings
            default_settings = SiteSettings()
            db.session.add(default_settings)
            db.session.commit()
            print("Default site settings created.")

if __name__ == "__main__":
    check_and_update_columns()