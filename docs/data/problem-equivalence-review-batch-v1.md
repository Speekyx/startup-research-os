# Problem-equivalence review batch V1 — blind human labels

**Mission 1.24 §8. Generated, never hand-picked.** Regenerate with
`python infrastructure/scripts/render_equivalence_batch.py`.

- rubric: `problem-equivalence-rubric@1.0.0`
- candidate generator: `docker-lexical-candidates@1.0.0`
- batch selection: `review-batch-selection@1.0.0`
- corpus: 89 Docker `community_question` observations (`mission-1.20-normalize`)
- pairs: **40** — 23 development, 17 holdout

> **No model has seen any of these pairs and no prediction exists.** Nothing in
> this file was produced by an LLM. The labels you write here are the reference
> set; the classifier is scored against them, never the other way round.

## How to answer

For each pair write `SAME`, `DIFFERENT` or `UNCERTAIN` on its **Your label** line.

- **SAME** — a reader who had the working fix for one would, from that fix alone,
  know what to change for the other, and the change is to the same component,
  addressing the same class of misconfiguration or defect.
- **DIFFERENT** — different actionable failure concepts, even where the tool, the
  tags, the wrapper diagnostic or the generic error class are shared.
- **UNCERTAIN** — the published text does not establish the concept on both sides.
  This is a real answer, not a skipped one, and it is the counterpart of the
  classifier's mandatory ABSTAIN.

None of the following makes two questions the same problem, on its own or
together: the same tool; the same tags; the same wrapper diagnostic however long
the shared string; the same generic error class; the same broad symptom; the same
language, framework or base image.

## Why the split is already decided

Each pair is marked `development` or `holdout`, computed from its id before any
label existed. Five pairs are pinned to `development` because the rubric quotes
them or describes their pattern, so the classifier is shown their answer in its
own instructions -- counting those as holdout successes would inflate the result.

## The acceptance criterion, stated before any of this is scored

> The classifier passes only if it produces ZERO false SAME_PROBLEM decisions on the holdout -- a pair the reviewer labelled DIFFERENT or UNCERTAIN and the model called SAME. A model may ABSTAIN freely; abstention is never counted against it, because the alternative to an abstention here is a guess. The evaluation is only reportable at all with at least 12 labelled holdout pairs and at least one SAME anywhere in the reference set: with no positive, a classifier that answered DIFFERENT to everything would score perfectly, and nothing would have been measured. Below either threshold the outcome is EVALUATION_INSUFFICIENT rather than a pass. No accuracy, precision or recall figure is a pass condition, because a proportion over a few dozen pairs has an interval wider than any difference it could show.

## Scope, which every downstream statement inherits

> Scope: the 60 pairs surfaced by docker-lexical-candidates@1.0.0 out of 3916 possible pairs over 89 observations, capped at 60. A pair this generator did not surface is UNCONSIDERED, not different. No statement derived from this set describes all repeated problems in the corpus, and none may be worded as though it did.

---

### 1. `78086542::78099519` — development

*Pinned to development: the same shared-wrapper pattern the rubric describes and names; in-sample by description even though the ids are not quoted.*

**A · 78086542** — Docker compose/ failed to create task for container  
tags: `python`, `docker`, `pycharm`

> error: shop-backend-database | 2024-03-01 08:31:53.031 utc [1] log: database system is ready to accept connections error response from daemon: failed to create task for container: failed to create shim task: oci runtime create failed: runc 

**B · 78099519** — Cannot run a "docker compose up"  
tags: `docker`, `jupyter`, `pipenv`

> error when i ran sudo docker compose up as follwoing: [+] running 1/0 ✔ container docker-webapp-1 recreated 0.1s attaching to webapp-1 error response from daemon: failed to create task for container: failed to create shim task: oci runtime 

*Surfaced because: shares 2 title token(s); shares a 106-character diagnostic fragment.*

*Shared fragment, 106 characters:* ` error response from daemon: failed to create task for container: failed to create shim task: oci runtime `

**Your label:** `____________`

---

### 2. `78086542::78099680` — development

*Pinned to development: quoted verbatim in the rubric's non-qualifying worked example, so the classifier is shown the answer in its own instructions.*

