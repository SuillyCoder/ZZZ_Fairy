Copy-Item -Recurse vosk_model dist\Fairy\vosk_model -Force
Copy-Item -Recurse voice_samples dist\Fairy\voice_samples -Force
Copy-Item -Recurse gui\elements dist\Fairy\gui\elements -Force
Copy-Item -Recurse media dist\Fairy\media -Force
Copy-Item -Recurse computer_vision\sleep_alarm dist\Fairy\computer_vision\sleep_alarm -Force
Copy-Item -Recurse computer_vision\intruder_alert dist\Fairy\computer_vision\intruder_alert -Force
Copy-Item -Recurse computer_vision\intruder_alert dist\Fairy\transcripts -Force
Copy-Item .env dist\Fairy\.env -Force
Copy-Item credentials.json dist\Fairy\credentials.json -Force
Copy-Item token.json dist\Fairy\token.json -Force -ErrorAction SilentlyContinue
Copy-Item token_sheets.json dist\Fairy\token_sheets.json -Force -ErrorAction SilentlyContinue
Copy-Item token_spotify.json dist\Fairy\token_spotify.json -Force -ErrorAction SilentlyContinue
Write-Host "Post-build copy complete." -ForegroundColor Green
