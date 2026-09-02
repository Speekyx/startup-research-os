# Problem-family human reference batch V1 — blind review

**Mission 1.26. Generated, never hand-picked. No model was called and no model
output was read.** Regenerate with
`python infrastructure/scripts/render_human_reference_batch.py`.

- dataset: `problem-family-human-reference-v1`
- relation: **`SAME_PROBLEM_FAMILY`** — rubric `problem-family-rubric@1.0.0`, unchanged
- sampling: `problem-family-human-reference-sampling@1.0.0`  ·  split: `problem-family-human-reference-split@1.0.0`
- eligibility: `docker-problem-family-candidates@1.0.0`, frozen from Mission 1.25
- corpus: 89 Docker `community_question` observations, unchanged
  since Mission 1.20. 731 pairs eligible; 20 already labelled in Mission 1.25 and excluded; 711 available
- **40 pairs — 24 development, 16 holdout**, split frozen before any label exists

> **Nothing here carries a prediction, a suggested label, or an expected answer.**
> Mission 1.25's classifier output played no part in choosing these pairs, and no
> model has seen them. Your judgement is the reference.

## Why this batch exists

Mission 1.25 evaluated a problem-family classifier against 10 human-labelled
holdout pairs containing 2 positives. That was enough to reject a classifier that
answers DIFFERENT to everything — and it did reject one — but it is not enough to
*develop* or credibly evaluate a successor. Ten pairs with two positives can say
*this does not work*; they cannot say *this works*.

This batch is the reference set that would make the next answer worth having.

## The question, for every pair

> **Are these two observations substantially the same user problem, pain or
> blocked goal, such that one product, tool, documentation intervention or
> workflow could reasonably help both?**

Two published observations belong to the SAME PROBLEM FAMILY when they describe
substantially the same user problem, pain or blocked goal -- at a level where one
product, tool, documentation change or workflow could reasonably help both people
-- even if the technical root causes differ and even if the fixes differ.

Ask: WHAT WAS EACH PERSON TRYING TO DO, AND WHAT STOPPED THEM? If the answers are
substantially the same thing, it is one family. If one intervention would have to
be two unrelated interventions to help both, it is not.

This is a question about the published descriptions, not about the underlying
truth, and not about the code. Where the text does not establish what the person
was trying to do, the answer is ABSTAIN.

Answer each with `SAME_FAMILY`, `DIFFERENT_FAMILY` or `UNCERTAIN`.

**`UNCERTAIN` is a real answer and is never coerced into a binary one.** If the
published text does not establish what one or both people were trying to do, that
is the correct answer and it is useful.

**You are not asked to diagnose anything.** No Docker knowledge is required: the
question is about what each person was trying to do and what stopped them, not
about what would fix it.

## None of this makes two observations one family

- the same tool, runtime or platform. Every observation here is a Docker question, so a relation satisfied by that would return SAME for everything
- the same site tags, however specific
- the same language, framework or base image
- the same wrapper or harness diagnostic, however long the shared string. Mission 1.20's three questions share 106 characters of exact runc output and are three unrelated blocked goals
- the same generic error class -- permission denied, connection refused, exit code 1, HTTP 500, a bare ValueError, 'the build failed'
- the same broad category of component. Two database connectivity failures are not one family merely because both involve databases; MongoDB unreachable from a container and SQL Server refusing an integrated-security login are different blocked goals with different interventions
- the same lifecycle phase alone. 'Both happen at build time' is a coordinate, not a goal

## How these 40 were chosen

Deterministically, from the frozen eligibility rule, in five feature bands. **The
bands are sampling mechanisms and carry no expected answer** — they describe what
two questions share lexically, which is exactly what a reviewer is needed to look
past.

| band | what the pair shares | available | drawn |
|---|---|---|---|
| A high specificity | a site tag carried by ~6 or fewer of 89 | 53 | 10 |
| B medium specificity | a tag of middling frequency | 136 | 8 |
| C low specificity | a common tag; eligible and weak | 275 | 8 |
| D diagnostic wrapper | a shared error fragment | 2 | 2 |
| E different tags | no shared tag; overlapping title words only | 245 | 12 |

> **This 40-pair set is an EVALUATION-ORIENTED ENRICHED SAMPLE. Strata were sampled at deliberately unequal rates -- the low-similarity stratum holds 275 of the 711 available pairs and contributes 8, the wrapper stratum holds 2 and contributes both -- so the proportion of any label in it is NOT an estimate of how often that label occurs among Docker Stack Exchange pairs. It may be used to develop and evaluate a classifier. It may never be used to state a prevalence.**

## The split is already frozen

Each pair is marked `development` or `holdout`, assigned within its band before
any label existed. Development may later be used to design a successor
classifier; **holdout must stay untouched by that work**. Please label both: the
split governs how the labels may be *used*, never how they should be *made*.

## What is shown, and why there is no summary

Each observation appears as **verbatim source excerpts** — the title, the site's
own tags, the opening sentences, and any error output — selected by fixed rules.
There is no plain-language summary. Writing one would mean an assistant phrasing
the question for you, and a phrasing carries a reading; this review exists to
obtain a reading that is yours. The canonical URL is given for each observation,
both as CC BY-SA attribution and so you can open the original where the excerpt
is not enough.

---

## PAIR 1/40 — `78086387::78096175`

split: **development**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 51

### Observation A · question 78086387

**Troubles with postgres while building docker container**

tags: `django`, `linux`, `postgresql`, `docker`, `devops`  
source: <https://stackoverflow.com/questions/78086387/troubles-with-postgres-while-building-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to lauch DJANGO + POSTGRES inside a single container with DOCKERFILE. I have the folowing dockerfile which basicly installs all the python dependencies and postgresql. Then it lauches the script to create db and user (presented below). FROM python WORKDIR /app COPY requirements.txt . RUN pip install -r requirements.txt COPY . .

Error output quoted in the question:

    error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/djang
    error checking a consistent migration history performed for database connection 'default': connection to server at "localhost" (127.0.0.1), port 5432 failed: connection refused 3.377 is the server running on that host an

### Observation B · question 78096175

**My postgresql database doesn't persist between docker runs**

