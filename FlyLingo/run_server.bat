@echo off
title FlyLingo - JAL In-Flight Gateway
echo ========================================================
echo   JAPAN AIRLINES (JAL) - 100%% OFFLINE AIR-GAPPED GATEWAY
echo   Flight JL740 (DEL to HND) - Boeing 787-9 Dreamliner
echo ========================================================
echo.
echo Distinct Offline Endpoints:
echo   1. Passenger Language Selection: http://127.0.0.1:8000/language
echo   2. Passenger Seat Portal:        http://127.0.0.1:8000/passenger
echo   3. Cabin Crew Station (Tablet):  http://127.0.0.1:8000/crew
echo   4. Boarding Pass & QR Screen:    http://127.0.0.1:8000/ticket
echo   5. Operations Surveillance Deck: http://127.0.0.1:8000/surveillance
echo.
echo Starting local aircraft edge server on port 8000...
echo Opening Passenger and Crew interfaces in your browser...
start "" http://127.0.0.1:8000/language
start "" http://127.0.0.1:8000/crew
python -m uvicorn server:app --host 0.0.0.0 --port 8000
pause
