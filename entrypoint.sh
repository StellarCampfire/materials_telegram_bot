#!/bin/bash

if [ -d /app/bot.log ]; then
    rm -rf /app/bot.log
    touch /app/bot.log
    chmod 644 /app/bot.log
elif [ ! -f /app/bot.log ]; then
    touch /app/bot.log
    chmod 644 /app/bot.log
fi

if [ -d /app/materials.db ]; then
    rm -rf /app/materials.db
    touch /app/materials.db
    chmod 644 /app/materials.db
elif [ ! -f /app/materials.db ]; then
    touch /app/materials.db
    chmod 644 /app/materials.db
fi

exec python main.py