"""Helper script to set up Discord bot token."""

import os
from pathlib import Path

def setup_bot_token():
    """Interactive setup for Discord bot token."""
    print("🤖 Discord Bot Setup")
    print("=" * 50)
    print("\n1. Go to https://discord.com/developers/applications")
    print("2. Click 'New Application'")
    print("3. Give it a name (e.g., 'Quillix Bot')")
    print("4. Go to 'Bot' section")
    print("5. Click 'Add Bot'")
    print("6. Copy the bot token")
    print("\n7. Invite the bot to your server:")
    print("   - Go to OAuth2 > URL Generator")
    print("   - Select 'bot' scope")
    print("   - Select permissions: Send Messages, Read Message History")
    print("   - Use the generated URL to invite the bot")
    
    token = input("\n🔑 Enter your Discord bot token: ").strip()
    
    if not token:
        print("❌ No token provided!")
        return
    
    # Find .env file
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print(f"❌ .env file not found at {env_file}")
        return
    
    # Read existing .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add bot token
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('DISCORD_BOT_TOKEN='):
            lines[i] = f'DISCORD_BOT_TOKEN={token}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'DISCORD_BOT_TOKEN={token}\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Bot token saved to {env_file}")
    print("\n🚀 Now restart your backend with: ./run.sh")
    print("📱 Create a channel named 'bot-commands' in your Discord server")
    print("🎯 Test with: !ping")

if __name__ == "__main__":
    setup_bot_token()