# Cosmeta: Incarnate - E-Novel Platform

A Flask-based web application that allows users to read, upload, and manage e-novel chapters with Discord OAuth2 integration and role-based access control.

## Features

- **Discord OAuth2 Authentication**: Users log in with their Discord accounts
- **Role-Based Access Control**:
  - **User**: Can read chapters, track reading progress, but access new chapters 24 hrs after release
  - **Supporter**: Same as User, but can access new chapters instantly
  - **Author**: Can upload/edit/delete chapters, reorder them, and has all user + supporter rights
  - **Admin**: Can manage users (delete, promote/demote), and has full access to all features
- **Chapter Management**: Authors can create, edit, delete, and reorder chapters
- **Reading Progress Tracking**: Users' reading progress is automatically saved
- **Comments System**: Users can comment on chapters
- **Discord Notifications**: Automatic Discord notifications when new chapters are published
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL (via Supabase or direct connection)
- **Authentication**: Discord OAuth2
- **Deployment**: Vercel-compatible

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Discord Developer Application

### Environment Variables

Copy the `example.env` file to `.env` and fill in the required values:

```
# Flask configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@host:port/database

# Discord OAuth2 configuration
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret
DISCORD_GUILD_ID=your-discord-server-id
DISCORD_SUPPORTER_ROLE_ID=your-supporter-role-id
DISCORD_BOT_TOKEN=your-discord-bot-token

# Supabase configuration (if using Supabase)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

### Discord Application Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "OAuth2" section
4. Add a redirect URL: `https://your-domain.com/authorize` (or `http://localhost:5000/authorize` for local development)
5. Copy the Client ID and Client Secret to your `.env` file
6. Go to the "Bot" section and create a bot
7. Enable the "Server Members Intent" under Privileged Gateway Intents

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/cosmeta-incarnate.git
   cd cosmeta-incarnate
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. Run the application:
   ```
   flask run
   ```

### Deployment to Vercel

1. Install the Vercel CLI:
   ```
   npm install -g vercel
   ```

2. Deploy to Vercel:
   ```
   vercel
   ```

3. Set up environment variables in the Vercel dashboard.

## Project Structure

```
cosmeta-incarnate/
├── app.py                 # Main application file
├── models.py              # Database models
├── forms.py               # Form definitions
├── utils.py               # Utility functions (Discord notifications, etc.)
├── update_db.py           # Database migration script
├── static/                # Static files (CSS, JS, images)
│   ├── css/               # CSS stylesheets
│   │   ├── style.css      # Main stylesheet
│   │   ├── themes.css     # Theme-specific styles
│   │   ├── admin.css      # Admin panel styles
│   │   └── profile.css    # User profile styles
│   ├── js/                # JavaScript files
│   ├── images/            # Image assets
│   └── uploads/           # Uploaded chapter cover images
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Home page
│   ├── chapter.html       # Chapter view
│   ├── chapters.html      # All chapters page
│   ├── dashboard.html     # Author dashboard
│   ├── admin/             # Admin templates
│   │   ├── dashboard.html # Admin dashboard
│   │   ├── settings.html  # Site settings
│   │   └── team.html      # Team management
│   ├── chapter_form.html  # Chapter creation/editing form
│   ├── profile.html       # User profile page
│   ├── feed.html          # RSS feed HTML view
│   ├── 404.html           # 404 error page
│   └── 500.html           # 500 error page
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel configuration
├── example.env            # Example environment variables
└── .env                   # Environment variables (not in repo)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.