**A · 78086542** — Docker compose/ failed to create task for container  
tags: `python`, `docker`, `pycharm`

> error: shop-backend-database | 2024-03-01 08:31:53.031 utc [1] log: database system is ready to accept connections error response from daemon: failed to create task for container: failed to create shim task: oci runtime create failed: runc 

**B · 78099680** — Unable to run uvicorn under gunicorn in a Docker container  
tags: `docker`, `fastapi`, `gunicorn`, `uvicorn`

> error: (.venv) bob /volumes/2tbwdb/code/uvitest [main] $ docker compose up -d [+] running 0/1 ⠹ container uvitest-uvitest-1 starting 0.2s error response from daemon: failed to create task for container: failed to create shim task: oci runti

*Surfaced because: shares 2 title token(s); shares a 104-character diagnostic fragment.*

*Shared fragment, 104 characters:* `s error response from daemon: failed to create task for container: failed to create shim task: oci runti`

**Your label:** `____________`

---

### 3. `78099519::78099680` — development

*Pinned to development: the same shared-wrapper pattern the rubric describes and names; in-sample by description even though the ids are not quoted.*

**A · 78099519** — Cannot run a "docker compose up"  
tags: `docker`, `jupyter`, `pipenv`

> error when i ran sudo docker compose up as follwoing: [+] running 1/0 ✔ container docker-webapp-1 recreated 0.1s attaching to webapp-1 error response from daemon: failed to create task for container: failed to create shim task: oci runtime 

**B · 78099680** — Unable to run uvicorn under gunicorn in a Docker container  
tags: `docker`, `fastapi`, `gunicorn`, `uvicorn`

> error: (.venv) bob /volumes/2tbwdb/code/uvitest [main] $ docker compose up -d [+] running 0/1 ⠹ container uvitest-uvitest-1 starting 0.2s error response from daemon: failed to create task for container: failed to create shim task: oci runti

*Surfaced because: shares 2 title token(s); shares a 103-character diagnostic fragment.*

*Shared fragment, 103 characters:* ` error response from daemon: failed to create task for container: failed to create shim task: oci runti`

**Your label:** `____________`

---

### 4. `78093369::78105004` — development

**A · 78093369** — installing psycopg in alpine docker image  
tags: `docker`, `dockerfile`, `psycopg2`, `docker-image`

> error occurs when the image is loaded: error: failed to solve: process "/bin/sh -c pip install -r ./requirements/local.txt" did not complete successfully: exit code: 1 i tried to install various dependencies in my dockerfile. but always the

**B · 78105004** — Docker build fails because unable to install `libc-bin`  
tags: `ruby-on-rails`, `docker`, `kamal`

> error processing package libc-bin (--configure): 63.34 installed libc-bin package post-installation script subprocess returned error exit status 139 63.44 errors were encountered while processing: 63.44 libc-bin 63.54 e: sub-process /usr/bi

*Surfaced because: shares a 45-character diagnostic fragment.*

*Shared fragment, 45 characters:* `" did not complete successfully: exit code: 1`

**Your label:** `____________`

---

### 5. `78097579::78103879` — holdout

**A · 78097579** — Spring Boot Application doesn't expose the port in Docker  
tags: `java`, `spring-boot`, `docker`, `port`

> failed to connect to 127.0.0.1 port 8090 after 0 ms: connection refused i run the container via docker run -it javaproj . here's the application.properties: server.port=8090 spring.mvc.static-path-pattern=/static/** and the dockerfile: from

**B · 78103879** — Spring Boot App in Docker container - SQL Server Integrated Security  
tags: `java`, `sql-server`, `spring`, `spring-boot`, `docker`

> I have a Spring Boot App (RESTful Service) that runs in a Docker Container and the Database Server is outside of the Docker Cluster, it´s on a special server cluster. In dev, the app works with "Integrated security" without a problem (because of my account), but in a docker container, there is no Kerberos Ticket availa

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 3 title token(s).*

**Your label:** `____________`

---

### 6. `78088430::78090396` — development

*Pinned to development: quoted in the rubric's borderline worked example, with its decision stated.*

**A · 78088430** — Dockerized Wordpress environment has load issues and service disruption  
tags: `wordpress`, `docker`, `docker-compose`

