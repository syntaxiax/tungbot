# Discord Bot

A feature-rich Discord bot built with discord.py.

## Structure

```
bot.py              — Main entry point, bot setup and event handlers
cogs/
  general.py        — General utility commands
  fun.py            — Fun and entertainment commands
  moderation.py     — Server moderation commands
```

## Setup

Requires a `DISCORD_TOKEN` environment secret set to your bot token.

## Commands

### General (prefix: !)
- `!ping` — Check bot latency
- `!info` — Show bot info and uptime
- `!serverinfo` — Show server info
- `!userinfo [@user]` — Show user info
- `!avatar [@user]` — Show user avatar

### Fun
- `!roll [NdS]` — Roll dice (e.g. `!roll 2d6`)
- `!flip` — Flip a coin
- `!8ball <question>` — Ask the magic 8-ball
- `!choose <opt1, opt2, ...>` — Choose between options
- `!rps <rock/paper/scissors>` — Play rock paper scissors
- `!joke` — Tell a random joke

### Moderation (requires permissions)
- `!kick @user [reason]` — Kick a member
- `!ban @user [reason]` — Ban a member
- `!unban username` — Unban a user
- `!purge <amount>` — Delete messages (1-100)
- `!mute @user [minutes] [reason]` — Timeout a member
- `!unmute @user` — Remove timeout
- `!slowmode [seconds]` — Set channel slowmode

## Dependencies

- discord.py
- python-dotenv
