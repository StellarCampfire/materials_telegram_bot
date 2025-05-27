#!/bin/bash

if [ ! -f /app/bot.log ]; then
    touch /app/bot.log
    chmod 644 /app/bot.log
fi

if [ ! -f /app/materials.db ]; then
    touch /app/materials.db
    chmod 644 /app/materials.db
fi

exec python main.py