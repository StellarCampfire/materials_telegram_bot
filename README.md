# 1C Materials Telegram Bot

A Telegram bot for distributing 1C educational materials, allowing users to browse materials, access demo versions, and purchase full versions with payment integration.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Docker Deployment](#docker-deployment)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

## Overview
This Telegram bot is designed to provide users with access to 1C educational materials. Users can:
- View a list of available materials.
- Access demo versions of materials.
- Purchase full versions via integrated payment processing.
- The bot uses SQLite for data storage and supports Docker deployment for scalability.

## Features
- **Material Browsing**: Displays a list of materials with titles, descriptions, and images.
- **Demo Access**: Provides links to demo versions of materials.
- **Payment Integration**: Supports payments for full material access using a payment provider (e.g., YooKassa).
- **Logging**: Logs bot activity and errors to a file (`bot.log`) with rotation for efficient storage.
- **Database Management**: Stores material details in an SQLite database (`materials.db`).
- **Docker Support**: Includes a `Dockerfile` and `docker-compose.yml` for containerized deployment.

## Prerequisites
- Python 3.11
- Docker (optional, for containerized deployment)
- A Telegram bot token (obtained from [BotFather](https://t.me/BotFather))
- A payment provider token (e.g., YooKassa)
- SQLite (included with Python)

## Installation
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
1. **Create a `.env` File**:
   In the project root, create a `.env` file with the following content:
   ```
   TOKEN=your_telegram_bot_token
   PAYMENT_PROVIDER_TOKEN=your_payment_provider_token
   ```
   Replace `your_telegram_bot_token` with the token from BotFather and `your_payment_provider_token` with your payment provider's token (e.g., YooKassa).

2. **Database Setup**:
   The bot automatically creates an SQLite database (`materials.db`) on first run. Populate the database with material data (e.g., using a script or manual SQL queries). The schema is defined in `database.py`.

## Usage
1. **Run the Bot Locally**:
   ```bash
   python main.py
   ```
   The bot will start and connect to Telegram, logging activity to `bot.log`.

2. **Interact with the Bot**:
   - Start the bot with the `/start` command.
   - Browse materials from the inline keyboard.
   - Click a material to view its description and image.
   - Download a demo version or purchase the full material.
   - After a successful payment, receive a link to the full material.

## Project Structure
```
├── .dockerignore         # Ignored files for Docker builds
├── .gitignore           # Ignored files for Git
├── .env                 # Environment variables (not tracked)
├── bot.log              # Log file (not tracked)
├── materials.db         # SQLite database (not tracked)
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── main.py              # Main bot logic
├── material.py          # Material class definition
├── database.py          # Database handling logic
└── README.md            # This file
```

## Docker Deployment
1. **Build and Run with Docker Compose**:
   ```bash
   docker-compose up -d --build
   ```
   This builds the Docker image and starts the bot in detached mode.

2. **Environment Variables**:
   Ensure the `.env` file is present in the project root, as it is mounted into the container.

3. **Volumes**:
   - `materials.db`: Persists the SQLite database.
   - `bot.log`: Persists the log file.

4. **Stop the Container**:
   ```bash
   docker-compose down
   ```

## Logging
- Logs are written to `bot.log` with a maximum size of 5MB and up to 5 backup files.
- Logs include bot startup, user interactions, payment events, and errors.
- Console output is also enabled with UTF-8 encoding.

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.