> exceptionally fast but still ok, but if you just open multiple tabs (~10) and hit reload the message "error establishing a database connection” pops up, even if containers don't crash and keep running. then it just takes a few seconds to co

**B · 78090396** — Wordpress Web UI dosen't load in browser  
tags: `wordpress`, `docker`, `docker-compose`

> When I deploy the docker compose configuration that I wrote the Phpmyadmin starts, but my the Wordpress web UI dosen't work. version: '3.1' services: wordpress: image: wordpress:latest restart: always ports: - 8000:80 environment: WORDPRESS_DB_HOST=db: 3306 WORDPRESS_DB_USER: wordpress WORDPRESS_DB_PASSWORD: wordpress 

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 7. `78092816::78098380` — development

**A · 78092816** — I am using docker-compose.yml to generate a docker container and initial schemas. Everything loads fine, but the initial table is nowhere to be found  
tags: `database`, `docker`, `docker-compose`, `dockerfile`, `docker-container`

> timeout: 45s interval: 10s retries: 10 restart: always environment: - postgres_user=root - postgres_password=password - postgres_db=mydatabasename_db - app_db_user=appuser - app_db_pass=appass - app_db_name=appname volumes: - ./init-schema.

**B · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 8. `78092816::78102512` — development

**A · 78092816** — I am using docker-compose.yml to generate a docker container and initial schemas. Everything loads fine, but the initial table is nowhere to be found  
tags: `database`, `docker`, `docker-compose`, `dockerfile`, `docker-container`

> timeout: 45s interval: 10s retries: 10 restart: always environment: - postgres_user=root - postgres_password=password - postgres_db=mydatabasename_db - app_db_user=appuser - app_db_pass=appass - app_db_name=appname volumes: - ./init-schema.

**B · 78102512** — docker: Error response from daemon: Duplicate mount point:: Mounting multiple docker volumes on same docker container having same target?  
tags: `docker`, `docker-compose`, `dockerfile`

> error message docker: error response from daemon: duplicate mount point: /rootdir1. i have gone through 1 . however, the problem is different. i am trying to mount multiple docker volume in same target location inside same docker container.

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 9. `78095654::78098380` — holdout

**A · 78095654** — Docker single build artifact for multiple images  
tags: `docker`, `docker-compose`, `dockerfile`

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

**B · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 10. `78095654::78102512` — development

**A · 78095654** — Docker single build artifact for multiple images  
tags: `docker`, `docker-compose`, `dockerfile`

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

**B · 78102512** — docker: Error response from daemon: Duplicate mount point:: Mounting multiple docker volumes on same docker container having same target?  
tags: `docker`, `docker-compose`, `dockerfile`

> error message docker: error response from daemon: duplicate mount point: /rootdir1. i have gone through 1 . however, the problem is different. i am trying to mount multiple docker volume in same target location inside same docker container.

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 11. `78095654::78103425` — development

**A · 78095654** — Docker single build artifact for multiple images  
tags: `docker`, `docker-compose`, `dockerfile`

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

**B · 78103425** — Using a single connectionstring for local and in docker (Database Access)  
tags: `docker`, `docker-compose`, `dockerfile`

> error detail=true" }, docker-compose.yaml version: '3.4' services: example-api: image: ${docker_registry-}api container_name: example-api restart: always build: context: . dockerfile: src/api/dockerfile depends_on: - postgres-db postgres-db

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 12. `78096175::78097071` — development

*Pinned to development: quoted in the rubric's abstention worked example, with its decision stated.*

**A · 78096175** — My postgresql database doesn't persist between docker runs  
tags: `django`, `postgresql`, `docker`, `docker-compose`

> I am learning docker and postgresql and I have problem with persisting data between the re-runs of the app. My docker-compose.yml: version: '3.7' services: web: build: . command: python3 /code/manage.py runserver 0.0.0.0:8000 volumes: - .:/code ports: - 8000:8000 depends_on: - db db: image: postgres:15 volumes: - postg

**B · 78097071** — How can I set up a database through an npm package in a Docker container?  
tags: `postgresql`, `docker`, `npm`, `docker-compose`, `prisma`

