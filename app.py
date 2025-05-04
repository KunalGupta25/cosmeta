import os
import random
from flask import Flask, render_template, redirect, url_for, flash, request, session, Response, make_response, send_from_directory
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from dotenv import load_dotenv
from datetime import datetime, timedelta
from authlib.integrations.flask_client import OAuth
import json
import xml.etree.ElementTree as ET
from werkzeug.utils import secure_filename
from models import db, User, Chapter, ReadingProgress, Comment, UserPreference, TeamMember, ContactMessage, SiteSettings
from forms import ChapterForm, CommentForm
from functools import wraps
from utils import send_discord_notification

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')

# Try to connect to PostgreSQL using the DATABASE_URL from environment variables
try:
    import psycopg2
    # Get the connection string from environment variables
    conn_string = os.getenv('DATABASE_URL')
    
    # Ensure the connection string uses postgresql:// instead of postgres://
    if conn_string and conn_string.startswith('postgres://'):
        conn_string = conn_string.replace('postgres://', 'postgresql://', 1)
    
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
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize OAuth
oauth = OAuth(app)
discord = oauth.register(
    name='discord',
    client_id=os.getenv('DISCORD_CLIENT_ID'),
    client_secret=os.getenv('DISCORD_CLIENT_SECRET'),
    access_token_url='https://discord.com/api/oauth2/token',
    access_token_params=None,
    authorize_url='https://discord.com/api/oauth2/authorize',
    authorize_params=None,
    api_base_url='https://discord.com/api/',
    client_kwargs={'scope': 'identify guilds'},
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom decorators for role-based access control
def supporter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role < User.ROLE_SUPPORTER:
            flash('This page requires supporter access.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def author_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role < User.ROLE_AUTHOR:
            flash('This page requires author access.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role < User.ROLE_ADMIN:
            flash('This page requires admin access.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to add variables to all templates
@app.context_processor
def inject_now():
    return {
        'now': datetime.utcnow(),
        'datetime': datetime,
        'timedelta': timedelta
    }

@app.context_processor
def inject_user_preferences():
    if current_user.is_authenticated:
        user_preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
        if not user_preferences:
            user_preferences = UserPreference(user_id=current_user.id, theme='system')
            db.session.add(user_preferences)
            db.session.commit()
        return {'user_preferences': user_preferences}
    return {'user_preferences': None}

# Routes
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                               'logo.png', mimetype='image/png')

@app.route('/')
def index():
    # Get latest chapters (only 3)
    latest_chapters = Chapter.query.order_by(Chapter.created_at.desc()).limit(3).all()
    return render_template('index.html', latest_chapters=latest_chapters)

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return discord.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = discord.authorize_access_token()
    resp = discord.get('users/@me', token=token)
    user_info = resp.json()
    
    # Get user's guilds to check for roles
    guilds_resp = discord.get('users/@me/guilds', token=token)
    guilds = guilds_resp.json()
    
    # Check if user is in our specific Discord server
    target_guild_id = os.getenv('DISCORD_GUILD_ID')
    is_in_guild = any(g['id'] == target_guild_id for g in guilds)
    
    # If user is in our guild, get their roles
    user_role = User.ROLE_USER  # Default role
    if is_in_guild:
        # Get member info from the guild to check roles
        # Note: This requires the bot to have proper permissions
        try:
            # We need to use the bot token for this request, not the user token
            # This is a limitation of Discord's API
            headers = {
                'Authorization': f'Bot {os.getenv("DISCORD_BOT_TOKEN")}',
                'Content-Type': 'application/json'
            }
            
            # Make a direct request to Discord API
            import requests
            member_resp = requests.get(
                f'https://discord.com/api/v10/guilds/{target_guild_id}/members/{user_info["id"]}',
                headers=headers
            )
            
            if member_resp.status_code == 200:
                member_info = member_resp.json()
                # Check if user has the "Supporter" role
                supporter_role_id = os.getenv('DISCORD_SUPPORTER_ROLE_ID')
                
                # Debug information
                print(f"User roles: {member_info.get('roles', [])}")
                print(f"Looking for supporter role: {supporter_role_id}")
                
                if supporter_role_id in member_info.get('roles', []):
                    user_role = User.ROLE_SUPPORTER
                    print(f"User {user_info['username']} has Supporter role in Discord")
            else:
                print(f"Failed to get member info: {member_resp.status_code} - {member_resp.text}")
        except Exception as e:
            print(f"Error checking Discord roles: {e}")
    
    # Find or create user
    user = User.query.filter_by(discord_id=user_info['id']).first()
    
    # Check if this is the first user (make them admin)
    is_first_user = User.query.count() == 0
    
    if not user:
        # If this is the first user to log in, make them an admin
        if is_first_user:
            user_role = User.ROLE_ADMIN
            print(f"First user {user_info['username']} created as Admin")
            flash(f"Welcome! As the first user, you've been granted Admin privileges.", "success")
        
        user = User(
            discord_id=user_info['id'],
            username=user_info['username'],
            avatar=user_info.get('avatar'),
            role=user_role
        )
        db.session.add(user)
    else:
        # Update existing user info
        user.username = user_info['username']
        user.avatar = user_info.get('avatar')
        # Only upgrade role, never downgrade automatically
        if user_role > user.role:
            user.role = user_role
    
    db.session.commit()
    login_user(user)
    
    # Redirect to last read chapter if available
    last_progress = ReadingProgress.query.filter_by(user_id=user.id).order_by(ReadingProgress.last_read.desc()).first()
    if last_progress:
        return redirect(url_for('chapter', chapter_id=last_progress.chapter_id))
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/request-supporter', methods=['GET', 'POST'])
@login_required
def request_supporter():
    if request.method == 'POST':
        discord_username = request.form.get('discord_username')
        message = request.form.get('message', '')
        
        # Create a notification for admins (you could store this in the database)
        # For now, we'll just flash a message
        flash('Your supporter role request has been submitted. An admin will review it soon.', 'success')
        
        # You could also send an email to admins or create a database entry
        # to track these requests
        
        return redirect(url_for('index'))
    
    return render_template('request_supporter.html')

@app.route('/chapters')
def chapters():
    # Get all chapters, ordered by sequence
    all_chapters = Chapter.query.order_by(Chapter.sequence).all()
    return render_template('chapters.html', chapters=all_chapters)

@app.route('/profile')
@login_required
def profile():
    # Get all chapters
    all_chapters = Chapter.query.order_by(Chapter.sequence).all()
    
    # Get user's reading progress
    user_progress = ReadingProgress.query.filter_by(user_id=current_user.id).all()
    
    # Create a dictionary of chapter_id -> ReadingProgress
    reading_progress = {progress.chapter_id: progress for progress in user_progress}
    
    # Get list of read chapter IDs
    read_chapter_ids = [progress.chapter_id for progress in user_progress if progress.completed]
    
    # Get last read chapter
    last_read = ReadingProgress.query.filter_by(user_id=current_user.id).order_by(ReadingProgress.last_read.desc()).first()
    
    # Calculate reading stats
    total_chapters = len(all_chapters)
    total_chapters_read = len(read_chapter_ids)
    completion_percentage = round((total_chapters_read / total_chapters) * 100) if total_chapters > 0 else 0
    
    reading_stats = {
        'total_chapters': total_chapters,
        'total_chapters_read': total_chapters_read,
        'completion_percentage': completion_percentage
    }
    
    # Get user preferences
    user_preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not user_preferences:
        user_preferences = UserPreference(user_id=current_user.id, theme='system')
        db.session.add(user_preferences)
        db.session.commit()
    
    return render_template('profile.html', 
                          all_chapters=all_chapters,
                          reading_progress=reading_progress,
                          read_chapter_ids=read_chapter_ids,
                          last_read=last_read,
                          reading_stats=reading_stats,
                          user_preferences=user_preferences)

@app.route('/mark-read/<int:chapter_id>', methods=['POST'])
@login_required
def mark_read(chapter_id):
    # Check if chapter exists
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Check if progress already exists
    progress = ReadingProgress.query.filter_by(user_id=current_user.id, chapter_id=chapter_id).first()
    
    if progress:
        progress.completed = True
        progress.last_read = datetime.utcnow()
        progress.updated_at = datetime.utcnow()
    else:
        progress = ReadingProgress(
            user_id=current_user.id,
            chapter_id=chapter_id,
            completed=True,
            last_read=datetime.utcnow()
        )
        db.session.add(progress)
    
    db.session.commit()
    flash('Chapter marked as read!', 'success')
    return redirect(url_for('profile'))

@app.route('/mark-unread/<int:chapter_id>', methods=['POST'])
@login_required
def mark_unread(chapter_id):
    # Check if chapter exists
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Check if progress exists
    progress = ReadingProgress.query.filter_by(user_id=current_user.id, chapter_id=chapter_id).first()
    
    if progress:
        progress.completed = False
        progress.updated_at = datetime.utcnow()
        db.session.commit()
    
    flash('Chapter marked as unread!', 'success')
    return redirect(url_for('profile'))

@app.route('/save-preferences', methods=['POST'])
@login_required
def save_preferences():
    theme = request.form.get('theme', 'system')
    
    # Get user preferences
    user_preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if user_preferences:
        user_preferences.theme = theme
    else:
        user_preferences = UserPreference(user_id=current_user.id, theme=theme)
        db.session.add(user_preferences)
    
    db.session.commit()
    flash('Preferences saved!', 'success')
    return redirect(url_for('profile'))

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    bio = request.form.get('bio')
    current_user.bio = bio
    
    # Handle profile image upload
    if 'profile_image' in request.files and request.files['profile_image'].filename:
        try:
            file = request.files['profile_image']
            filename = secure_filename(file.filename)
            
            # Add timestamp to filename to prevent caching issues
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"profile_{current_user.id}_{timestamp}_{filename}"
            
            # Save the file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Update user avatar
            current_user.avatar = url_for('static', filename=f'uploads/{filename}')
            
            flash('Profile image updated!', 'success')
        except Exception as e:
            flash(f'Error uploading image: {str(e)}', 'error')
    
    db.session.commit()
    flash('Profile updated!', 'success')
    return redirect(url_for('profile'))

@app.route('/about')
def about():
    # Get team members
    team_members = TeamMember.query.order_by(TeamMember.order).all()
    
    # Get site settings
    site_settings = SiteSettings.query.first()
    
    return render_template('about.html', team_members=team_members, site_settings=site_settings)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # Get site settings
    site_settings = SiteSettings.query.first()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Create contact message
        contact_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(contact_message)
        db.session.commit()
        
        # Send to Discord webhook if configured
        if site_settings and site_settings.discord_webhook_url:
            try:
                import requests
                webhook_url = site_settings.discord_webhook_url
                
                # Format message for Discord
                discord_message = {
                    "embeds": [{
                        "title": f"New Contact Message: {subject}",
                        "description": message,
                        "color": 8388736,  # Purple color
                        "fields": [
                            {"name": "Name", "value": name, "inline": True},
                            {"name": "Email", "value": email, "inline": True},
                            {"name": "User ID", "value": str(current_user.id) if current_user.is_authenticated else "Not logged in", "inline": True}
                        ],
                        "timestamp": datetime.utcnow().isoformat()
                    }]
                }
                
                # Send to Discord
                response = requests.post(webhook_url, json=discord_message)
                if response.status_code == 204:
                    print("Message sent to Discord successfully")
                else:
                    print(f"Failed to send message to Discord: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error sending to Discord: {e}")
        
        flash('Your message has been sent! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', site_settings=site_settings)

@app.route('/admin/team', methods=['GET', 'POST'])
@admin_required
def admin_team():
    # Get all team members
    team_members = TeamMember.query.order_by(TeamMember.order).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name')
            role = request.form.get('role')
            bio = request.form.get('bio')
            user_id = request.form.get('user_id')
            twitter = request.form.get('twitter')
            discord = request.form.get('discord')
            instagram = request.form.get('instagram')
            website = request.form.get('website')
            order = request.form.get('order', 0)
            
            # Handle photo upload
            photo = None
            if 'photo' in request.files and request.files['photo'].filename:
                try:
                    file = request.files['photo']
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    photo = filename
                except Exception as e:
                    flash(f"Error uploading photo: {e}", "error")
            
            # Create team member
            team_member = TeamMember(
                name=name,
                role=role,
                bio=bio,
                user_id=user_id if user_id else None,
                photo=photo,
                twitter=twitter,
                discord=discord,
                instagram=instagram,
                website=website,
                order=order
            )
            db.session.add(team_member)
            db.session.commit()
            flash('Team member added successfully!', 'success')
            
        elif action == 'edit':
            member_id = request.form.get('member_id')
            team_member = TeamMember.query.get_or_404(member_id)
            
            team_member.name = request.form.get('name')
            team_member.role = request.form.get('role')
            team_member.bio = request.form.get('bio')
            team_member.user_id = request.form.get('user_id') or None
            team_member.twitter = request.form.get('twitter')
            team_member.discord = request.form.get('discord')
            team_member.instagram = request.form.get('instagram')
            team_member.website = request.form.get('website')
            team_member.order = request.form.get('order', 0)
            
            # Handle photo upload
            if 'photo' in request.files and request.files['photo'].filename:
                try:
                    # Delete old photo if it exists
                    if team_member.photo:
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], team_member.photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    file = request.files['photo']
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    team_member.photo = filename
                except Exception as e:
                    flash(f"Error uploading photo: {e}", "error")
            
            db.session.commit()
            flash('Team member updated successfully!', 'success')
            
        elif action == 'delete':
            member_id = request.form.get('member_id')
            team_member = TeamMember.query.get_or_404(member_id)
            
            # Delete photo if it exists
            if team_member.photo:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], team_member.photo)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            
            db.session.delete(team_member)
            db.session.commit()
            flash('Team member deleted successfully!', 'success')
        
        return redirect(url_for('admin_team'))
    
    # Get all users for the dropdown
    users = User.query.all()
    
    return render_template('admin/team.html', team_members=team_members, users=users)

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    # Get site settings
    site_settings = SiteSettings.query.first()
    if not site_settings:
        site_settings = SiteSettings()
        db.session.add(site_settings)
        db.session.commit()
    
    if request.method == 'POST':
        # General settings
        site_settings.site_name = request.form.get('site_name')
        site_settings.site_description = request.form.get('site_description')
        site_settings.contact_email = request.form.get('contact_email')
        site_settings.about_page_content = request.form.get('about_page_content')
        
        # Discord notification settings
        site_settings.discord_webhook_url = request.form.get('discord_webhook_url')
        site_settings.discord_channel_id = request.form.get('discord_channel_id')
        site_settings.discord_new_chapter_message = request.form.get('discord_new_chapter_message')
        site_settings.discord_notifications_enabled = 'discord_notifications_enabled' in request.form
        
        db.session.commit()
        flash('Site settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html', site_settings=site_settings)

