@echo off
echo Installing requirements...
pip install -r requirements.txt

echo Building client executable...
pyinstaller --onefile --noconsole --name "DrawingBoard" client.py

echo Building server executable...
pyinstaller --onefile --name "DrawingBoardServer" server.py

echo Moving executables to dist folder...
mkdir dist\DrawingBoard
move dist\DrawingBoard.exe dist\DrawingBoard\
move dist\DrawingBoardServer.exe dist\DrawingBoard\

echo Creating launcher...
echo @echo off > dist\DrawingBoard\Launch_Client.bat
echo start DrawingBoard.exe >> dist\DrawingBoard\Launch_Client.bat

echo Creating server launcher...
echo @echo off > dist\DrawingBoard\Start_Server.bat
echo echo Starting Drawing Board Server... >> dist\DrawingBoard\Start_Server.bat
echo echo To connect clients, make note of this computer's IP address >> dist\DrawingBoard\Start_Server.bat
echo ipconfig | findstr /i "ipv4" >> dist\DrawingBoard\Start_Server.bat
echo echo. >> dist\DrawingBoard\Start_Server.bat
echo DrawingBoardServer.exe >> dist\DrawingBoard\Start_Server.bat

echo Done! Check the dist\DrawingBoard folder for the executables.
pause 