@echo off
(
echo C:\Users\aboja\Documents\SpiderFighting\Scripts\Animancer.Examples
echo C:\Users\aboja\Documents\SpiderFighting\Assets\Plugins\Animancer
echo C:\Users\aboja\Documents\SpiderFighting\Assets
) | "C:\Users\aboja\Documents\SpiderFightingFinalVersionIncha2Allah\UnityGUIDFixerTools\GUIDcorrector\ReplaceGUIDwithCorrectOne\x64\Release\ReplaceGUIDwithCorrectOne.exe"
if %errorlevel% neq 0 (
    echo.
    echo Tool exited with error code %errorlevel%
    pause
)