> errors out when i build the project. dockerfile (project a) arg owner from node:20-buster-slim env node_env 'development' env owner "username" run apt-get update && apt-get install libssl-dev ca-certificates -y # create app directory workdi

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 13. `78096355::78097579` — development

**A · 78096355** — why spring boot schedule logs not showing in docker.?  
tags: `java`, `spring-boot`, `docker`

> error. not only for scheduled tasks, its not working for commandlinerunner functions as well. here is my application properties file logging.level.com.priyan.algoservice=info java 21 spring boot 3.2.3 docker version 25.0.3 is there anything

**B · 78097579** — Spring Boot Application doesn't expose the port in Docker  
tags: `java`, `spring-boot`, `docker`, `port`

> failed to connect to 127.0.0.1 port 8090 after 0 ms: connection refused i run the container via docker run -it javaproj . here's the application.properties: server.port=8090 spring.mvc.static-path-pattern=/static/** and the dockerfile: from

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 14. `78096355::78103879` — holdout

**A · 78096355** — why spring boot schedule logs not showing in docker.?  
tags: `java`, `spring-boot`, `docker`

> error. not only for scheduled tasks, its not working for commandlinerunner functions as well. here is my application properties file logging.level.com.priyan.algoservice=info java 21 spring boot 3.2.3 docker version 25.0.3 is there anything

**B · 78103879** — Spring Boot App in Docker container - SQL Server Integrated Security  
tags: `java`, `sql-server`, `spring`, `spring-boot`, `docker`

> I have a Spring Boot App (RESTful Service) that runs in a Docker Container and the Database Server is outside of the Docker Cluster, it´s on a special server cluster. In dev, the app works with "Integrated security" without a problem (because of my account), but in a docker container, there is no Kerberos Ticket availa

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 15. `78098380::78102512` — holdout

**A · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

**B · 78102512** — docker: Error response from daemon: Duplicate mount point:: Mounting multiple docker volumes on same docker container having same target?  
tags: `docker`, `docker-compose`, `dockerfile`

> error message docker: error response from daemon: duplicate mount point: /rootdir1. i have gone through 1 . however, the problem is different. i am trying to mount multiple docker volume in same target location inside same docker container.

*Surfaced because: shares 2 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 16. `78086639::78092806` — development

**A · 78086639** — How to get a Windows Docker Container to auto start on login with Docker Desktop?  
tags: `docker`, `docker-desktop`

> Docker Desktop (on Windows) has an option to auto-start at login, which causes the Docker Desktop app to start on login. Is there a way to set a container to auto-start on login as well? For example, I am running the conduktor-console container, which provides a web interface for managing Kafka brokers. Currently, I ha

**B · 78092806** — Unexpected WSL Error on Docker Desktop with Hyper-V on Windows 11  
tags: `docker`, `windows-subsystem-for-linux`, `hyper-v`, `docker-desktop`, `windows-11`

> error". the error message suggests that it might be related to access rights issues, especially after waking the computer or when it's not connected to the domain/active directory. the recommended steps include shutting down wsl using wsl -

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 3 title token(s).*

**Your label:** `____________`

---

### 17. `78091723::78097184` — holdout

**A · 78091723** — invalid reference format on building docker image on github actions  
tags: `docker`, `github`

> error on adding tag on my docker file /usr/bin/docker buildx build --iidfile /tmp/docker-build-push-snaljd/iidfile --tag ***/image-micro-service:$(date +'%y-%m-%d%h-%m-%s') --metadata-file /tmp/docker-build-push-snaljd/metadata-file . error

**B · 78097184** — Can't pass env variables from GitHub Actions to Docker container  
tags: `docker`, `github`, `github-actions`

> I'm trying to pass variables in GitHub: I have the following step in workflow: - name: SSH into VPS and deploy uses: appleboy/ssh-action@master with: host: ${{ secrets.VPSHOST }} username: ${{ secrets.USERNAME }} key: ${{ secrets.SSH_KEY }} script: | export BLOG_POSTGRES_DB=${{ env.BLOG_POSTGRES_DB }} export BLOG_POSTG

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 3 title token(s).*

**Your label:** `____________`

---

### 18. `78097216::78103879` — holdout

**A · 78097216** — Postman Requests From Host Machine Are Not Able to Reach Tomcat Server Running On Docker Container  
tags: `java`, `docker`, `rest`, `servlets`, `containers`

> error. i tried removing the first stage of building the .war file in the container itself by copying the .war file generated in local to the webapps folder of the tomcat container. and surprisingly that time when i started the docker contai

**B · 78103879** — Spring Boot App in Docker container - SQL Server Integrated Security  
tags: `java`, `sql-server`, `spring`, `spring-boot`, `docker`

> I have a Spring Boot App (RESTful Service) that runs in a Docker Container and the Database Server is outside of the Docker Cluster, it´s on a special server cluster. In dev, the app works with "Integrated security" without a problem (because of my account), but in a docker container, there is no Kerberos Ticket availa

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 3 title token(s).*

**Your label:** `____________`

---

### 19. `78086323::78089075` — holdout

**A · 78086323** — Getting ETIMEDOUT while running Telegraf bot in docker container with network mode host  
tags: `node.js`, `docker`, `docker-network`, `telegraf`

> error instantly: fetcherror: request to https://api.telegram.org/bot6411340281:[redacted]/setmycommands failed, reason: at clientrequest.<anonymous> (/usr/src/app/node_modules/node-fetch/lib/index.js:1501:11) at clientrequest.emit (node:eve

**B · 78089075** — Can not connect with click-house running inside docker with nodejs  
tags: `node.js`, `docker`, `clickhouse`

> error. same is true for port 9000 as well. i am using host network in docker, so i should be able to connect this interface from my browser. same is happening for nodejs as well const { clickhouse } = require("clickhouse"); const clickhouse

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 20. `78086323::78097216` — development

**A · 78086323** — Getting ETIMEDOUT while running Telegraf bot in docker container with network mode host  
tags: `node.js`, `docker`, `docker-network`, `telegraf`

> error instantly: fetcherror: request to https://api.telegram.org/bot6411340281:[redacted]/setmycommands failed, reason: at clientrequest.<anonymous> (/usr/src/app/node_modules/node-fetch/lib/index.js:1501:11) at clientrequest.emit (node:eve

**B · 78097216** — Postman Requests From Host Machine Are Not Able to Reach Tomcat Server Running On Docker Container  
tags: `java`, `docker`, `rest`, `servlets`, `containers`

> error. i tried removing the first stage of building the .war file in the container itself by copying the .war file generated in local to the webapps folder of the tomcat container. and surprisingly that time when i started the docker contai

*Surfaced because: shares 4 title token(s).*

**Your label:** `____________`

---

### 21. `78086387::78087887` — development

**A · 78086387** — Troubles with postgres while building docker container  
tags: `django`, `linux`, `postgresql`, `docker`, `devops`

> error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/django/core/management/co

**B · 78087887** — QStandardPaths: runtime directory '/tmp' is not owned by UID 1000, but a directory permissions 0777 owned by UID 0 GID 0 in docker container  
tags: `linux`, `docker`, `permissions`

> error appeared when i installed wkhtmltopdf in my container. here is part of my dockerfile env xdg_runtime_dir=/tmp run python3.9 -m venv /py && \ ... apk add wkhtmltopdf && \ ... adduser --disabled-password --no-create-home ozangue && \ ..

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 23. `78086387::78097071` — holdout

**A · 78086387** — Troubles with postgres while building docker container  
tags: `django`, `linux`, `postgresql`, `docker`, `devops`

> error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/django/core/management/co

**B · 78097071** — How can I set up a database through an npm package in a Docker container?  
tags: `postgresql`, `docker`, `npm`, `docker-compose`, `prisma`

> errors out when i build the project. dockerfile (project a) arg owner from node:20-buster-slim env node_env 'development' env owner "username" run apt-get update && apt-get install libssl-dev ca-certificates -y # create app directory workdi

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 25. `78088481::78089563` — holdout

**A · 78088481** — Docker Compose MongoDB connection  
tags: `node.js`, `mongodb`, `docker`, `nginx`, `docker-compose`

> error that i get is: mongooseserverselectionerror: connect econnrefused 172.28.0.2:27017

**B · 78089563** — Error when running spark job using bitnami docker compose on Windows  
tags: `windows`, `docker`, `apache-spark`, `docker-compose`, `bitnami`