@app.route('/chapter/<int:chapter_id>')
@login_required
def chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Check if user has access to this chapter
    if current_user.role < User.ROLE_SUPPORTER:
        # Regular users need to wait 24 hours after release
        if chapter.created_at > datetime.utcnow() - timedelta(hours=24):
            flash('This chapter is only available to supporters for the first 24 hours after release.', 'info')
            return redirect(url_for('index'))
    
    # Get previous and next chapters
    prev_chapter = Chapter.query.filter(Chapter.sequence < chapter.sequence).order_by(Chapter.sequence.desc()).first()
    next_chapter = Chapter.query.filter(Chapter.sequence > chapter.sequence).order_by(Chapter.sequence.asc()).first()
    
    # Update reading progress
    progress = ReadingProgress.query.filter_by(user_id=current_user.id, chapter_id=chapter.id).first()
    if not progress:
        progress = ReadingProgress(
            user_id=current_user.id, 
            chapter_id=chapter.id,
            completed=True,
            created_at=datetime.utcnow()
        )
        db.session.add(progress)
    else:
        progress.completed = True  # Mark as completed when reading
    
    progress.last_read = datetime.utcnow()
    progress.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Get comments
    comments = Comment.query.filter_by(chapter_id=chapter.id).order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm()
    
    return render_template('chapter.html', chapter=chapter, prev_chapter=prev_chapter, 
                          next_chapter=next_chapter, comments=comments, form=comment_form)