tags: `django`, `postgresql`, `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78096175/my-postgresql-database-doesnt-persist-between-docker-runs>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am learning docker and postgresql and I have problem with persisting data between the re-runs of the app. My docker-compose.yml: version: '3.7' services: web: build: .

*Lexically these two share: tags django, postgresql; title words docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 2/40 — `78086387::78101562`

split: **development**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 105

### Observation A · question 78086387

**Troubles with postgres while building docker container**

tags: `django`, `linux`, `postgresql`, `docker`, `devops`  
source: <https://stackoverflow.com/questions/78086387/troubles-with-postgres-while-building-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to lauch DJANGO + POSTGRES inside a single container with DOCKERFILE. I have the folowing dockerfile which basicly installs all the python dependencies and postgresql. Then it lauches the script to create db and user (presented below). FROM python WORKDIR /app COPY requirements.txt . RUN pip install -r requirements.txt COPY . .

Error output quoted in the question:

    error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/djang
    error checking a consistent migration history performed for database connection 'default': connection to server at "localhost" (127.0.0.1), port 5432 failed: connection refused 3.377 is the server running on that host an

### Observation B · question 78101562

**Reduce the size of Docker and Laravel 7.4?**

tags: `php`, `linux`, `docker`, `apache`  
source: <https://stackoverflow.com/questions/78101562/reduce-the-size-of-docker-and-laravel-7-4>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have a problem. My project is with the Laravel framework, and when I upload it to Docker, the size of the Docker image becomes 6 GB, which is too much. How can I reduce the size of the image?

*Lexically these two share: tags linux; title words docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 3/40 — `78088329::78089171`

split: **development**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 36

### Observation A · question 78088329

**What is the purpose of mounting volumes that contain already mounted volumes?**

tags: `docker`, `kubernetes`, `docker-compose`, `kubernetes-statefulset`  
source: <https://stackoverflow.com/questions/78088329/what-is-the-purpose-of-mounting-volumes-that-contain-already-mounted-volumes>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am looking at a docker-compose file for the Eramba project, the volumes part looks like this: volumes: - data:/var/www/eramba/app/upgrade/data - app:/var/www/eramba - logs:/var/www/eramba/app/upgrade/logs Why do they mount data and logs when app (which is the parent dir) is also mounted? To me it seems to be duplicates in some way when doing this?

### Observation B · question 78089171

**In the nextjs project environment variable in k8s is undefined**

tags: `kubernetes`, `next.js`, `dockerfile`, `environment-variables`  
source: <https://stackoverflow.com/questions/78089171/in-the-nextjs-project-environment-variable-in-k8s-is-undefined>  
licence: CC BY-SA 4.0, Stack Exchange Network

> The project has api endpoints that have values ​​if they are in a dev environment or docker containers (work normally / have value). However, in a prod/qa environment in k8s it has no value, even though the env is in the POD. prod/qa: local dev/docker: The two ways I'm trying to call.

Error output quoted in the question:

    not found") } ... } async function fetchdata() { const apitest = process.env['next_public_bff_orm_status'] if (!apitest) { console.log("api teste sem valor") } ... } dockerfile: from node:lts as dependencies workdir /fro

*Lexically these two share: tags kubernetes. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 4/40 — `78088481::78103907`

split: **holdout**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 39

### Observation A · question 78088481

**Docker Compose MongoDB connection**

tags: `node.js`, `mongodb`, `docker`, `nginx`, `docker-compose`  
source: <https://stackoverflow.com/questions/78088481/docker-compose-mongodb-connection>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have a NodeJS server that needs to connect to MongoDB, everything is built with docker compose, including NGINX.

Error output quoted in the question:

    error that i get is: mongooseserverselectionerror: connect econnrefused 172.28.0.2:27017

### Observation B · question 78103907

**How can I create a Dockerfile that runs both my nodeJS server and also launches mongodb? All in the same container**

tags: `node.js`, `mongodb`, `docker`, `dockerfile`  
source: <https://stackoverflow.com/questions/78103907/how-can-i-create-a-dockerfile-that-runs-both-my-nodejs-server-and-also-launches>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I need to be able to run within the same container both: my nodejs server.js and mongodb. I know it is possible to achieve this with docker-compose or with two separate containers but that is not an option here. I need both services running on the same container.

*Lexically these two share: tags mongodb, node.js; title words mongodb. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 5/40 — `78089075::78103907`

split: **development**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 111

### Observation A · question 78089075

**Can not connect with click-house running inside docker with nodejs**

tags: `node.js`, `docker`, `clickhouse`  
source: <https://stackoverflow.com/questions/78089075/can-not-connect-with-click-house-running-inside-docker-with-nodejs>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have downloaded this click-house docker image https://hub.docker.com/r/clickhouse/clickhouse-server/ I started click-house server with the following command docker run --network=host --name some-clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-server I connected with clickhouse with the following command docker exec -it some-clickhouse-server clickhouse-client Output of the above command ClickH

Error output quoted in the question:

    error. same is true for port 9000 as well. i am using host network in docker, so i should be able to connect this interface from my browser. same is happening for nodejs as well const { clickhouse } = require("clickhouse
    error on terminal error inserting row: error: connect econnrefused ::1:9000 at tcpconnectwrap.afterconnect [as oncomplete] (node:net:1532:16) { errno: -61, code: 'econnrefused', syscall: 'connect', address: '::1', port: 

### Observation B · question 78103907

**How can I create a Dockerfile that runs both my nodeJS server and also launches mongodb? All in the same container**

tags: `node.js`, `mongodb`, `docker`, `dockerfile`  
source: <https://stackoverflow.com/questions/78103907/how-can-i-create-a-dockerfile-that-runs-both-my-nodejs-server-and-also-launches>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I need to be able to run within the same container both: my nodejs server.js and mongodb. I know it is possible to achieve this with docker-compose or with two separate containers but that is not an option here. I need both services running on the same container.

*Lexically these two share: tags node.js; title words nodejs. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 6/40 — `78090939::78105296`

split: **holdout**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 43

### Observation A · question 78090939

**Springboot application, deploy in Render fail**

tags: `java`, `spring-boot`, `docker`, `deployment`  
source: <https://stackoverflow.com/questions/78090939/springboot-application-deploy-in-render-fail>  
licence: CC BY-SA 4.0, Stack Exchange Network

> i'm experiencing an issue with my java app, i'm trying to deploy it on render, in a docker container. my Dockerfile looks like this: FROM amazoncorretto:17-alpine-jdk MAINTAINER SchJavier COPY /out/artifacts/agilstratApi_jar agilstratApi.jar ENTRYPOINT ["java", "-jar", "agilstratApi.jar" the deploy logs throw me this error: Error: Invalid or corrupt jarfile agilstratApi.jar I don't know how to solve it.

Error output quoted in the question:

    error: error: invalid or corrupt jarfile agilstratapi.jar i don't know how to solve it. something curious that may have something to do with it, when i upload the changes to the remote repository, it gives me this warnin
    cannot run the app. now i got a lot of new issues to share with you! well, thanks a lot!

### Observation B · question 78105296

**Deploying an Angular Application to OpenShift via GitLab**

tags: `angular`, `docker`, `deployment`, `gitlab`, `openshift`  
source: <https://stackoverflow.com/questions/78105296/deploying-an-angular-application-to-openshift-via-gitlab>  
licence: CC BY-SA 4.0, Stack Exchange Network

> My company utilizes OpenShift for application deployment. As per guidance from my senior, the recommended approach involves utilizing GitLab as an intermediate step. The process entails creating and pushing the container to a GitLab repository, and then using that repository (containing the container) to deploy the application on OpenShift.

*Lexically these two share: tags deployment; title words application. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 7/40 — `78096175::78099350`

split: **development**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 113

### Observation A · question 78096175

**My postgresql database doesn't persist between docker runs**

tags: `django`, `postgresql`, `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78096175/my-postgresql-database-doesnt-persist-between-docker-runs>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am learning docker and postgresql and I have problem with persisting data between the re-runs of the app. My docker-compose.yml: version: '3.7' services: web: build: .

### Observation B · question 78099350

**Docker-compose with Golang and Postgres connection is refused**

tags: `postgresql`, `docker`, `go`, `docker-compose`  
source: <https://stackoverflow.com/questions/78099350/docker-compose-with-golang-and-postgres-connection-is-refused>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to make the connection with PostgreSQL using Docker Compose. I have a Golang CLI application called flow and it creates, views, adjust's, gets, and removes the budget information. When I write the docker docker-compose up -d , it creates two images and one container.