> exception is that i have added mapping for port 7077, as i need to submit job using that port. then i create simplest possible job with pyspark, submit it, and worker exits with exit code 1, master spawn workers in an endless loop. when i g

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 27. `78088481::78096903` — holdout

**A · 78088481** — Docker Compose MongoDB connection  
tags: `node.js`, `mongodb`, `docker`, `nginx`, `docker-compose`

> error that i get is: mongooseserverselectionerror: connect econnrefused 172.28.0.2:27017

**B · 78096903** — docker compose file, set keys from environment  
tags: `docker`, `docker-compose`

> I'm trying to use environment variables in my docker compose file, with docker stack. When I to use an environment variable like this, it works: services: service_test01: networks: - ${network} # more options here... networks: some_network: driver: overlay attachable: true However, if I try to use ${network} instead of

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 29. `78088692::78098380` — holdout

**A · 78088692** — strange behavior when getting env var in container  
tags: `django`, `docker`, `environment-variables`, `python-poetry`

> I need to get an env var from an docker container. This build is triggered with a docker compose file and I passed also the env variables with env_file . When I login to the container with docker exec -it conatinerName bash I can echo the variable and get correct output. Even when I trigger docker exec -it containerNam

**B · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 31. `78089113::78090158` — holdout

**A · 78089113** — Docker image from customized Grafana source code  
tags: `docker`, `docker-compose`, `dockerfile`, `grafana`

> error to build the image. but, when i comment out the the below code the dashboard is fine. run if [[ "$bingo" = "true" ]]; then \ go install github.com/bwplotka/bingo@latest && \ bingo get -v; \ fi my questions: what does this code do? the

**B · 78090158** — How to create a new image from existing docker image?  
tags: `docker`, `dockerfile`

> I have a docker file that has 3rd party application which downloads models from internet when build the docker image. Docker file: FROM my-third-party-address # add arguments # run commands ENTRYPOINT["/run-application.sh"] When I build and run this dockerfile, it downloads models and puts the image directory. I execut

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 33. `78089113::78092816` — development

**A · 78089113** — Docker image from customized Grafana source code  
tags: `docker`, `docker-compose`, `dockerfile`, `grafana`

> error to build the image. but, when i comment out the the below code the dashboard is fine. run if [[ "$bingo" = "true" ]]; then \ go install github.com/bwplotka/bingo@latest && \ bingo get -v; \ fi my questions: what does this code do? the

**B · 78092816** — I am using docker-compose.yml to generate a docker container and initial schemas. Everything loads fine, but the initial table is nowhere to be found  
tags: `database`, `docker`, `docker-compose`, `dockerfile`, `docker-container`

> timeout: 45s interval: 10s retries: 10 restart: always environment: - postgres_user=root - postgres_password=password - postgres_db=mydatabasename_db - app_db_user=appuser - app_db_pass=appass - app_db_name=appname volumes: - ./init-schema.

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 35. `78089113::78095654` — holdout

**A · 78089113** — Docker image from customized Grafana source code  
tags: `docker`, `docker-compose`, `dockerfile`, `grafana`

> error to build the image. but, when i comment out the the below code the dashboard is fine. run if [[ "$bingo" = "true" ]]; then \ go install github.com/bwplotka/bingo@latest && \ bingo get -v; \ fi my questions: what does this code do? the

**B · 78095654** — Docker single build artifact for multiple images  
tags: `docker`, `docker-compose`, `dockerfile`

> I have two .NET projects which depend on the same DLL. Currently, this DLL is building for each of the projects. Is there a way to build it once and share it among the Dockerfiles?

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 37. `78089113::78102512` — development

**A · 78089113** — Docker image from customized Grafana source code  
tags: `docker`, `docker-compose`, `dockerfile`, `grafana`

> error to build the image. but, when i comment out the the below code the dashboard is fine. run if [[ "$bingo" = "true" ]]; then \ go install github.com/bwplotka/bingo@latest && \ bingo get -v; \ fi my questions: what does this code do? the

**B · 78102512** — docker: Error response from daemon: Duplicate mount point:: Mounting multiple docker volumes on same docker container having same target?  
tags: `docker`, `docker-compose`, `dockerfile`

