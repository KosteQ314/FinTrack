@echo off
echo Building CLI...
call build_cli.bat
echo.
echo Building App...
call build_app.bat
echo.
echo Zipping builds...

cd dist
powershell Compress-Archive -Path "FinTrack" -DestinationPath "FinTrack.zip" -Force
powershell Compress-Archive -Path "FinTrack-CLI" -DestinationPath "FinTrack-CLI.zip" -Force
cd ..

echo.
echo Done. Check the dist folder for zips.
pause
