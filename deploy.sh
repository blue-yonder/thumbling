#!/bin/bash

RESOURCE_GROUP=""
SERVICE_PLAN=""
UNIQUE_APP_SERVICE_NAME=""
BOT_NAME=""
APP_ID=""
APP_PASSWORD=""
BOTFILE_SECRET=""
DEPLOYMENT_USER=""
DEPLOYMENT_PASSWORD=""


az group create --name ${RESOURCE_GROUP} --location "West Europe"

az appservice plan create --name ${SERVICE_PLAN} \
--resource-group ${RESOURCE_GROUP} --sku B1 --is-linux

az webapp create --resource-group ${RESOURCE_GROUP} \
--plan ${SERVICE_PLAN} --name ${UNIQUE_APP_SERVICE_NAME} \
--runtime "PYTHON|3.7" --deployment-local-git \
--startup-file "gunicorn --bind=0.0.0.0  --timeout 600 --chdir src thumbling.bot_server:app --worker-class aiohttp.worker.GunicornWebWorker --access-logfile gun.log --error-logfile gun.log"

az webapp config appsettings set --resource-group ${RESOURCE_GROUP} \
--name ${UNIQUE_APP_SERVICE_NAME} --settings "botFilePath=../thumbling.bot"

az webapp config appsettings set --resource-group ${RESOURCE_GROUP} \
--name ${UNIQUE_APP_SERVICE_NAME} --settings "botFileSecret=${BOTFILE_SECRET}"

az webapp config appsettings set --resource-group ${RESOURCE_GROUP} \
--name ${UNIQUE_APP_SERVICE_NAME} --settings "APP_ENVIRONMENT=production"

az bot create --resource-group ${RESOURCE_GROUP} --name ${BOT_NAME} \
--kind registration --version v4 --appid ${APP_ID} --password ${APP_PASSWORD} \
-l "West Europe" -e https://${UNIQUE_APP_SERVICE_NAME}.azurewebsites.net/api/messages

az webapp deployment user set --user-name ${DEPLOYMENT_USER} --password ${DEPLOYMENT_PASSWORD}

git remote add azure https://${DEPLOYMENT_USER}@${UNIQUE_APP_SERVICE_NAME}.scm.azurewebsites.net/${UNIQUE_APP_SERVICE_NAME}.git
git push azure master

# if you want to use a fake prometheus server you can deploy this way:
# PROM_FAKE_APP="thumbling-prom-fake"

# az webapp create --resource-group ${RESOURCE_GROUP} \
# --plan ${SERVICE_PLAN} --name ${PROM_FAKE_APP} \
# --runtime "PYTHON|3.7" --deployment-local-git \
# --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 --chdir tests prometheus_fake:app --worker-class aiohttp.worker.GunicornWebWorker --access-logfile gun.log --error-logfile gun.log"

# git remote add azure-prom-fake https://${DEPLOYMENT_USER}@${PROM_FAKE_APP}.scm.azurewebsites.net/${PROM_FAKE_APP}.git
# git push azure zure-prom-fake