> error message docker: error response from daemon: duplicate mount point: /rootdir1. i have gone through 1 . however, the problem is different. i am trying to mount multiple docker volume in same target location inside same docker container.

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 39. `78089171::78098380` — development

**A · 78089171** — In the nextjs project environment variable in k8s is undefined  
tags: `kubernetes`, `next.js`, `dockerfile`, `environment-variables`

> not found") } ... } async function fetchdata() { const apitest = process.env['next_public_bff_orm_status'] if (!apitest) { console.log("api teste sem valor") } ... } dockerfile: from node:lts as dependencies workdir /front copy package.json

**B · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 41. `78089563::78096903` — development

**A · 78089563** — Error when running spark job using bitnami docker compose on Windows  
tags: `windows`, `docker`, `apache-spark`, `docker-compose`, `bitnami`

> exception is that i have added mapping for port 7077, as i need to submit job using that port. then i create simplest possible job with pyspark, submit it, and worker exits with exit code 1, master spawn workers in an endless loop. when i g

**B · 78096903** — docker compose file, set keys from environment  
tags: `docker`, `docker-compose`

> I'm trying to use environment variables in my docker compose file, with docker stack. When I to use an environment variable like this, it works: services: service_test01: networks: - ${network} # more options here... networks: some_network: driver: overlay attachable: true However, if I try to use ${network} instead of

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 43. `78090158::78093369` — holdout

**A · 78090158** — How to create a new image from existing docker image?  
tags: `docker`, `dockerfile`

> I have a docker file that has 3rd party application which downloads models from internet when build the docker image. Docker file: FROM my-third-party-address # add arguments # run commands ENTRYPOINT["/run-application.sh"] When I build and run this dockerfile, it downloads models and puts the image directory. I execut

**B · 78093369** — installing psycopg in alpine docker image  
tags: `docker`, `dockerfile`, `psycopg2`, `docker-image`

> error occurs when the image is loaded: error: failed to solve: process "/bin/sh -c pip install -r ./requirements/local.txt" did not complete successfully: exit code: 1 i tried to install various dependencies in my dockerfile. but always the

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 45. `78090939::78097579` — holdout

**A · 78090939** — Springboot application, deploy in Render fail  
tags: `java`, `spring-boot`, `docker`, `deployment`

> error: error: invalid or corrupt jarfile agilstratapi.jar i don't know how to solve it. something curious that may have something to do with it, when i upload the changes to the remote repository, it gives me this warning: warning: file out

**B · 78097579** — Spring Boot Application doesn't expose the port in Docker  
tags: `java`, `spring-boot`, `docker`, `port`

> failed to connect to 127.0.0.1 port 8090 after 0 ms: connection refused i run the container via docker run -it javaproj . here's the application.properties: server.port=8090 spring.mvc.static-path-pattern=/static/** and the dockerfile: from

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 47. `78091032::78092816` — development

**A · 78091032** — How to use Docker compose in c program?  
tags: `c`, `docker`, `docker-compose`, `dockerfile`

> I want to isolate my development environment to create a project in C. But I don't know how to use Docker with C. I'm getting confused about running the program and I would like someone to help me. Take for example a "hello world" with an input. basic as a program. How can I make a docker compose and how to run it. And

**B · 78092816** — I am using docker-compose.yml to generate a docker container and initial schemas. Everything loads fine, but the initial table is nowhere to be found  
tags: `database`, `docker`, `docker-compose`, `dockerfile`, `docker-container`

> timeout: 45s interval: 10s retries: 10 restart: always environment: - postgres_user=root - postgres_password=password - postgres_db=mydatabasename_db - app_db_user=appuser - app_db_pass=appass - app_db_name=appname volumes: - ./init-schema.

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 49. `78091032::78096903` — development

**A · 78091032** — How to use Docker compose in c program?  
tags: `c`, `docker`, `docker-compose`, `dockerfile`

> I want to isolate my development environment to create a project in C. But I don't know how to use Docker with C. I'm getting confused about running the program and I would like someone to help me. Take for example a "hello world" with an input. basic as a program. How can I make a docker compose and how to run it. And