@app.route('/chapter/<int:chapter_id>/comment', methods=['POST'])
@login_required
def add_comment(chapter_id):
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            chapter_id=chapter_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
    return redirect(url_for('chapter', chapter_id=chapter_id))

# Author routes
@app.route('/dashboard')
@author_required
def dashboard():
    chapters = Chapter.query.order_by(Chapter.sequence).all()
    return render_template('dashboard.html', chapters=chapters)

@app.route('/dashboard/chapter/new', methods=['GET', 'POST'])
@author_required
def new_chapter():
    form = ChapterForm()
    if form.validate_on_submit():
        # Find the highest sequence number
        max_sequence = db.session.query(db.func.max(Chapter.sequence)).scalar() or 0
        
        # Handle cover image upload
        cover_image = None
        if form.cover_image.data and form.cover_image.data.filename:
            try:
                print(f"Uploading file: {form.cover_image.data.filename}")
                
                # Ensure upload directory exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Get file extension
                _, file_extension = os.path.splitext(form.cover_image.data.filename)
                
                # Create a unique filename
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
                filename = f"{timestamp}_{random_suffix}{file_extension.lower()}"
                
                # Save the file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"Saving to: {filepath}")
                
                # Save the file
                form.cover_image.data.save(filepath)
                cover_image = filename
                print(f"File saved successfully as: {cover_image}")
            except Exception as e:
                print(f"Error uploading file: {str(e)}")
                flash(f"Error uploading cover image: {str(e)}", "danger")
        
        chapter = Chapter(
            title=form.title.data,
            content=form.content.data,
            sequence=max_sequence + 1,
            cover_image=cover_image
        )
        db.session.add(chapter)
        db.session.commit()
        
        # Send Discord notification for the new chapter
        base_url = request.url_root
        notification_sent = send_discord_notification(chapter, base_url)
        
        if notification_sent:
            flash('New chapter has been created and Discord notification sent!', 'success')
        else:
            flash('New chapter has been created!', 'success')
            
        return redirect(url_for('dashboard'))
    
    return render_template('chapter_form.html', form=form, title='New Chapter')

