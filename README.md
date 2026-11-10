# spinner-bot

A Discord bot that spins a wheel to pick a random item.

Use `/spin`, enter one item per line, and the bot replies with an animated WebP of the wheel spinning and landing on a random item.

## Running

Create a `.env` file:

```env
DISCORD_TOKEN=your-bot-token
ENV=dev
```

Then run with Docker:

```sh
docker build -t spinner-bot .
docker run --env-file .env spinner-bot
```

To run locally instead, install `fonts-noto-cjk` and run `uv run main.py`.

## License

[AGPL-3.0](LICENSE)
