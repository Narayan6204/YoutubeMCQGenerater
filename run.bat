@echo off
title YouTube Playlist MCQ Generator
echo ===================================================
echo Starting YouTube Playlist MCQ Generator UI...
echo ===================================================
.\.venv\Scripts\streamlit run app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start Streamlit app.
    pause
)
