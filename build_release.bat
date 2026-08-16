@echo off
echo Building SpriteStitcher executable with PyInstaller...

REM Include the assets folder in the bundle (Windows syntax: source;dest)
pyinstaller --onefile --windowed --name "SpriteStitcher" --add-data "assets;assets" stitch_sprites.py

echo Creating release ZIP...
if exist SpriteStitcher-Release.zip del SpriteStitcher-Release.zip
powershell -Command "Compress-Archive -Path dist\SpriteStitcher.exe -DestinationPath SpriteStitcher-Release.zip"

echo Done. SpriteStitcher-Release.zip created in project root.
pause