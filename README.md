# Cosmeta: Incarnate

![Cosmeta logo](static/images/logo.png)

Cosmeta: Incarnate is a Flask-based e-novel platform for reading chapters, tracking progress, managing content, and running Discord-based role access for users, supporters, authors, and admins.

## Screenshots

Homepage
![Homepage](https://github.com/user-attachments/assets/83c52065-f2d9-4f3e-a78b-3107c2f8a0ab)

Admin dashboard for user management
![Admin dashboard](https://github.com/user-attachments/assets/f3e71032-df4a-416f-80b1-1772aedc8db1)

Author dashboard for chapter management
![Author dashboard](https://github.com/user-attachments/assets/4dac3255-9d45-4c9d-b69b-ad18fd684774)

## Features

- Discord OAuth2 login and guild-based role checks
- Role-based access control for users, supporters, authors, and admins
- Chapter creation, editing, deletion, and reordering
- Reading progress tracking per user and chapter
- Chapter comments and discussion
- Discord notifications when new chapters are published
- RSS feed support for chapter updates
- Responsive layout for desktop and mobile
- Admin tools for user management, site settings, and team profiles

## Tech Stack

- Backend: Flask, Python
- Database: PostgreSQL in production, with SQLite fallback for local or degraded environments
- Authentication: Discord OAuth2 via Authlib
- Forms: Flask-WTF and WTForms
- ORM: Flask-SQLAlchemy
- Deployment: Vercel
- Notifications: Discord webhook integration

## Project Structure

```
cosmeta/
├── app.py
├── models.py
├── forms.py
├── utils.py
├── update_db.py
├── promote_user.py
├── static/
│   ├── css/
│   ├── images/
│   ├── js/
│   └── uploads/
├── templates/
│   ├── admin/
│   └── *.html
├── requirements.txt
├── vercel.json
├── example.env
└── README.md
```

## Requirements

- Python 3.8 or newer
- A PostgreSQL database, such as Neon, Supabase, or another managed provider
- A Discord Developer Application
- Vercel account if you want to deploy there

## Environment Variables

Copy [example.env](example.env) to `.env` and set the values below.

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require

DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret
DISCORD_GUILD_ID=your-discord-guild-id
DISCORD_SUPPORTER_ROLE_ID=your-supporter-role-id
DISCORD_BOT_TOKEN=your-discord-bot-token

SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

Only `DATABASE_URL` is required for the database connection used by the app. The other variables are used for Discord authentication, role checks, and optional integrations.

## Local Setup

1. Clone the repository.

   ```bash
   git clone https://github.com/KunalGupta25/cosmeta.git
   cd cosmeta
   ```

2. Create and activate a virtual environment.

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Configure your environment.

   - Copy `example.env` to `.env`
   - Fill in `SECRET_KEY`, `DATABASE_URL`, and the Discord values

5. Run the app.

   ```bash
   flask --app app run
   ```

The app initializes database tables on startup, so a fresh database can be used without a manual migration step.

## Discord Setup

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application.
3. Add an OAuth2 redirect URL:
   - Local development: `http://localhost:5000/authorize`
   - Production: `https://your-domain.com/authorize`
4. Copy the client ID and client secret into your environment variables.
5. Create a bot for the application.
6. Enable the Server Members Intent under Privileged Gateway Intents.
7. Add your Discord guild ID, supporter role ID, and bot token to the environment.

## Deployment to Vercel

1. Push the repository to GitHub.
2. Import the project into Vercel.
3. Set the environment variables in the Vercel dashboard.
   - Required: `SECRET_KEY`, `DATABASE_URL`, and the Discord variables you use
4. Deploy using the default Vercel Python setup defined in [vercel.json](vercel.json).
5. Verify the deployment URL after the build completes.

### Vercel Notes

- Vercel’s filesystem is read-only at runtime, so the app avoids writing to project folders during startup.
- If `DATABASE_URL` is unavailable or the database tables are missing, the app now initializes tables on boot.
- File uploads on Vercel should be treated carefully because serverless storage is ephemeral.

## Useful URLs

- Home page: `/`
- Login: `/login`
- Author dashboard: `/dashboard`
- Admin dashboard: `/admin`
- RSS feed: `/rss.xml`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support Me

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Y8Y6IPAOF)