Error output quoted in the question:

    refused message. here is the command: docker run -it flow-budget_planner ./flow budget create -c category -a 300 what should i do to make the connection established and enter the data in postgresql successfully using doc
    error) { v := variables{ host: middleware.loadenvvariable("host"), port: middleware.loadenvvariable("port"), user: middleware.loadenvvariable("user"), password: middleware.loadenvvariable("password"), dbname: middleware.

*Lexically these two share: tags docker-compose, postgresql. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 8/40 — `78096175::78100773`

split: **holdout**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 114

### Observation A · question 78096175

**My postgresql database doesn't persist between docker runs**

tags: `django`, `postgresql`, `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78096175/my-postgresql-database-doesnt-persist-between-docker-runs>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am learning docker and postgresql and I have problem with persisting data between the re-runs of the app. My docker-compose.yml: version: '3.7' services: web: build: .

### Observation B · question 78100773

**Could not create schema and table in PostgreSQL**

tags: `postgresql`, `docker`  
source: <https://stackoverflow.com/questions/78100773/could-not-create-schema-and-table-in-postgresql>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I faced with a weird behavior in the PostgreSQL database.

Error output quoted in the question:

    timeout: 5s retries: 5 volumes: - ./dependencies/in_postgres_startup_insert.sql:/docker-entrypoint-initdb.d/in_postgres_startup_insert.sql as you see in this docker file i use in_postgres_startup_insert.sql file. here is

*Lexically these two share: tags postgresql; title words postgresql. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 9/40 — `78098246::78098969`

split: **holdout**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 117

### Observation A · question 78098246

**my flask api doesnt get my port even if i specify it**

tags: `python`, `linux`, `bash`, `docker`, `sh`  
source: <https://stackoverflow.com/questions/78098246/my-flask-api-doesnt-get-my-port-even-if-i-specify-it>  
licence: CC BY-SA 4.0, Stack Exchange Network

> my userapi if __name__ == "__main__": if len(sys.argv) >= 2: try: app_port = int(sys.argv[1]) except ValueError as ve: app_port = 5558 app.run(debug=True, host='0.0.0.0', port=app_port) else: raise ValueError('No starting port for the application') my startdocker.sh file #!/bin/bash docker container stop userapi_cnt_ad docker container rm userapi_cnt_ad docker image rm userapi_img_ad docker volume rm ad_vol docker vo

### Observation B · question 78098969

**How to handle remotely updating a continuously running python script on a linux machine**

tags: `linux`, `docker`, `raspberry-pi`  
source: <https://stackoverflow.com/questions/78098969/how-to-handle-remotely-updating-a-continuously-running-python-script-on-a-linux>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have a python script running on a raspberry pi. This script is part of a git repo. I intend on the rpi and this script to be running all the time because the application is for responding fairly quickly to MQTT messages and controlling devices. Some small <5min downtime during updating is acceptable. I am developing the script on my desktop machine and want to deploy to the raspberry pi.

*Lexically these two share: tags linux. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 10/40 — `78102252::78103994`

split: **development**  ·  band: `A_HIGH_SPECIFICITY`  ·  candidate rank 61

### Observation A · question 78102252

**ModuleNotFoundError message when run gcp dataflow pipeline with python**

tags: `python`, `docker`, `google-cloud-platform`, `google-cloud-dataflow`, `apache-beam`  
source: <https://stackoverflow.com/questions/78102252/modulenotfounderror-message-when-run-gcp-dataflow-pipeline-with-python>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I'm trying to install dependencies in a dataflow pipeline. First I used requirements_file flag but i get (ModuleNotFoundError: No module named 'unidecode' [while running 'Map(wordcleanfn)-ptransform-54']) the unique package added is unidecode.

Error output quoted in the question:

    error is the same, please someone can help me? i understand that the workers are using de default beam sdk, is correct that? how i can fix it?

### Observation B · question 78103994

**Deploying to GCP: unable to prepare context: unable to evaluate symlinks in Dockerfile path: lstat /workspace/Dockerfile: no such file or directory**

tags: `python`, `docker`, `google-cloud-platform`  
source: <https://stackoverflow.com/questions/78103994/deploying-to-gcp-unable-to-prepare-context-unable-to-evaluate-symlinks-in-dock>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Receiving the error above when deploying a python app to a Docker image on GCP.

Error output quoted in the question:

    error above when deploying a python app to a docker image on gcp. my cloudbuild.yaml: steps: # install dependencies - name: python entrypoint: pip args: ["install", "-r", "requirements.txt", "--user"] # docker build - na
    unable to prepare context: unable to evaluate symlinks in dockerfile path: lstat /workspace/dockerfile: no such file or directory finished step #1 error error: build step 1 "gcr.io/cloud-builders/docker" failed: step exi

*Lexically these two share: tags google-cloud-platform, python; title words gcp. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 11/40 — `78086836::78098246`

split: **holdout**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 144

### Observation A · question 78086836

**AttributeError: module 'jwt.algorithms' has no attribute 'hashes'**

tags: `python`, `docker`, `pip`, `jwt`, `attributeerror`  
source: <https://stackoverflow.com/questions/78086836/attributeerror-module-jwt-algorithms-has-no-attribute-hashes>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I try to run the following script in a Python virtual environment by having pyjwt installed with pip3 install -U pyjwt as per suggested and it works import requests from requests_oauthlib import OAuth1 from oauthlib.oauth1 import SIGNATURE_RSA headerauth = OAuth1(client_key, rsa_key, signature_type="auth_header", signature_method=SIGNATURE_RSA) r = requests.get(url, auth=headerauth) However, it's throwing an error wh

Error output quoted in the question:

    error when i try to run the local docker image attributeerror: module 'jwt.algorithms' has no attribute 'hashes' the versions stated in pipfile are same as those in python virtual environment [packages] pyjwt = ">=2.8.0"

### Observation B · question 78098246

**my flask api doesnt get my port even if i specify it**

tags: `python`, `linux`, `bash`, `docker`, `sh`  
source: <https://stackoverflow.com/questions/78098246/my-flask-api-doesnt-get-my-port-even-if-i-specify-it>  
licence: CC BY-SA 4.0, Stack Exchange Network

> my userapi if __name__ == "__main__": if len(sys.argv) >= 2: try: app_port = int(sys.argv[1]) except ValueError as ve: app_port = 5558 app.run(debug=True, host='0.0.0.0', port=app_port) else: raise ValueError('No starting port for the application') my startdocker.sh file #!/bin/bash docker container stop userapi_cnt_ad docker container rm userapi_cnt_ad docker image rm userapi_img_ad docker volume rm ad_vol docker vo

*Lexically these two share: tags python. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 12/40 — `78089113::78089171`

split: **development**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 418

### Observation A · question 78089113

**Docker image from customized Grafana source code**

tags: `docker`, `docker-compose`, `dockerfile`, `grafana`  
source: <https://stackoverflow.com/questions/78089113/docker-image-from-customized-grafana-source-code>  
licence: CC BY-SA 4.0, Stack Exchange Network

> We have fork from the Grafana source and make changes mainly the UI. Now, I want to create docker image and faced issue.

Error output quoted in the question:

    error to build the image. but, when i comment out the the below code the dashboard is fine. run if [[ "$bingo" = "true" ]]; then \ go install github.com/bwplotka/bingo@latest && \ bingo get -v; \ fi my questions: what do
    error. now, if i remove certain peice of code, i was manage to build the image. my quesion is do i need that code?

### Observation B · question 78089171

**In the nextjs project environment variable in k8s is undefined**

tags: `kubernetes`, `next.js`, `dockerfile`, `environment-variables`  
source: <https://stackoverflow.com/questions/78089171/in-the-nextjs-project-environment-variable-in-k8s-is-undefined>  
licence: CC BY-SA 4.0, Stack Exchange Network

> The project has api endpoints that have values ​​if they are in a dev environment or docker containers (work normally / have value). However, in a prod/qa environment in k8s it has no value, even though the env is in the POD. prod/qa: local dev/docker: The two ways I'm trying to call.

Error output quoted in the question:

    not found") } ... } async function fetchdata() { const apitest = process.env['next_public_bff_orm_status'] if (!apitest) { console.log("api teste sem valor") } ... } dockerfile: from node:lts as dependencies workdir /fro

*Lexically these two share: tags dockerfile. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 13/40 — `78089171::78093369`

split: **holdout**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 432

### Observation A · question 78089171

**In the nextjs project environment variable in k8s is undefined**

tags: `kubernetes`, `next.js`, `dockerfile`, `environment-variables`  
source: <https://stackoverflow.com/questions/78089171/in-the-nextjs-project-environment-variable-in-k8s-is-undefined>  
licence: CC BY-SA 4.0, Stack Exchange Network

> The project has api endpoints that have values ​​if they are in a dev environment or docker containers (work normally / have value). However, in a prod/qa environment in k8s it has no value, even though the env is in the POD. prod/qa: local dev/docker: The two ways I'm trying to call.

Error output quoted in the question:

    not found") } ... } async function fetchdata() { const apitest = process.env['next_public_bff_orm_status'] if (!apitest) { console.log("api teste sem valor") } ... } dockerfile: from node:lts as dependencies workdir /fro

### Observation B · question 78093369

**installing psycopg in alpine docker image**

tags: `docker`, `dockerfile`, `psycopg2`, `docker-image`  
source: <https://stackoverflow.com/questions/78093369/installing-psycopg-in-alpine-docker-image>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have the following dockerfile: FROM python:3.12.0-alpine3.18 WORKDIR /usr/src/app ENV PYTHONDONTWRITEBYTECODE 1 ENV PYTHONUNBUFFERED 1 RUN apk update && \ apk add --virtual build-deps gcc python3-dev musl-dev && \ apk add postgresql-dev COPY requirements ./requirements RUN pip install -r ./requirements/local.txt COPY . .

Error output quoted in the question:

    error occurs when the image is loaded: error: failed to solve: process "/bin/sh -c pip install -r ./requirements/local.txt" did not complete successfully: exit code: 1 i tried to install various dependencies in my docker
    error. what dependencies do i need to add to my dockerfile for psycopg to install? and also where can you read what dependencies you need to add and your dockerfile for certain libraries based on a certain image?

*Lexically these two share: tags dockerfile. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 14/40 — `78091298::78098246`

split: **development**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 159

### Observation A · question 78091298

**Minimal example of docker oci_image with custom python toolchain in bazel**

tags: `python`, `docker`, `bazel`, `rules-oci`  
source: <https://stackoverflow.com/questions/78091298/minimal-example-of-docker-oci-image-with-custom-python-toolchain-in-bazel>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to produce a docker image using the rules_oci bazel repo. I am using a custom python toolchain I have registered in my WORKSPACE . The following code builds a docker image that contains the python toolchain and run_api_server.py and its relevant dependencies.

### Observation B · question 78098246

**my flask api doesnt get my port even if i specify it**

tags: `python`, `linux`, `bash`, `docker`, `sh`  
source: <https://stackoverflow.com/questions/78098246/my-flask-api-doesnt-get-my-port-even-if-i-specify-it>  
licence: CC BY-SA 4.0, Stack Exchange Network

> my userapi if __name__ == "__main__": if len(sys.argv) >= 2: try: app_port = int(sys.argv[1]) except ValueError as ve: app_port = 5558 app.run(debug=True, host='0.0.0.0', port=app_port) else: raise ValueError('No starting port for the application') my startdocker.sh file #!/bin/bash docker container stop userapi_cnt_ad docker container rm userapi_cnt_ad docker image rm userapi_img_ad docker volume rm ad_vol docker vo

*Lexically these two share: tags python. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 15/40 — `78091354::78095654`

split: **development**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 23

### Observation A · question 78091354

**Nest.js CLI not found in Docker multi-stage build**

tags: `docker`, `dockerfile`, `nest`  
source: <https://stackoverflow.com/questions/78091354/nest-js-cli-not-found-in-docker-multi-stage-build>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I'm trying to set up a multi-stage Docker build for my Node.js and Nest.js application. The Dockerfile includes installing dependencies, building the application, and running it. However, I'm encountering an issue with the npm run build command in the production stage of the Dockerfile.

Error output quoted in the question:

    error message i'm getting is: sh: 1: nest: not found it seems that the nest.js cli is not available in the path during the production build, even though it's installed as a dev dependency in my package.json. #11 [prod 1/

### Observation B · question 78095654

**Docker single build artifact for multiple images**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78095654/docker-single-build-artifact-for-multiple-images>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

*Lexically these two share: tags dockerfile; title words build, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 16/40 — `78093369::78102512`

split: **holdout**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 468

### Observation A · question 78093369

**installing psycopg in alpine docker image**

tags: `docker`, `dockerfile`, `psycopg2`, `docker-image`  
source: <https://stackoverflow.com/questions/78093369/installing-psycopg-in-alpine-docker-image>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have the following dockerfile: FROM python:3.12.0-alpine3.18 WORKDIR /usr/src/app ENV PYTHONDONTWRITEBYTECODE 1 ENV PYTHONUNBUFFERED 1 RUN apk update && \ apk add --virtual build-deps gcc python3-dev musl-dev && \ apk add postgresql-dev COPY requirements ./requirements RUN pip install -r ./requirements/local.txt COPY . .

Error output quoted in the question:

    error occurs when the image is loaded: error: failed to solve: process "/bin/sh -c pip install -r ./requirements/local.txt" did not complete successfully: exit code: 1 i tried to install various dependencies in my docker
    error. what dependencies do i need to add to my dockerfile for psycopg to install? and also where can you read what dependencies you need to add and your dockerfile for certain libraries based on a certain image?

### Observation B · question 78102512

**docker: Error response from daemon: Duplicate mount point:: Mounting multiple docker volumes on same docker container having same target?**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78102512/docker-error-response-from-daemon-duplicate-mount-point-mounting-multiple-do>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to mount multiple docker volumes into same destination.

Error output quoted in the question:

    error message docker: error response from daemon: duplicate mount point: /rootdir1. i have gone through 1 . however, the problem is different. i am trying to mount multiple docker volume in same target location inside sa

*Lexically these two share: tags dockerfile; title words docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 17/40 — `78098380::78104298`

split: **development**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 32

### Observation A · question 78098380

**Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container**

tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`  
source: <https://stackoverflow.com/questions/78098380/make-docker-env-variables-from-an-env-file-available-in-build-step-dockerfil>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Premises Given a file oneSourceOfTruth.env : FOO=42 ... (many entries) and a docker-compose.yml : services: my-service: dockefile: ./Dockerfile env_file: oneSourceOfTruth.env 🏁 Objective I'd like to have all variables from oneSourceOfTruth.env available in the Dockerfile during the build step via docker compose build as well as in the container during runtime ( docker compose up ).

Error output quoted in the question:

    error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

### Observation B · question 78104298

**Add --add-opens java.base/java.lang=ALL-UNNAMED in Docker file**

tags: `docker`, `dockerfile`  
source: <https://stackoverflow.com/questions/78104298/add-add-opens-java-base-java-lang-all-unnamed-in-docker-file>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have this Docker configuration: # Use a Java runtime as the base image FROM openjdk:21-slim-buster VOLUME /tmp # Copy the built JAR file into the container ADD build/libs/engine.jar engine.jar # Expose the default port for the app EXPOSE 8080 # Start the app when the container launches ENTRYPOINT ["java", "-jar", "engine.jar", "--spring.config.additional-location=file:/engine-configuration.yml", "--add-opens java.b

*Lexically these two share: tags dockerfile; title words docker, file. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 18/40 — `78102512::78104298`

split: **development**  ·  band: `B_MEDIUM_SPECIFICITY`  ·  candidate rank 476

### Observation A · question 78102512

**docker: Error response from daemon: Duplicate mount point:: Mounting multiple docker volumes on same docker container having same target?**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78102512/docker-error-response-from-daemon-duplicate-mount-point-mounting-multiple-do>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to mount multiple docker volumes into same destination.

Error output quoted in the question:

    error message docker: error response from daemon: duplicate mount point: /rootdir1. i have gone through 1 . however, the problem is different. i am trying to mount multiple docker volume in same target location inside sa

### Observation B · question 78104298

**Add --add-opens java.base/java.lang=ALL-UNNAMED in Docker file**

tags: `docker`, `dockerfile`  
source: <https://stackoverflow.com/questions/78104298/add-add-opens-java-base-java-lang-all-unnamed-in-docker-file>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have this Docker configuration: # Use a Java runtime as the base image FROM openjdk:21-slim-buster VOLUME /tmp # Copy the built JAR file into the container ADD build/libs/engine.jar engine.jar # Expose the default port for the app EXPOSE 8080 # Start the app when the container launches ENTRYPOINT ["java", "-jar", "engine.jar", "--spring.config.additional-location=file:/engine-configuration.yml", "--add-opens java.b

*Lexically these two share: tags dockerfile; title words docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 19/40 — `78091032::78100506`

split: **development**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 605

### Observation A · question 78091032

**How to use Docker compose in c program?**

tags: `c`, `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78091032/how-to-use-docker-compose-in-c-program>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I want to isolate my development environment to create a project in C. But I don't know how to use Docker with C. I'm getting confused about running the program and I would like someone to help me. Take for example a "hello world" with an input. basic as a program. How can I make a docker compose and how to run it. And still with live-reload?

### Observation B · question 78100506

**KeyDB container problems in version 6.3.2 and later**

tags: `docker`, `docker-compose`, `keydb`  
source: <https://stackoverflow.com/questions/78100506/keydb-container-problems-in-version-6-3-2-and-later>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have a Java application that uses a redundant KeyDB, load-balanced through HAProxy, where I store the elements with information to facilitate the business logic of my application. A few months ago, I pulled the Docker container for KeyDB, where I previously had version 6.0.18, and it was updated to version 6.3.2.

Error output quoted in the question:

    error messages in my processes: in the container logs, it appears that the primary node is unable to establish communication with the secondary node when the error occurs, and the connection timer expires: from the hapro

*Lexically these two share: tags docker-compose. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 20/40 — `78092962::78096175`

split: **development**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 637

### Observation A · question 78092962

**Poetry in Docker creates venv despite `poetry env use system`**

tags: `python`, `docker`, `docker-compose`, `python-venv`, `python-poetry`  
source: <https://stackoverflow.com/questions/78092962/poetry-in-docker-creates-venv-despite-poetry-env-use-system>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Dockerfile: FROM python:3.12-bookworm # Configure Poetry ENV POETRY_VERSION=1.8.1 ENV POETRY_HOME=/opt/poetry ENV POETRY_VENV=/opt/poetry-venv ENV POETRY_CACHE_DIR=/opt/.cache # Install Poetry isolated from the system RUN python -m venv $POETRY_VENV \ && $POETRY_VENV/bin/pip install -U pip setuptools \ && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION} # Add Poetry to PATH ENV PATH="${PATH}:${POETRY_VENV}/bin"

Error output quoted in the question:

    error: web-1 | creating virtualenv djadja-va82wl8v-py3.12 in /opt/.cache/virtualenvs web-1 | command not found: uvicorn i've tried: poetry config virtualenvs.create false poetry config virtualenvs.in-project false cmd ["

### Observation B · question 78096175

**My postgresql database doesn't persist between docker runs**

tags: `django`, `postgresql`, `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78096175/my-postgresql-database-doesnt-persist-between-docker-runs>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am learning docker and postgresql and I have problem with persisting data between the re-runs of the app. My docker-compose.yml: version: '3.7' services: web: build: .

*Lexically these two share: tags docker-compose; title words docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 21/40 — `78095654::78097218`

split: **development**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 663

### Observation A · question 78095654

**Docker single build artifact for multiple images**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78095654/docker-single-build-artifact-for-multiple-images>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

### Observation B · question 78097218

**Mounting a local file to a specific path in the container of ActiveMQ Artemis, container stops working**

tags: `docker`, `docker-compose`, `jboss`, `activemq-artemis`, `artemiscloud`  
source: <https://stackoverflow.com/questions/78097218/mounting-a-local-file-to-a-specific-path-in-the-container-of-activemq-artemis-c>  
licence: CC BY-SA 4.0, Stack Exchange Network

> The image I am using is quay.io/artemiscloud/activemq-artemis-broker . My docker-compose.yml is: version: "3" services: artemis: image: quay.io/artemiscloud/activemq-artemis-broker environment: AMQ_USER: admin AMQ_PASSWORD: password ports: - "5672:5672" - "61616:61616" - "8161:8161" networks: - backend networks: backend: driver: bridge When I run docker-compose up , the container can successfully run.

Error output quoted in the question:

    failure log below) after verified these things. i stoped the container by docker-compose down . then, i modified my docker-compose.yml to mount a local file on my host ./config/my.json to the container path /home/jboss/b
    failed. the log shows this message: 2024-03-03 18:51:40 /opt/amq/bin/launch.sh: line 49: /home/jboss/broker/bin/artemis: no such file or directory 2024-03-03 18:51:40 running broker the logs basically says the launch.sh 

*Lexically these two share: tags docker-compose. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 22/40 — `78095654::78099949`

split: **development**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 666

### Observation A · question 78095654

**Docker single build artifact for multiple images**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78095654/docker-single-build-artifact-for-multiple-images>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

### Observation B · question 78099949

**how to merge compose file fragments correctly**

tags: `docker`, `docker-compose`, `yaml`  
source: <https://stackoverflow.com/questions/78099949/how-to-merge-compose-file-fragments-correctly>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I would like to merge the seaweed-master-defaults and deploy_test01 fragments into the seaweed_master_test01 service, see the example below: version: "3.9" x-service-defaults: &service-defaults # common defaults for all services deploy: restart_policy: condition: on-failure delay: 10s max_attempts: 3 window: 120s endpoint_mode: dnsrr x-seaweeed-master-defaults: &seaweed-master-defaults image: chrislusf/seaweedfs volu

*Lexically these two share: tags docker-compose. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 23/40 — `78095654::78105118`

split: **holdout**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 75

### Observation A · question 78095654

**Docker single build artifact for multiple images**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78095654/docker-single-build-artifact-for-multiple-images>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

### Observation B · question 78105118

**To configure Docker to use different network interfaces on a host with multiple network interfaces?**

tags: `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78105118/to-configure-docker-to-use-different-network-interfaces-on-a-host-with-multiple>  
licence: CC BY-SA 4.0, Stack Exchange Network

> To configure Docker to use different network interfaces on a host with multiple network interfaces, and using Docker Compose to start services with host network mode How to solve ; By default, when starting, it uses the IP of ens0. But I want to communicate with ens192.

*Lexically these two share: tags docker-compose; title words docker, multiple. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 24/40 — `78096903::78099350`

split: **holdout**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 680

### Observation A · question 78096903

**docker compose file, set keys from environment**

tags: `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78096903/docker-compose-file-set-keys-from-environment>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I'm trying to use environment variables in my docker compose file, with docker stack. When I to use an environment variable like this, it works: services: service_test01: networks: - ${network} # more options here...

### Observation B · question 78099350

**Docker-compose with Golang and Postgres connection is refused**

tags: `postgresql`, `docker`, `go`, `docker-compose`  
source: <https://stackoverflow.com/questions/78099350/docker-compose-with-golang-and-postgres-connection-is-refused>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to make the connection with PostgreSQL using Docker Compose. I have a Golang CLI application called flow and it creates, views, adjust's, gets, and removes the budget information. When I write the docker docker-compose up -d , it creates two images and one container.

Error output quoted in the question:

    refused message. here is the command: docker run -it flow-budget_planner ./flow budget create -c category -a 300 what should i do to make the connection established and enter the data in postgresql successfully using doc
    error) { v := variables{ host: middleware.loadenvvariable("host"), port: middleware.loadenvvariable("port"), user: middleware.loadenvvariable("user"), password: middleware.loadenvvariable("password"), dbname: middleware.

*Lexically these two share: tags docker-compose. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 25/40 — `78096903::78102669`

split: **holdout**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 683

### Observation A · question 78096903

**docker compose file, set keys from environment**

tags: `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78096903/docker-compose-file-set-keys-from-environment>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I'm trying to use environment variables in my docker compose file, with docker stack. When I to use an environment variable like this, it works: services: service_test01: networks: - ${network} # more options here...

### Observation B · question 78102669

**Hawkbit server doesn't work after few hours online**

tags: `docker`, `docker-compose`, `eclipse-hawkbit`, `hawkbit`  
source: <https://stackoverflow.com/questions/78102669/hawkbit-server-doesnt-work-after-few-hours-online>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have an hawkbit server behind a traefik proxy running on docker-compose mysql: image: "mysql:latest" environment: MYSQL_DATABASE: "hawkbit" MYSQL_ALLOW_EMPTY_PASSWORD: "true" restart: always ports: - "3306:3306" volumes: mysql-db-data:/var/lib/mysql labels: NAME: "mysql" networks: hawkbit-network hawkbit: image: "hawkbit/hawkbit-update-server:latest-mysql" environment: - 'SPRING_DATASOURCE_URL=jdbc:mariadb://mysql:

Error output quoted in the question:

    error code : 1049 message : (conn=82) unknown database 'hawkbit' at org.flywaydb.core.internal.jdbc.jdbcutils.openconnection(jdbcutils.java:60) at org.flywaydb.core.internal.jdbc.jdbcconnectionfactory.<init>(jdbcconnecti

*Lexically these two share: tags docker-compose. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 26/40 — `78102669::78103425`

split: **development**  ·  band: `C_LOW_SPECIFICITY`  ·  candidate rank 728

### Observation A · question 78102669

**Hawkbit server doesn't work after few hours online**

tags: `docker`, `docker-compose`, `eclipse-hawkbit`, `hawkbit`  
source: <https://stackoverflow.com/questions/78102669/hawkbit-server-doesnt-work-after-few-hours-online>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have an hawkbit server behind a traefik proxy running on docker-compose mysql: image: "mysql:latest" environment: MYSQL_DATABASE: "hawkbit" MYSQL_ALLOW_EMPTY_PASSWORD: "true" restart: always ports: - "3306:3306" volumes: mysql-db-data:/var/lib/mysql labels: NAME: "mysql" networks: hawkbit-network hawkbit: image: "hawkbit/hawkbit-update-server:latest-mysql" environment: - 'SPRING_DATASOURCE_URL=jdbc:mariadb://mysql:

Error output quoted in the question:

    error code : 1049 message : (conn=82) unknown database 'hawkbit' at org.flywaydb.core.internal.jdbc.jdbcutils.openconnection(jdbcutils.java:60) at org.flywaydb.core.internal.jdbc.jdbcconnectionfactory.<init>(jdbcconnecti

### Observation B · question 78103425

**Using a single connectionstring for local and in docker (Database Access)**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78103425/using-a-single-connectionstring-for-local-and-in-docker-database-access>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Is it possible to have an API with the same connectionstring for running locally and in Docker?

Error output quoted in the question:

    error detail=true" }, docker-compose.yaml version: '3.4' services: example-api: image: ${docker_registry-}api container_name: example-api restart: always build: context: . dockerfile: src/api/dockerfile depends_on: - pos

*Lexically these two share: tags docker-compose. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 27/40 — `78086542::78099519`

split: **development**  ·  band: `D_DIAGNOSTIC_WRAPPER`  ·  candidate rank 239

### Observation A · question 78086542

**Docker compose/ failed to create task for container**

tags: `python`, `docker`, `pycharm`  
source: <https://stackoverflow.com/questions/78086542/docker-compose-failed-to-create-task-for-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> when i up my docker (docker-compose up --build) i take this error: shop-backend-database | 2024-03-01 08:31:53.031 UTC [1] LOG: database system is ready to accept connections Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: "/usr/src/app/entrypoint.sh": permission denied : unknown my doc

Error output quoted in the question:

    error: shop-backend-database | 2024-03-01 08:31:53.031 utc [1] log: database system is ready to accept connections error response from daemon: failed to create task for container: failed to create shim task: oci runtime 
    failed: unable to start container process: exec: "/usr/src/app/entrypoint.sh": permission denied : unknown my dockerfile: from python:3.8 workdir /usr/src/app/ env pythondontwritebytecode 1 env pythonunbuffered 1 run pip

### Observation B · question 78099519

**Cannot run a "docker compose up"**

tags: `docker`, `jupyter`, `pipenv`  
source: <https://stackoverflow.com/questions/78099519/cannot-run-a-docker-compose-up>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have been trying to work on creating my Dockerfile in which Jupyter Lab, along with the pip extensions described in the Pipfile and Pipfile.lock, runs in my Pipenv virtual environment.

Error output quoted in the question:

    error when i ran sudo docker compose up as follwoing: [+] running 1/0 ✔ container docker-webapp-1 recreated 0.1s attaching to webapp-1 error response from daemon: failed to create task for container: failed to create shi
    failed: runc create failed: unable to start container process: exec: "/app/.venv/bin/pipenv": stat /app/.venv/bin/pipenv: no such file or directory: unknown i don't see any issues in these files, but i'm unable to start 

*Lexically these two share: title words compose, docker; a 106-character error fragment. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 28/40 — `78099519::78099680`

split: **holdout**  ·  band: `D_DIAGNOSTIC_WRAPPER`  ·  candidate rank 400

### Observation A · question 78099519

**Cannot run a "docker compose up"**

tags: `docker`, `jupyter`, `pipenv`  
source: <https://stackoverflow.com/questions/78099519/cannot-run-a-docker-compose-up>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have been trying to work on creating my Dockerfile in which Jupyter Lab, along with the pip extensions described in the Pipfile and Pipfile.lock, runs in my Pipenv virtual environment.

Error output quoted in the question:

    error when i ran sudo docker compose up as follwoing: [+] running 1/0 ✔ container docker-webapp-1 recreated 0.1s attaching to webapp-1 error response from daemon: failed to create task for container: failed to create shi
    failed: runc create failed: unable to start container process: exec: "/app/.venv/bin/pipenv": stat /app/.venv/bin/pipenv: no such file or directory: unknown i don't see any issues in these files, but i'm unable to start 

### Observation B · question 78099680

**Unable to run uvicorn under gunicorn in a Docker container**

tags: `docker`, `fastapi`, `gunicorn`, `uvicorn`  
source: <https://stackoverflow.com/questions/78099680/unable-to-run-uvicorn-under-gunicorn-in-a-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> The following Dockerfile builds a working Fastapi demo app running under a single instance of uvicorn: # example of a multistage build # Stage 1: Builder # Use the official larger Docker Python image FROM python:3.11-bookworm as builder # Install python modules with known release RUN pip install poetry==1.8.2 RUN pip install gunicorn==21.2.0 # Set Poetry environment variables for non-interactive installation ENV POET

Error output quoted in the question:

    error: (.venv) bob /volumes/2tbwdb/code/uvitest [main] $ docker compose up -d [+] running 0/1 ⠹ container uvitest-uvitest-1 starting 0.2s error response from daemon: failed to create task for container: failed to create 
    failed: runc create failed: unable to start container process: exec: "gunicorn": executable file not found in $path: unknown please help fix. thanks

*Lexically these two share: title words docker, run; a 103-character error fragment. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 29/40 — `78086323::78086387`

split: **development**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 89

### Observation A · question 78086323

**Getting ETIMEDOUT while running Telegraf bot in docker container with network mode host**

tags: `node.js`, `docker`, `docker-network`, `telegraf`  
source: <https://stackoverflow.com/questions/78086323/getting-etimedout-while-running-telegraf-bot-in-docker-container-with-network-mo>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Telegraf.js Version: Final version Node.js Version: v21 Operating System: Ubuntu:latest Minimal Example Code Reproducing the Issue const { Telegraf } = require('telegraf') const bot = new Telegraf('TELEGRAM_TOKEN') bot.telegram.setMyCommands([ {command: 'start', description: 'Starts the system'}, {command: 'restart', description: 'Restarts the system'}, {command: 'help', description: 'Show commands help'}, ]) bot.sta

Error output quoted in the question:

    error instantly: fetcherror: request to https://api.telegram.org/bot6411340281:[redacted]/setmycommands failed, reason: at clientrequest.<anonymous> (/usr/src/app/node_modules/node-fetch/lib/index.js:1501:11) at clientre
    error while running in host mode network?

### Observation B · question 78086387

**Troubles with postgres while building docker container**

tags: `django`, `linux`, `postgresql`, `docker`, `devops`  
source: <https://stackoverflow.com/questions/78086387/troubles-with-postgres-while-building-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to lauch DJANGO + POSTGRES inside a single container with DOCKERFILE. I have the folowing dockerfile which basicly installs all the python dependencies and postgresql. Then it lauches the script to create db and user (presented below). FROM python WORKDIR /app COPY requirements.txt . RUN pip install -r requirements.txt COPY . .

Error output quoted in the question:

    error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/djang
    error checking a consistent migration history performed for database connection 'default': connection to server at "localhost" (127.0.0.1), port 5432 failed: connection refused 3.377 is the server running on that host an

*Lexically these two share: title words container, docker, while. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 30/40 — `78086387::78097003`

split: **holdout**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 203

### Observation A · question 78086387

**Troubles with postgres while building docker container**

tags: `django`, `linux`, `postgresql`, `docker`, `devops`  
source: <https://stackoverflow.com/questions/78086387/troubles-with-postgres-while-building-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I am trying to lauch DJANGO + POSTGRES inside a single container with DOCKERFILE. I have the folowing dockerfile which basicly installs all the python dependencies and postgresql. Then it lauches the script to create db and user (presented below). FROM python WORKDIR /app COPY requirements.txt . RUN pip install -r requirements.txt COPY . .

Error output quoted in the question:

    error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/djang
    error checking a consistent migration history performed for database connection 'default': connection to server at "localhost" (127.0.0.1), port 5432 failed: connection refused 3.377 is the server running on that host an

### Observation B · question 78097003

**Curl PHP cannot connect to localhost inside Docker container**

tags: `php`, `docker`, `curl`  
source: <https://stackoverflow.com/questions/78097003/curl-php-cannot-connect-to-localhost-inside-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> My Docker-compose.yml is: version: '3.8' services: app: build: context: . dockerfile: ./docker/app/Dockerfile command: bash -c " if [ ! -d /var/www/vendor ] ; then composer install --no-interaction ; fi && if [ ! -f /var/www/.env ] ; then composer env-set ; fi && if [ ! -d /var/www/node_modules ] ; then npm install && npm install chokidar && npm run dev ; fi && if [ !

Error output quoted in the question:

    error. found that problem exactly in docker's nature of http://localhost:8086 (( when change url to http://influx:8086 - got curl 6. how to work with docker containers by php curl ?

*Lexically these two share: title words container, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 31/40 — `78086501::78103425`

split: **development**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 222

### Observation A · question 78086501

**Docker & compose errors on Golang + React + MySQL app. Binary not found and unitilialized database**

tags: `docker`  
source: <https://stackoverflow.com/questions/78086501/docker-compose-errors-on-golang-react-mysql-app-binary-not-found-and-unit>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have a Golang + MySQL + React project. When I call to compose up I get some errors that I have to overcome: these are "binary not found" and "unitilialized database". I would be very grateful if someone could help me.

Error output quoted in the question:

    errors that i have to overcome: these are "binary not found" and "unitilialized database". i would be very grateful if someone could help me. my directory tree is: the nd-back dockerfile is: from golang:1.22-alpine3.19 r
    errors: attaching to back-1, db-1, front-1 db-1 | 2024-03-01 08:21:18+00:00 [note] [entrypoint]: entrypoint script for mysql server 8.3.0-1.el8 started. db-1 | 2024-03-01 08:21:18+00:00 [note] [entrypoint]: switching to 

### Observation B · question 78103425

**Using a single connectionstring for local and in docker (Database Access)**

tags: `docker`, `docker-compose`, `dockerfile`  
source: <https://stackoverflow.com/questions/78103425/using-a-single-connectionstring-for-local-and-in-docker-database-access>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Is it possible to have an API with the same connectionstring for running locally and in Docker?

Error output quoted in the question:

    error detail=true" }, docker-compose.yaml version: '3.4' services: example-api: image: ${docker_registry-}api container_name: example-api restart: always build: context: . dockerfile: src/api/dockerfile depends_on: - pos

*Lexically these two share: title words database, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 32/40 — `78086542::78103907`

split: **holdout**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 244

### Observation A · question 78086542

**Docker compose/ failed to create task for container**

tags: `python`, `docker`, `pycharm`  
source: <https://stackoverflow.com/questions/78086542/docker-compose-failed-to-create-task-for-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> when i up my docker (docker-compose up --build) i take this error: shop-backend-database | 2024-03-01 08:31:53.031 UTC [1] LOG: database system is ready to accept connections Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: "/usr/src/app/entrypoint.sh": permission denied : unknown my doc

Error output quoted in the question:

    error: shop-backend-database | 2024-03-01 08:31:53.031 utc [1] log: database system is ready to accept connections error response from daemon: failed to create task for container: failed to create shim task: oci runtime 
    failed: unable to start container process: exec: "/usr/src/app/entrypoint.sh": permission denied : unknown my dockerfile: from python:3.8 workdir /usr/src/app/ env pythondontwritebytecode 1 env pythonunbuffered 1 run pip

### Observation B · question 78103907

**How can I create a Dockerfile that runs both my nodeJS server and also launches mongodb? All in the same container**

tags: `node.js`, `mongodb`, `docker`, `dockerfile`  
source: <https://stackoverflow.com/questions/78103907/how-can-i-create-a-dockerfile-that-runs-both-my-nodejs-server-and-also-launches>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I need to be able to run within the same container both: my nodejs server.js and mongodb. I know it is possible to achieve this with docker-compose or with two separate containers but that is not an option here. I need both services running on the same container.

*Lexically these two share: title words container, create. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 33/40 — `78087887::78103879`

split: **development**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 270

### Observation A · question 78087887

**QStandardPaths: runtime directory '/tmp' is not owned by UID 1000, but a directory permissions 0777 owned by UID 0 GID 0 in docker container**

tags: `linux`, `docker`, `permissions`  
source: <https://stackoverflow.com/questions/78087887/qstandardpaths-runtime-directory-tmp-is-not-owned-by-uid-1000-but-a-directo>  
licence: CC BY-SA 4.0, Stack Exchange Network

> This error appeared when I installed wkhtmltopdf in my container. Here is part of my Dockerfile ENV XDG_RUNTIME_DIR=/tmp RUN python3.9 -m venv /py && \ ... apk add wkhtmltopdf && \ ... adduser --disabled-password --no-create-home ozangue && \ ... ENV PATH="/scripts:/py/bin:$PATH" USER ozangue When I try to add the following lines: chown -R ozangue:ozangue /tmp && \ chmod -R 755 /tmp the error message changes.

Error output quoted in the question:

    error appeared when i installed wkhtmltopdf in my container. here is part of my dockerfile env xdg_runtime_dir=/tmp run python3.9 -m venv /py && \ ... apk add wkhtmltopdf && \ ... adduser --disabled-password --no-create-
    error message changes. i get: wkhtmltopdf exited with non-zero code -11. error: unknown error when i change the permissions like this: chmod -r 7777 /tmp i always get the precedent error message: wkhtmltopdf exited with 

### Observation B · question 78103879

**Spring Boot App in Docker container - SQL Server Integrated Security**

tags: `java`, `sql-server`, `spring`, `spring-boot`, `docker`  
source: <https://stackoverflow.com/questions/78103879/spring-boot-app-in-docker-container-sql-server-integrated-security>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have a Spring Boot App (RESTful Service) that runs in a Docker Container and the Database Server is outside of the Docker Cluster, it´s on a special server cluster. In dev, the app works with "Integrated security" without a problem (because of my account), but in a docker container, there is no Kerberos Ticket available to work with. Is it even possible to add the JDBC Auth lib to the container and use it?

*Lexically these two share: title words container, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 34/40 — `78088692::78097184`

split: **holdout**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 281

### Observation A · question 78088692

**strange behavior when getting env var in container**

tags: `django`, `docker`, `environment-variables`, `python-poetry`  
source: <https://stackoverflow.com/questions/78088692/strange-behavior-when-getting-env-var-in-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I need to get an env var from an docker container. This build is triggered with a docker compose file and I passed also the env variables with env_file . When I login to the container with docker exec -it conatinerName bash I can echo the variable and get correct output. Even when I trigger docker exec -it containerName echo $DEBUG inside the poetry environment, I get the correct answer.

### Observation B · question 78097184

**Can't pass env variables from GitHub Actions to Docker container**

tags: `docker`, `github`, `github-actions`  
source: <https://stackoverflow.com/questions/78097184/cant-pass-env-variables-from-github-actions-to-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I'm trying to pass variables in GitHub: I have the following step in workflow: - name: SSH into VPS and deploy uses: appleboy/ssh-action@master with: host: ${{ secrets.VPSHOST }} username: ${{ secrets.USERNAME }} key: ${{ secrets.SSH_KEY }} script: | export BLOG_POSTGRES_DB=${{ env.BLOG_POSTGRES_DB }} export BLOG_POSTGRES_USER=${{ env.BLOG_POSTGRES_USER }} export BLOG_POSTGRES_PASSWORD="${{ secrets.BLOG_POSTGRES_PASS

*Lexically these two share: title words container, env. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 35/40 — `78089075::78097003`

split: **development**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 92

### Observation A · question 78089075

**Can not connect with click-house running inside docker with nodejs**

tags: `node.js`, `docker`, `clickhouse`  
source: <https://stackoverflow.com/questions/78089075/can-not-connect-with-click-house-running-inside-docker-with-nodejs>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have downloaded this click-house docker image https://hub.docker.com/r/clickhouse/clickhouse-server/ I started click-house server with the following command docker run --network=host --name some-clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-server I connected with clickhouse with the following command docker exec -it some-clickhouse-server clickhouse-client Output of the above command ClickH

Error output quoted in the question:

    error. same is true for port 9000 as well. i am using host network in docker, so i should be able to connect this interface from my browser. same is happening for nodejs as well const { clickhouse } = require("clickhouse
    error on terminal error inserting row: error: connect econnrefused ::1:9000 at tcpconnectwrap.afterconnect [as oncomplete] (node:net:1532:16) { errno: -61, code: 'econnrefused', syscall: 'connect', address: '::1', port: 

### Observation B · question 78097003

**Curl PHP cannot connect to localhost inside Docker container**

tags: `php`, `docker`, `curl`  
source: <https://stackoverflow.com/questions/78097003/curl-php-cannot-connect-to-localhost-inside-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> My Docker-compose.yml is: version: '3.8' services: app: build: context: . dockerfile: ./docker/app/Dockerfile command: bash -c " if [ ! -d /var/www/vendor ] ; then composer install --no-interaction ; fi && if [ ! -f /var/www/.env ] ; then composer env-set ; fi && if [ ! -d /var/www/node_modules ] ; then npm install && npm install chokidar && npm run dev ; fi && if [ !

Error output quoted in the question:

    error. found that problem exactly in docker's nature of http://localhost:8086 (( when change url to http://influx:8086 - got curl 6. how to work with docker containers by php curl ?

*Lexically these two share: title words connect, docker, inside. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 36/40 — `78097003::78098380`

split: **development**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 357

### Observation A · question 78097003

**Curl PHP cannot connect to localhost inside Docker container**

tags: `php`, `docker`, `curl`  
source: <https://stackoverflow.com/questions/78097003/curl-php-cannot-connect-to-localhost-inside-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> My Docker-compose.yml is: version: '3.8' services: app: build: context: . dockerfile: ./docker/app/Dockerfile command: bash -c " if [ ! -d /var/www/vendor ] ; then composer install --no-interaction ; fi && if [ ! -f /var/www/.env ] ; then composer env-set ; fi && if [ ! -d /var/www/node_modules ] ; then npm install && npm install chokidar && npm run dev ; fi && if [ !

Error output quoted in the question:

    error. found that problem exactly in docker's nature of http://localhost:8086 (( when change url to http://influx:8086 - got curl 6. how to work with docker containers by php curl ?

### Observation B · question 78098380

**Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container**

tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`  
source: <https://stackoverflow.com/questions/78098380/make-docker-env-variables-from-an-env-file-available-in-build-step-dockerfil>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Premises Given a file oneSourceOfTruth.env : FOO=42 ... (many entries) and a docker-compose.yml : services: my-service: dockefile: ./Dockerfile env_file: oneSourceOfTruth.env 🏁 Objective I'd like to have all variables from oneSourceOfTruth.env available in the Dockerfile during the build step via docker compose build as well as in the container during runtime ( docker compose up ).

Error output quoted in the question:

    error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Lexically these two share: title words container, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 37/40 — `78097216::78099680`

split: **development**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 378

### Observation A · question 78097216

**Postman Requests From Host Machine Are Not Able to Reach Tomcat Server Running On Docker Container**

tags: `java`, `docker`, `rest`, `servlets`, `containers`  
source: <https://stackoverflow.com/questions/78097216/postman-requests-from-host-machine-are-not-able-to-reach-tomcat-server-running-o>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I was working on a java servlet REST Api project GitHub Repo , and I decided to create a Docker image for the project which I can deploy easily to some cloud platform or maybe publish to some container registry. So I created the Dockerfile for the above mentioned requirement which has two stages in it.

Error output quoted in the question:

    error. i tried removing the first stage of building the .war file in the container itself by copying the .war file generated in local to the webapps folder of the tomcat container. and surprisingly that time when i start

### Observation B · question 78099680

**Unable to run uvicorn under gunicorn in a Docker container**

tags: `docker`, `fastapi`, `gunicorn`, `uvicorn`  
source: <https://stackoverflow.com/questions/78099680/unable-to-run-uvicorn-under-gunicorn-in-a-docker-container>  
licence: CC BY-SA 4.0, Stack Exchange Network

> The following Dockerfile builds a working Fastapi demo app running under a single instance of uvicorn: # example of a multistage build # Stage 1: Builder # Use the official larger Docker Python image FROM python:3.11-bookworm as builder # Install python modules with known release RUN pip install poetry==1.8.2 RUN pip install gunicorn==21.2.0 # Set Poetry environment variables for non-interactive installation ENV POET

Error output quoted in the question:

    error: (.venv) bob /volumes/2tbwdb/code/uvitest [main] $ docker compose up -d [+] running 0/1 ⠹ container uvitest-uvitest-1 starting 0.2s error response from daemon: failed to create task for container: failed to create 
    failed: runc create failed: unable to start container process: exec: "gunicorn": executable file not found in $path: unknown please help fix. thanks

*Lexically these two share: title words container, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 38/40 — `78097574::78105004`

split: **holdout**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 386

### Observation A · question 78097574

**How to setup the netCDF4 package in multistage docker build?**

tags: `python`, `docker`, `netcdf`, `netcdf4`  
source: <https://stackoverflow.com/questions/78097574/how-to-setup-the-netcdf4-package-in-multistage-docker-build>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have an existing dockerfile that runs a python program involving netCDF4.

### Observation B · question 78105004

**Docker build fails because unable to install `libc-bin`**

tags: `ruby-on-rails`, `docker`, `kamal`  
source: <https://stackoverflow.com/questions/78105004/docker-build-fails-because-unable-to-install-libc-bin>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Using kamal to deploy a rails app, but having trouble with docker and getting all installed. I in the past had it setup to use esbuild and yarn, but switched to bun later. Now, I need to install node for a tool on the ruby side, so trying to go back to esbuild/yarn/node for the setup.

Error output quoted in the question:

    error processing package libc-bin (--configure): 63.34 installed libc-bin package post-installation script subprocess returned error exit status 139 63.44 errors were encountered while processing: 63.44 libc-bin 63.54 e:
    error code (1) ------ dockerfile:64 -------------------- 63 | # install packages needed for deployment 64 | >>> run apt-get update -qq && \ 65 | >>> apt-get install --no-install-recommends -y curl libvips postgresql-clie

*Lexically these two share: title words build, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 39/40 — `78097574::78105286`

split: **development**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 387

### Observation A · question 78097574

**How to setup the netCDF4 package in multistage docker build?**

tags: `python`, `docker`, `netcdf`, `netcdf4`  
source: <https://stackoverflow.com/questions/78097574/how-to-setup-the-netcdf4-package-in-multistage-docker-build>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I have an existing dockerfile that runs a python program involving netCDF4.

### Observation B · question 78105286

**Docker Build With Low RAM Causing OOM - Raspberry Pi 4B**

tags: `docker`, `ubuntu-20.04`, `raspberry-pi4`  
source: <https://stackoverflow.com/questions/78105286/docker-build-with-low-ram-causing-oom-raspberry-pi-4b>  
licence: CC BY-SA 4.0, Stack Exchange Network

> Hardware: Raspberry Pi 4B (linux/arm64/v8) - 4GB RAM & 64 GB SD card OS: Ubuntu 20.04 LTS TLDR What can I do to build the image on my Pi without OOM? Can I emulate a build from one of my AMD devices to build as ARM architecture for the Pi 4B to pull from DockerHub? I want to build this Dockerfile and run the container for my drone-project .

Error output quoted in the question:

    error: killed (program cc1plus)

*Lexically these two share: title words build, docker. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---

## PAIR 40/40 — `78098568::78105118`

split: **holdout**  ·  band: `E_DIFFERENT_TAGS_SHARED_TOKENS`  ·  candidate rank 398

### Observation A · question 78098568

**Setting Docker network as external via Terraform**

tags: `docker`, `terraform`, `traefik`, `terraform-provider-docker`  
source: <https://stackoverflow.com/questions/78098568/setting-docker-network-as-external-via-terraform>  
licence: CC BY-SA 4.0, Stack Exchange Network

> I'm in the process of building out some of my Docker Compose containers via Terraform.

### Observation B · question 78105118

**To configure Docker to use different network interfaces on a host with multiple network interfaces?**

tags: `docker`, `docker-compose`  
source: <https://stackoverflow.com/questions/78105118/to-configure-docker-to-use-different-network-interfaces-on-a-host-with-multiple>  
licence: CC BY-SA 4.0, Stack Exchange Network

> To configure Docker to use different network interfaces on a host with multiple network interfaces, and using Docker Compose to start services with host network mode How to solve ; By default, when starting, it uses the IP of ens0. But I want to communicate with ens192.

*Lexically these two share: title words docker, network. That is why the pair was surfaced, and it is not an argument that they are one family.*

**Are these substantially the same user problem, pain or blocked goal, such
that one product, tool, documentation intervention or workflow could
reasonably help both?**

**Your label:** `____________`

---
