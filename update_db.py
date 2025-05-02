from app import app, db
from models import SiteSettings
import sys

def update_site_settings_table():
    """
    Update the site_settings table to add the new columns
    """
    with app.app_context():
        try:
            # Check if we need to add site_name column
            try:
                # Try to access the site_name column
                SiteSettings.query.first()
                print("Database schema is already up to date.")
                return True
            except Exception as e:
                if "column site_settings.site_name does not exist" in str(e):
                    print("Updating database schema...")
                    # Add the new columns
                    with db.engine.connect() as conn:
                        conn.execute(db.text('ALTER TABLE site_settings ADD COLUMN site_name VARCHAR(120) DEFAULT \'Cosmeta: Incarnate\''))
                        conn.execute(db.text('ALTER TABLE site_settings ADD COLUMN site_description TEXT DEFAULT \'A web novel platform\''))
                        conn.execute(db.text('ALTER TABLE site_settings ADD COLUMN discord_channel_id VARCHAR(120)'))
                        conn.execute(db.text('ALTER TABLE site_settings ADD COLUMN discord_new_chapter_message TEXT DEFAULT \'📚 **New Chapter Alert!** 📚\n\n**{title}** (Chapter {sequence}) has just been published!\n\nRead it now: {url}\''))
                        conn.execute(db.text('ALTER TABLE site_settings ADD COLUMN discord_notifications_enabled BOOLEAN DEFAULT FALSE'))
                        conn.commit()
                    
                    print("Database schema updated successfully!")
                    return True
                else:
                    raise e
        except Exception as e:
            print(f"Error updating database schema: {str(e)}")
            return False

if __name__ == "__main__":
    success = update_site_settings_table()
    sys.exit(0 if success else 1)