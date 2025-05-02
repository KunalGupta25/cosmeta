from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    # User roles
    ROLE_USER = 1
    ROLE_SUPPORTER = 2
    ROLE_AUTHOR = 3
    ROLE_ADMIN = 4
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(120))
    avatar = db.Column(db.String(255))
    bio = db.Column(db.Text)
    role = db.Column(db.Integer, default=ROLE_USER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    theme_preference = db.Column(db.String(20), default='system')
    
    # Relationships
    reading_progress = db.relationship('ReadingProgress', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def is_supporter(self):
        return self.role >= self.ROLE_SUPPORTER
    
    @property
    def is_author(self):
        return self.role >= self.ROLE_AUTHOR
    
    @property
    def is_admin(self):
        return self.role >= self.ROLE_ADMIN

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    cover_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reading_progress = db.relationship('ReadingProgress', backref='chapter', lazy=True)
    comments = db.relationship('Comment', backref='chapter', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Chapter {self.title}>'

class ReadingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    last_read = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'chapter_id', name='unique_user_chapter'),
    )
    
    def __repr__(self):
        return f'<ReadingProgress User:{self.user_id} Chapter:{self.chapter_id}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment {self.id} by User:{self.user_id}>'

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    theme = db.Column(db.String(20), default='system')  # 'system', 'light', or 'dark'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('preferences', uselist=False))
    
    def __repr__(self):
        return f'<UserPreference User:{self.user_id}>'

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text)
    photo = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    twitter = db.Column(db.String(255))
    discord = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    website = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='team_profile')
    
    def __repr__(self):
        return f'<TeamMember {self.name}>'

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='contact_messages')
    
    def __repr__(self):
        return f'<ContactMessage {self.id} from {self.name}>'

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(120), default="Cosmeta: Incarnate")
    site_description = db.Column(db.Text, default="A web novel platform")
    discord_webhook_url = db.Column(db.String(255))
    discord_channel_id = db.Column(db.String(120))
    discord_new_chapter_message = db.Column(db.Text, default="📚 **New Chapter Alert!** 📚\n\n**{title}** (Chapter {sequence}) has just been published!\n\nRead it now: {url}")
    discord_notifications_enabled = db.Column(db.Boolean, default=False)
    contact_email = db.Column(db.String(120))
    about_page_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteSettings {self.id}>'