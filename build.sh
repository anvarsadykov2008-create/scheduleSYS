#!/usr/bin/env bash
# Скрипт сборки для Render (комбинированный хостинг)

# 1. Сборка фронтенда
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# 2. Установка зависимостей бэкенда
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt
