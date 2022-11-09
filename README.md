# Thumbling

[Thumbling on Wikipedia](https://en.wikipedia.org/wiki/Thumbling)

The current purpose of this repository and the thumbling app is to explore the Azure Bot Service for Python and to provide help and examples to others.
As the SDK for Python and Python Azure Web Apps on Linux are still in a Preview state the usage can be a bit bumpy and I hope to this documentation can help with this.
It is especially the case for deployment and running the bot app. I will use the thumbling app in this documentation as an example app to run you through all steps necessary to run a bot in Azure.

**Disclaimer**: Running a Azure Bot Service in Azure creates costs depending on the selected resource class.
Executing Azure deployment commands can delete or render existing resources useless, so be careful when deploying to an already used subscription and control your costs.

## What does Thumbling?

Thumbling just tries to detect if someone is talking about a problem with a service. It then tries to get a list of alerts from a Prometheus monitoring server for this service at the defined time and sends it back to the user.

## Microsoft Language Understanding (LUIS)

Links: [LUIS documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/luis/) and [West Europe LUIS](https://eu.luis.ai)

To detect user's intents Thumbling uses a very simple and stupid model to. Basically we want only to detect if someone has a problem, for which instance or service and in which time range were the problems. 
To use the thumbling app you have to create one simple LUIS app as well. For this login and:
1. create a new app
2. create a new intent named "problem"
3. add examples sentences to the intent. e.g.
    * have there been any problems on euler-p1 today?
    * was there a problem with euler-s2 on sunday?
    * a customer has a problem with euler-p2 since 9:00.
    * any incidents with gauss-p2 during the weekend?
    * I have problems sending data to gauss-s1.
    * are there any known problems with gauss?
    * is euler working today?
3. mark "euler" and "gauss" in each utterance as new entity "service-name"
4. mark the "p1", "s1", "s2" and "p2" occurrence as a new entity "instance-identifier"
5. wrap the "euler" and "gauss" occurrence with their instance identifiers as as new entity "instance"
6. in the entities overview add "datetimeV2" from the prebuild entities
7. start a training
8. publish the app to production
9. get the endpoint and access key from the "Keys and Endpoints" page in the manage section

You can now use the endpoint to get message intents and entities for sent query sentences or you can use the test functionality on the web page.

## Running the Bot Locally

Even for running the bot locally the LUIS app is required and has to be setup in the thumbling.bot file.

Install the requirements:

    pip install -r requirements.in

or for not pinned requirements:

    pip install -e .

To run the fake Prometheus server:

    python prometheus_fake.py

To start the thumbling bot app:

    python src/thumbling/bot_server.py

Load the thumbling.bot file in the [Microsoft BotFramework-Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases) and ask the bot:

    Was there a problem with euler today?

and it should answer with multiple alerts.


## Deployment

### Requirements

#### Azure CLI

You need a subscription to run services in Azure. You can get a timely limited free subscription with some start credits from https://azure.microsoft.com.

I recommend to create and deploy the required resources with help of the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/?view=azure-cli-latest). Creating a Web App Bot in the Azure Portal creates additional resources you might not need for development and it will also not use the App Service for Linux which comes with the python 3.7 support. How you can do this will be part of this chapter. More infos about running a Python Web App can also be found in the [Azure documentation](https://docs.microsoft.com/en-us/azure/app-service/containers/quickstart-python).

#### Application Registration

The Azure Bot App needs to have an application ID and password so it can work in Azure. For a local setup this is not required. It can be registered at the [Microsoft Application Registration Portal](https://apps.dev.microsoft.com).

Add a new app and a new password for this app. The app ID and password will be required in the thumbling.bot file and for the deployment.

### .bot file

Microsoft uses .bot files to store required configuration values like app ID, password and consumed services.
This is not required and you can use whatever you like but the [Microsoft BotFramework-Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases) can directly use a .bot file to run the app locally.

To run the thumbling app you have to provide the required service infos to the app via the thumbling.bot file.
You can either edit thumbling.bot or use a own file and change the deployment commands.
What you have to do:
* use a correct appID and appPassword for the production endpoint
* add the LUIS information to the production luis service (for more information see the LUIS section in the documentation)
* set the Prometheus URL where the metrics should be scraped
* encrypt the .bot file; you can use msbot tool for this from the [botbuilder-tools](https://github.com/Microsoft/botbuilder-tools/tree/master/packages/MSBot)
* add the .bot file secret to the deployment commands

### Resource Deployment

The minimalist setup consist of three Azure resources and all three can be created with the Azure CLI:
* App Service plan
* App Service
* Bot Channels Registration

The deployment commands are also in the deploy.sh bash script.

**Deployment User**:

For development you can deploy from a local git repository to an Azure Web App. For this you need a deployment user. To create one use the following Azure CLI command:

    az webapp deployment user set --user-name ${DEPLOYMENT_USER} --password ${DEPLOYMENT_PASSWORD}

**Resource Group**:

First we need to create a resource group where the above listed services will be deployed into:

    az group create --name ${RESOURCE_GROUP} --location "West Europe"

**App Service Plan**:

The App Service plan defines the environment where the app is running in: the compute resources, platform, additional resources, scaling, ...

We will use the cheapest pricing tier *B1* on Linux for development:

    az appservice plan create --name ${SERVICE_PLAN} --resource-group ${RESOURCE_GROUP} --sku B1 --is-linux

**App Service**:

The App Service defines the runtime environment, here `python|3.7`. We also define the deployment type of the app, the settings e.g. how the app is started, environment variables and secrets. The app service name must be unique as it defines the URL how the app will be reachable: `https://${UNIQUE_APP_SERVICE_NAME}.azurewebsites.net`. For development purposes we use the local git deployment option.
We also define the gunicorn command which will be executed inside the container so that the git deployed thumbling app is found.

    az webapp create --resource-group ${RESOURCE_GROUP} --plan ${SERVICE_PLAN} --name ${UNIQUE_APP_SERVICE_NAME} --runtime "PYTHON|3.7" --deployment-local-git --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 --chdir src thumbling.bot_server:app --worker-class aiohttp.worker.GunicornWebWorker --access-logfile gun.log --error-logfile gun.log"


**Inside the output** of this deployment will be a "deploymentLocalGitUrl" key and URL as its value. You need this URL later for the git deployment.

To set application settings you can use the Azure CLI as well. To set the bot file path and the secret key to encrypt it do the following:

    # we have to go one directory up as we set the working dir in the gunicorn cmd to src
    az webapp config appsettings set --resource-group ${RESOURCE_GROUP} --name ${UNIQUE_APP_SERVICE_NAME} --settings "botFilePath=../thumbling.bot"
    
    az webapp config appsettings set --resource-group ${RESOURCE_GROUP} --name ${UNIQUE_APP_SERVICE_NAME} --settings "botFileSecret=${BOTFILE_SECRET}"

    az webapp config appsettings set --resource-group ${RESOURCE_GROUP} --name ${UNIQUE_APP_SERVICE_NAME} --settings "APP_ENVIRONMENT=production"

These settings will be environment variables in the environnement where the app is executed.

**Bot Channels Registration**:

That the Azure Web App actually can be used as a bot and from chat apps you need a Bot Channels Registration. This one defines which chat tools can talk to the bot and where the bot app is running. For this you also need the registered app ID and password from the section above:

    az bot create --resource-group ${RESOURCE_GROUP} --name ${BOT_NAME} --kind registration --version v4 --appid ${APP_ID} --password ${APP_PASSWORD} -l "West Europe" -e https://${UNIQUE_APP_SERVICE_NAME}.azurewebsites.net/api/messages

### App Deployment

**git deployment**:

Set the remote git URL where you want to deploy to:

    git remote add azure https://${DEPLOYMENT_USER}@${UNIQUE_APP_SERVICE_NAME}.scm.azurewebsites.net/${UNIQUE_APP_SERVICE_NAME}.git

Push current master to Azure:

    git push azure master

This can take some time as well as the container restart afterwards.
It will ask for the deployment user password you have set during its creation.

If there are problems during the git push, in the Azure portal in your Web App is a *Deployment options* section where you can get more information or you can just do a redeploy.

### Fake Prometheus

As it is not very easy to dump fake data to a [Prometheus](https://prometheus.io/) server, a fake server is added to the repository. This fake can be used for local experiments as well in Azure. But of course you can also use a real Prometheus instance.
See deploy.sh how it can be deployed. The URL of the deployed app has to be added to the thumbling.bot file.

### Use the bot

The bot should now be functional. Go to the created Bot Channels Registration in the Azure Portal. There is a "Test in Web Chat" where you can test drive the bot.

For connecting channels please see the [Azure Bot Service documentation](https://docs.microsoft.com/en-us/azure/bot-service/bot-service-manage-channels?view=azure-bot-service-4.0).