@app.route('/dashboard/chapter/<int:chapter_id>/edit', methods=['GET', 'POST'])
@author_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    form = ChapterForm(obj=chapter)
    
    if form.validate_on_submit():
        chapter.title = form.title.data
        chapter.content = form.content.data
        
        # Handle cover image upload
        if form.cover_image.data and form.cover_image.data.filename:
            try:
                print(f"Uploading file in edit mode: {form.cover_image.data.filename}")
                
                # Delete old image if it exists
                if chapter.cover_image:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], chapter.cover_image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                        print(f"Deleted old image: {old_image_path}")
                
                # Ensure upload directory exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Get file extension
                _, file_extension = os.path.splitext(form.cover_image.data.filename)
                
                # Create a unique filename
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
                filename = f"{timestamp}_{random_suffix}{file_extension.lower()}"
                
                # Save the file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"Saving to: {filepath}")
                
                # Save the file
                form.cover_image.data.save(filepath)
                chapter.cover_image = filename
                print(f"File saved successfully as: {filename}")
            except Exception as e:
                print(f"Error uploading file: {str(e)}")
                flash(f"Error uploading cover image: {str(e)}", "danger")
        
        db.session.commit()
        flash('Chapter has been updated!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('chapter_form.html', form=form, chapter=chapter, title='Edit Chapter')

@app.route('/dashboard/chapter/<int:chapter_id>/delete', methods=['POST'])
@author_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Delete cover image if it exists
    if chapter.cover_image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], chapter.cover_image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Delete associated reading progress and comments
    ReadingProgress.query.filter_by(chapter_id=chapter.id).delete()
    Comment.query.filter_by(chapter_id=chapter.id).delete()
    
    db.session.delete(chapter)
    db.session.commit()
    
    # Reorder remaining chapters
    chapters = Chapter.query.order_by(Chapter.sequence).all()
    for i, chap in enumerate(chapters, 1):
        chap.sequence = i
    db.session.commit()
    
    flash('Chapter has been deleted!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard/chapter/<int:chapter_id>/move/<direction>', methods=['POST'])