**B · 78096903** — docker compose file, set keys from environment  
tags: `docker`, `docker-compose`

> I'm trying to use environment variables in my docker compose file, with docker stack. When I to use an environment variable like this, it works: services: service_test01: networks: - ${network} # more options here... networks: some_network: driver: overlay attachable: true However, if I try to use ${network} instead of

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 51. `78091032::78102512` — holdout

**A · 78091032** — How to use Docker compose in c program?  
tags: `c`, `docker`, `docker-compose`, `dockerfile`

> I want to isolate my development environment to create a project in C. But I don't know how to use Docker with C. I'm getting confused about running the program and I would like someone to help me. Take for example a "hello world" with an input. basic as a program. How can I make a docker compose and how to run it. And

**B · 78102512** — docker: Error response from daemon: Duplicate mount point:: Mounting multiple docker volumes on same docker container having same target?  
tags: `docker`, `docker-compose`, `dockerfile`

> error message docker: error response from daemon: duplicate mount point: /rootdir1. i have gone through 1 . however, the problem is different. i am trying to mount multiple docker volume in same target location inside same docker container.

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 53. `78091354::78092816` — holdout

**A · 78091354** — Nest.js CLI not found in Docker multi-stage build  
tags: `docker`, `dockerfile`, `nest`

> error message i'm getting is: sh: 1: nest: not found it seems that the nest.js cli is not available in the path during the production build, even though it's installed as a dev dependency in my package.json. #11 [prod 1/2] run ls /app/node_

**B · 78092816** — I am using docker-compose.yml to generate a docker container and initial schemas. Everything loads fine, but the initial table is nowhere to be found  
tags: `database`, `docker`, `docker-compose`, `dockerfile`, `docker-container`

> timeout: 45s interval: 10s retries: 10 restart: always environment: - postgres_user=root - postgres_password=password - postgres_db=mydatabasename_db - app_db_user=appuser - app_db_pass=appass - app_db_name=appname volumes: - ./init-schema.

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 55. `78091354::78098380` — development

**A · 78091354** — Nest.js CLI not found in Docker multi-stage build  
tags: `docker`, `dockerfile`, `nest`

> error message i'm getting is: sh: 1: nest: not found it seems that the nest.js cli is not available in the path during the production build, even though it's installed as a dev dependency in my package.json. #11 [prod 1/2] run ls /app/node_

**B · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---

### 57. `78092648::78102252` — development

**A · 78092648** — How to Make Batch Jobs Logs Available When the Jobs Run Inside Ephemeral Docker Containers?  
tags: `python`, `docker`, `google-cloud-platform`, `logging`, `cron`

> Context So, basically I am running a cron job (python ETL script) via a docker container. That means, every day at 12.30 am my cron job runs docker run $IMAGE In the Dockerfile I have the script like # Run the script at container boot time. CMD ["./run_manager.sh"] This is how the run_manager.sh looks like. python3 mai

**B · 78102252** — ModuleNotFoundError message when run gcp dataflow pipeline with python  
tags: `python`, `docker`, `google-cloud-platform`, `google-cloud-dataflow`, `apache-beam`

> error is the same, please someone can help me? i understand that the workers are using de default beam sdk, is correct that? how i can fix it?

*Surfaced because: shares 2 site tag(s) beyond the query tag.*

**Your label:** `____________`

---

### 59. `78092816::78095639` — development

**A · 78092816** — I am using docker-compose.yml to generate a docker container and initial schemas. Everything loads fine, but the initial table is nowhere to be found  
tags: `database`, `docker`, `docker-compose`, `dockerfile`, `docker-container`

> timeout: 45s interval: 10s retries: 10 restart: always environment: - postgres_user=root - postgres_password=password - postgres_db=mydatabasename_db - app_db_user=appuser - app_db_pass=appass - app_db_name=appname volumes: - ./init-schema.

**B · 78095639** — Angular client application failing to resolve address for backend service from docker container  
tags: `angular`, `docker`, `docker-compose`

> error can someone help with this why the request is failing, i can across some solution that say to use ip address of backend service in the http url i don't think that's good choice

*Surfaced because: shares 1 site tag(s) beyond the query tag; shares 2 title token(s).*

**Your label:** `____________`

---
