@echo off
echo Установка зависимостей...
pip install -r requirements.txt

echo Сборка EXE...
pyinstaller --onefile --windowed --name "Prygkin" main.py

echo.
echo Готово! Файл находится в папке dist\Prygkin.exe
pause
