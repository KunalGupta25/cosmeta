from discord_webhook import DiscordWebhook, DiscordEmbed
from models import SiteSettings
from flask import url_for

def send_discord_notification(chapter, base_url):
    """
    Send a Discord notification when a new chapter is published
    
    Args:
        chapter: The Chapter object that was published
        base_url: The base URL of the website (for generating the chapter URL)
    """
    # Get site settings
    settings = SiteSettings.query.first()
    
    # Check if Discord notifications are enabled and webhook URL is set
    if not settings or not settings.discord_notifications_enabled or not settings.discord_webhook_url:
        return False
    
    try:
        # Format the message using the template from settings
        chapter_url = f"{base_url.rstrip('/')}{url_for('chapter', chapter_id=chapter.id)}"
        message = settings.discord_new_chapter_message.format(
            title=chapter.title,
            sequence=chapter.sequence,
            url=chapter_url
        )
        
        # Create webhook
        webhook = DiscordWebhook(url=settings.discord_webhook_url, content=message)
        
        # Add embed with more details
        embed = DiscordEmbed(
            title=f"Chapter {chapter.sequence}: {chapter.title}",
            description=chapter.content[:200] + "..." if len(chapter.content) > 200 else chapter.content,
            color="9B59B6"  # Purple color
        )
        
        # Add chapter image if available
        if chapter.cover_image:
            embed.set_thumbnail(url=f"{base_url.rstrip('/')}/static/uploads/{chapter.cover_image}")
        
        # Add timestamp
        embed.set_timestamp()
        
        # Add footer
        embed.set_footer(text=settings.site_name)
        
        # Add embed to webhook
        webhook.add_embed(embed)
        
        # Execute webhook
        response = webhook.execute()
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Discord notification: {str(e)}")
        return False