@author_required
def move_chapter(chapter_id, direction):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if direction == 'up' and chapter.sequence > 1:
        # Swap with the previous chapter
        prev_chapter = Chapter.query.filter_by(sequence=chapter.sequence - 1).first()
        if prev_chapter:
            prev_chapter.sequence, chapter.sequence = chapter.sequence, prev_chapter.sequence
    
    elif direction == 'down':
        # Swap with the next chapter
        next_chapter = Chapter.query.filter_by(sequence=chapter.sequence + 1).first()
        if next_chapter:
            next_chapter.sequence, chapter.sequence = chapter.sequence, next_chapter.sequence
    
    db.session.commit()
    return redirect(url_for('dashboard'))

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/user/<int:user_id>/role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role', type=int)
    
    # Validate role
    if new_role in [User.ROLE_USER, User.ROLE_SUPPORTER, User.ROLE_AUTHOR, User.ROLE_ADMIN]:
        user.role = new_role
        db.session.commit()
        flash(f'User {user.username} role has been updated!', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Delete user's reading progress and comments
    ReadingProgress.query.filter_by(user_id=user.id).delete()
    Comment.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/feed')
def feed_page():
    # HTML page for feed
    chapters = Chapter.query.order_by(Chapter.created_at.desc()).limit(20).all()
    return render_template('feed.html', chapters=chapters)

@app.route('/rss.xml')
def rss_feed_xml():
    """
    Generate a simple RSS feed in XML format for automation and feed readers.
    This endpoint always returns XML regardless of the Accept header.
    """
    try:
        # Get site settings
        site_settings = SiteSettings.query.first()
        site_name = site_settings.site_name if site_settings else "Cosmeta: Incarnate"
        site_description = site_settings.site_description if site_settings else "A web novel platform"
        
        # Get the latest chapters
        chapters = Chapter.query.order_by(Chapter.created_at.desc()).limit(20).all()
        
        # Create a simple RSS feed without complex namespaces
        rss = ET.Element('rss', {'version': '2.0'})
        channel = ET.SubElement(rss, 'channel')
        
        # Add channel information
        title = ET.SubElement(channel, 'title')
        title.text = site_name
        
        link = ET.SubElement(channel, 'link')
        link.text = request.url_root
        
        description = ET.SubElement(channel, 'description')
        description.text = site_description
        
        language = ET.SubElement(channel, 'language')
        language.text = 'en-us'
        
        # Add items (chapters)
        for chapter in chapters:
            item = ET.SubElement(channel, 'item')
            
            item_title = ET.SubElement(item, 'title')
            item_title.text = f"Chapter {chapter.sequence}: {chapter.title}"
            
            item_link = ET.SubElement(item, 'link')
            item_link.text = request.url_root.rstrip('/') + url_for('chapter', chapter_id=chapter.id)
            
            item_guid = ET.SubElement(item, 'guid')
            item_guid.text = request.url_root.rstrip('/') + url_for('chapter', chapter_id=chapter.id)
            
            item_pubDate = ET.SubElement(item, 'pubDate')
            item_pubDate.text = chapter.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # Add description
            item_description = ET.SubElement(item, 'description')
            if chapter.content:
                content_preview = chapter.content[:200] + '...' if len(chapter.content) > 200 else chapter.content
                item_description.text = content_preview
            else:
                item_description.text = "No preview available."
        
        # Convert to string
        xml_str = ET.tostring(rss, encoding='utf-8', method='xml')
        
        # Create response with proper headers
        response = make_response(xml_str)
        response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
        return response
        
    except Exception as e:
        # Log the error
        print(f"RSS Feed Error: {str(e)}")
        # Return a simple error response
        return f"Error generating RSS feed: {str(e)}", 500

@app.route('/rss')
def rss_feed():
    """
    Legacy RSS feed route that serves both HTML and XML based on the request
    """
    try:
        # Check if the request accepts HTML (browser) or XML (feed reader)
        best = request.accept_mimetypes.best_match(['text/html', 'application/rss+xml'])
        if best == 'text/html' and request.accept_mimetypes[best] > request.accept_mimetypes['application/rss+xml']:
            # Browser request - show HTML page
            chapters = Chapter.query.order_by(Chapter.created_at.desc()).limit(20).all()
            return render_template('feed.html', chapters=chapters)
        else:
            # RSS reader request - return XML
            return redirect(url_for('rss_feed_xml'))
    except Exception as e:
        print(f"RSS Route Error: {str(e)}")
        return f"Error processing RSS request: {str(e)}", 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)