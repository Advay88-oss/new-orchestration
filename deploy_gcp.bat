@echo off
setlocal enabledelayedexpansion

echo ================================================================================
echo 🚀 DEPLOYING VANNA GTM MISSION CONTROL TO GOOGLE CLOUD RUN
echo ================================================================================

set PROJECT_ID=sales-agent-504607
set REGION=us-central1
set SERVICE_NAME=vanna-gtm-mission
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%:latest

echo.
echo [1/3] Setting GCP project to %PROJECT_ID%...
call gcloud config set project %PROJECT_ID%

echo.
echo [2/3] Building container image via Google Cloud Build...
call gcloud builds submit --project %PROJECT_ID% --tag %IMAGE_NAME% .

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Cloud Build failed. Please check build logs.
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Deploying to Google Cloud Run (%REGION%)...
call gcloud run deploy %SERVICE_NAME% ^
    --project %PROJECT_ID% ^
    --image %IMAGE_NAME% ^
    --platform managed ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --memory 2Gi ^
    --cpu 2 ^
    --port 8080 ^
    --set-env-vars="NODE_ENV=production,PORT=8080,VERTEX_PROJECT=%PROJECT_ID%,VERTEX_LOCATION=%REGION%"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Cloud Run deployment failed.
    exit /b %ERRORLEVEL%
)

echo.
echo ================================================================================
echo ✅ DEPLOYMENT COMPLETE!
echo    Your Vanna GTM Mission Control is live on Google Cloud Run.
echo ================================================================================
