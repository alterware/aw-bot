# AlterWare's Discord Bot
This repo contains the AlterWare Bot written in python using discord.py

Contributions are welcome! Please follow the guidelines below:

- Sign [AlterWare CLA](https://alterware.dev/cla) and send a pull request or email your patch at patches@alterware.dev
- Make sure that PRs have only one commit, and deal with one issue only

## Discord gateway intents

The bot explicitly enables only the gateway intents it uses: guilds, members,
guild and DM messages, message content, guild reactions, and voice states.
Enable the **Server Members Intent** and **Message Content Intent** under
**Developer Portal > Application > Bot > Privileged Gateway Intents**. The
other enabled intents are not privileged.
