# Problem-family review batch V1 — blind reference labels

**Mission 1.25 §7. Generated, never hand-picked.** Regenerate with
`python infrastructure/scripts/render_family_batch.py`.

- relation: **`SAME_PROBLEM_FAMILY`** — *not* the Mission 1.24 exact relation
- rubric: `problem-family-rubric@1.0.0`
- candidate ordering: `docker-problem-family-candidates@1.0.0`
- batch selection: `family-review-batch-selection@1.0.0`
- corpus: 89 Docker `community_question` observations, unchanged since
  Mission 1.20. 731 of 3916 possible pairs qualify as candidates
- pairs: **20** — 10 development, 10 holdout

> **No model has seen any of these pairs and no prediction exists.** The labels
> written here are the reference set, and the classifier is scored against them.
> Record who or what produced them: `human_ground_truth` stays NOT_ESTABLISHED
> unless a person actually judges.

## The question, and it is not Mission 1.24's question

Mission 1.24 asked whether the working FIX for one would tell you what to change
for the other. That needed Docker expertise, and it is a different relation which
stays intact and unweakened.

**This one is answerable without knowing any fix.**

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

For each pair write `SAME_FAMILY`, `DIFFERENT_FAMILY` or `UNCERTAIN` on its
**Your label** line.

- **SAME_FAMILY** — substantially the same user problem or blocked goal. One
  product, tool, documentation change or workflow could reasonably help both
  people, even though their causes and fixes may differ entirely.
- **DIFFERENT_FAMILY** — different blocked goals. Helping both would take two
  unrelated interventions.
- **UNCERTAIN** — the text does not establish what one or both people were trying
  to do. A real answer, not a skipped one.

**You are not asked to diagnose anything.** If you cannot tell what either person
was trying to do, that is `UNCERTAIN` and it is useful.

## None of this makes two observations one family

- the same tool, runtime or platform. Every observation here is a Docker question, so a relation satisfied by that would return SAME for everything
- the same site tags, however specific
- the same language, framework or base image
- the same wrapper or harness diagnostic, however long the shared string. Mission 1.20's three questions share 106 characters of exact runc output and are three unrelated blocked goals
- the same generic error class -- permission denied, connection refused, exit code 1, HTTP 500, a bare ValueError, 'the build failed'
- the same broad category of component. Two database connectivity failures are not one family merely because both involve databases; MongoDB unreachable from a container and SQL Server refusing an integrated-security login are different blocked goals with different interventions
- the same lifecycle phase alone. 'Both happen at build time' is a coordinate, not a goal

## Why four pairs are already marked development

The rubric quotes them and states their answers, so the classifier is shown them
in its own instructions. Getting them right shows it can read its rubric and is
not evidence of generalisation. **Please label them anyway** — where your answer
differs from the rubric's stated one, that disagreement is the most useful thing
in this batch.

## The split, and why it leans to holdout

Each pair is marked development or holdout, computed from its id before any label
existed, with **60% to holdout** rather than the
half Mission 1.24 used. That mission planned prompt development and this one does
not: the family prompt is written once and frozen, so a large development set buys
nothing while a large holdout buys positive coverage in the split that decides.
Mission 1.24's single positive fell in development and left its holdout unable to
distinguish caution from correctness.

## The acceptance criterion, frozen before any prediction

> Frozen before any family prediction existed. The classifier passes only if ALL of the following hold on the scored split: at least 8 labelled pairs; at least 2 pairs the reference calls SAME_FAMILY, IN THAT SPLIT rather than anywhere in the reference set; ZERO false SAME_PROBLEM_FAMILY, meaning a pair the reference called DIFFERENT or UNCERTAIN that the model called SAME; and at least ONE true SAME_PROBLEM_FAMILY, meaning a pair the reference called SAME that the model also called SAME.

THE LAST CLAUSE IS THE ONE MISSION 1.24 LACKED. Without it a classifier that answers DIFFERENT to everything, or ABSTAIN to everything, records zero false positives and passes -- which is exactly what happened, and why that evaluation established nothing. Requiring a demonstrated positive makes both constant classifiers fail by construction.

Abstention is still never counted as an error, because the alternative to an abstention is a guess. But abstaining on EVERY positive now fails the true-SAME clause, which is the honest way to price caution: free when it is caution, and not free when it is refusal to ever commit.

No accuracy, precision or recall figure is a pass condition. A proportion over a few dozen pairs has an interval wider than any difference it could show, and quoting one would make a small experiment look calibrated.

## Scope, which every downstream statement inherits

> Scope: the 731 pairs surfaced by docker-problem-family-candidates@1.0.0 out of 3916 possible pairs over 89 observations. A pair this generator did not surface is UNCONSIDERED, not different. No statement derived from this set describes all repeated problems in the corpus, and none may be worded as though it did.

---

### 1. `78091723::78097184` — holdout

**A · 78091723** — invalid reference format on building docker image on github actions  
tags: `docker`, `github`

> error on adding tag on my docker file /usr/bin/docker buildx build --iidfile /tmp/docker-build-push-snaljd/iidfile --tag ***/image-micro-service:$(date +'%y-%m-%d%h-%m-%s') --metadata-file /tmp/docker-build-push-snaljd/metadata-file . error

**B · 78097184** — Can't pass env variables from GitHub Actions to Docker container  
tags: `docker`, `github`, `github-actions`

> I'm trying to pass variables in GitHub: I have the following step in workflow: - name: SSH into VPS and deploy uses: appleboy/ssh-action@master with: host: ${{ secrets.VPSHOST }} username: ${{ secrets.USERNAME }} key: ${{ secrets.SSH_KEY }} script: | export BLOG_POSTGRES_DB=${{ env.BLOG_POSTGRES_DB }} export BLOG_POSTG

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'github' (rarity 3.8); shares 3 title token(s).*

**Your label:** `____________`

---

### 2. `78086639::78092806` — development

**A · 78086639** — How to get a Windows Docker Container to auto start on login with Docker Desktop?  
tags: `docker`, `docker-desktop`

> Docker Desktop (on Windows) has an option to auto-start at login, which causes the Docker Desktop app to start on login. Is there a way to set a container to auto-start on login as well? For example, I am running the conduktor-console container, which provides a web interface for managing Kafka brokers. Currently, I ha

**B · 78092806** — Unexpected WSL Error on Docker Desktop with Hyper-V on Windows 11  
tags: `docker`, `windows-subsystem-for-linux`, `hyper-v`, `docker-desktop`, `windows-11`

> error". the error message suggests that it might be related to access rights issues, especially after waking the computer or when it's not connected to the domain/active directory. the recommended steps include shutting down wsl using wsl -

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'docker-desktop' (rarity 3.4); shares 3 title token(s).*

**Your label:** `____________`

---

### 3. `78097579::78103879` — development

**A · 78097579** — Spring Boot Application doesn't expose the port in Docker  
tags: `java`, `spring-boot`, `docker`, `port`

> failed to connect to 127.0.0.1 port 8090 after 0 ms: connection refused i run the container via docker run -it javaproj . here's the application.properties: server.port=8090 spring.mvc.static-path-pattern=/static/** and the dockerfile: from

**B · 78103879** — Spring Boot App in Docker container - SQL Server Integrated Security  
tags: `java`, `sql-server`, `spring`, `spring-boot`, `docker`

> I have a Spring Boot App (RESTful Service) that runs in a Docker Container and the Database Server is outside of the Docker Cluster, it´s on a special server cluster. In dev, the app works with "Integrated security" without a problem (because of my account), but in a docker container, there is no Kerberos Ticket availa

*Surfaced because: shares 2 site tag(s) beyond the query tag, rarest 'spring-boot' (rarity 3.1); shares 3 title token(s).*

**Your label:** `____________`

---

### 4. `78088430::78090396` — development

**A · 78088430** — Dockerized Wordpress environment has load issues and service disruption  
tags: `wordpress`, `docker`, `docker-compose`

> exceptionally fast but still ok, but if you just open multiple tabs (~10) and hit reload the message "error establishing a database connection” pops up, even if containers don't crash and keep running. then it just takes a few seconds to co

**B · 78090396** — Wordpress Web UI dosen't load in browser  
tags: `wordpress`, `docker`, `docker-compose`

> When I deploy the docker compose configuration that I wrote the Phpmyadmin starts, but my the Wordpress web UI dosen't work. version: '3.1' services: wordpress: image: wordpress:latest restart: always ports: - 8000:80 environment: WORDPRESS_DB_HOST=db: 3306 WORDPRESS_DB_USER: wordpress WORDPRESS_DB_PASSWORD: wordpress 

*Surfaced because: shares 2 site tag(s) beyond the query tag, rarest 'wordpress' (rarity 3.8); shares 2 title token(s).*

**Your label:** `____________`

---

### 5. `78095639::78105296` — holdout

**A · 78095639** — Angular client application failing to resolve address for backend service from docker container  
tags: `angular`, `docker`, `docker-compose`

> error can someone help with this why the request is failing, i can across some solution that say to use ip address of backend service in the http url i don't think that's good choice

**B · 78105296** — Deploying an Angular Application to OpenShift via GitLab  
tags: `angular`, `docker`, `deployment`, `gitlab`, `openshift`

> My company utilizes OpenShift for application deployment. As per guidance from my senior, the recommended approach involves utilizing GitLab as an intermediate step. The process entails creating and pushing the container to a GitLab repository, and then using that repository (containing the container) to deploy the app

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'angular' (rarity 3.8); shares 2 title token(s).*

**Your label:** `____________`

---

### 6. `78097216::78103879` — holdout

**A · 78097216** — Postman Requests From Host Machine Are Not Able to Reach Tomcat Server Running On Docker Container  
tags: `java`, `docker`, `rest`, `servlets`, `containers`

> error. i tried removing the first stage of building the .war file in the container itself by copying the .war file generated in local to the webapps folder of the tomcat container. and surprisingly that time when i started the docker contai

**B · 78103879** — Spring Boot App in Docker container - SQL Server Integrated Security  
tags: `java`, `sql-server`, `spring`, `spring-boot`, `docker`

> I have a Spring Boot App (RESTful Service) that runs in a Docker Container and the Database Server is outside of the Docker Cluster, it´s on a special server cluster. In dev, the app works with "Integrated security" without a problem (because of my account), but in a docker container, there is no Kerberos Ticket availa

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'java' (rarity 2.7); shares 3 title token(s).*

**Your label:** `____________`

---

### 7. `78088692::78098380` — development

**A · 78088692** — strange behavior when getting env var in container  
tags: `django`, `docker`, `environment-variables`, `python-poetry`

> I need to get an env var from an docker container. This build is triggered with a docker compose file and I passed also the env variables with env_file . When I login to the container with docker exec -it conatinerName bash I can echo the variable and get correct output. Even when I trigger docker exec -it containerNam

**B · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'environment-variables' (rarity 3.4); shares 2 title token(s).*

**Your label:** `____________`

---

### 8. `78096486::78097886` — holdout

**A · 78096486** — How do I install the latest version of gcc(13.2.0) in a dev container with image suse/sle15:15.2?  
tags: `c++`, `docker`, `containers`, `suse`

> no such file or directory. /home/developer/workspace/rough # g++ hello.cpp hello.cpp:2:10: fatal error: filesystem: no such file or directory #include <filesystem> ^~~~~~~~~~~~ compilation terminated. when i check the gcc --version it says 

**B · 78097886** — How to install packages from an environment yaml into a micromamba docker base image?  
tags: `docker`, `containers`, `conda`, `micromamba`

> errors like this: (base) joshs-mbp:containers jolespin$ docker build -t jolespin/qiime2-amplicon:2024.2 -f dockerfile_qiime2-amplicon-2024.2 . [+] building 7.3s (13/14) docker:desktop-linux => [internal] load build definition from dockerfil

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'containers' (rarity 3.4); shares 2 title token(s).*

**Your label:** `____________`

---

### 9. `78096355::78097579` — holdout

**A · 78096355** — why spring boot schedule logs not showing in docker.?  
tags: `java`, `spring-boot`, `docker`

> error. not only for scheduled tasks, its not working for commandlinerunner functions as well. here is my application properties file logging.level.com.priyan.algoservice=info java 21 spring boot 3.2.3 docker version 25.0.3 is there anything

**B · 78097579** — Spring Boot Application doesn't expose the port in Docker  
tags: `java`, `spring-boot`, `docker`, `port`

> failed to connect to 127.0.0.1 port 8090 after 0 ms: connection refused i run the container via docker run -it javaproj . here's the application.properties: server.port=8090 spring.mvc.static-path-pattern=/static/** and the dockerfile: from

*Surfaced because: shares 2 site tag(s) beyond the query tag, rarest 'spring-boot' (rarity 3.1); shares 2 title token(s).*

**Your label:** `____________`

---

### 10. `78096355::78103879` — holdout

**A · 78096355** — why spring boot schedule logs not showing in docker.?  
tags: `java`, `spring-boot`, `docker`

> error. not only for scheduled tasks, its not working for commandlinerunner functions as well. here is my application properties file logging.level.com.priyan.algoservice=info java 21 spring boot 3.2.3 docker version 25.0.3 is there anything

**B · 78103879** — Spring Boot App in Docker container - SQL Server Integrated Security  
tags: `java`, `sql-server`, `spring`, `spring-boot`, `docker`

> I have a Spring Boot App (RESTful Service) that runs in a Docker Container and the Database Server is outside of the Docker Cluster, it´s on a special server cluster. In dev, the app works with "Integrated security" without a problem (because of my account), but in a docker container, there is no Kerberos Ticket availa

*Surfaced because: shares 2 site tag(s) beyond the query tag, rarest 'spring-boot' (rarity 3.1); shares 2 title token(s).*

**Your label:** `____________`

---

### 11. `78086323::78089075` — development

**A · 78086323** — Getting ETIMEDOUT while running Telegraf bot in docker container with network mode host  
tags: `node.js`, `docker`, `docker-network`, `telegraf`

> error instantly: fetcherror: request to https://api.telegram.org/bot6411340281:[redacted]/setmycommands failed, reason: at clientrequest.<anonymous> (/usr/src/app/node_modules/node-fetch/lib/index.js:1501:11) at clientrequest.emit (node:eve

**B · 78089075** — Can not connect with click-house running inside docker with nodejs  
tags: `node.js`, `docker`, `clickhouse`

> error. same is true for port 9000 as well. i am using host network in docker, so i should be able to connect this interface from my browser. same is happening for nodejs as well const { clickhouse } = require("clickhouse"); const clickhouse

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'node.js' (rarity 2.9); shares 2 title token(s).*

**Your label:** `____________`

---

### 12. `78086387::78087887` — development

**A · 78086387** — Troubles with postgres while building docker container  
tags: `django`, `linux`, `postgresql`, `docker`, `devops`

> error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/django/core/management/co

**B · 78087887** — QStandardPaths: runtime directory '/tmp' is not owned by UID 1000, but a directory permissions 0777 owned by UID 0 GID 0 in docker container  
tags: `linux`, `docker`, `permissions`

> error appeared when i installed wkhtmltopdf in my container. here is part of my dockerfile env xdg_runtime_dir=/tmp run python3.9 -m venv /py && \ ... apk add wkhtmltopdf && \ ... adduser --disabled-password --no-create-home ozangue && \ ..

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'linux' (rarity 2.9); shares 2 title token(s).*

**Your label:** `____________`

---

### 13. `78086387::78097071` — holdout

**A · 78086387** — Troubles with postgres while building docker container  
tags: `django`, `linux`, `postgresql`, `docker`, `devops`

> error occured during this operation. log basicly says that django cant connect to postgress db. > [9/9] run python manage.py makemigrations && python manage.py migrate: 3.377 /usr/local/lib/python3.12/site-packages/django/core/management/co

**B · 78097071** — How can I set up a database through an npm package in a Docker container?  
tags: `postgresql`, `docker`, `npm`, `docker-compose`, `prisma`

> errors out when i build the project. dockerfile (project a) arg owner from node:20-buster-slim env node_env 'development' env owner "username" run apt-get update && apt-get install libssl-dev ca-certificates -y # create app directory workdi

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'postgresql' (rarity 2.9); shares 2 title token(s).*

**Your label:** `____________`

---

### 14. `78089075::78089578` — holdout

**A · 78089075** — Can not connect with click-house running inside docker with nodejs  
tags: `node.js`, `docker`, `clickhouse`

> error. same is true for port 9000 as well. i am using host network in docker, so i should be able to connect this interface from my browser. same is happening for nodejs as well const { clickhouse } = require("clickhouse"); const clickhouse

**B · 78089578** — How to get .NET MAUI Android emulator connect to local docker node js server  
tags: `c#`, `node.js`, `.net`, `docker`, `maui`

> I'm using Visual Studio's .NET Maui QEMU android emulator, and want it to make an HTTP request to my Node JS backend that's running on docker. How would I get it them to connect? I've tried using localhost, the host machine's ip, etc, but I get a HTTP connection failure error

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'node.js' (rarity 2.9); shares 2 title token(s).*

**Your label:** `____________`

---

### 15. `78096175::78097071` — development

*Pinned to development: the rubric's abstention worked example, quoted by id with its decision stated.*

**A · 78096175** — My postgresql database doesn't persist between docker runs  
tags: `django`, `postgresql`, `docker`, `docker-compose`

> I am learning docker and postgresql and I have problem with persisting data between the re-runs of the app. My docker-compose.yml: version: '3.7' services: web: build: . command: python3 /code/manage.py runserver 0.0.0.0:8000 volumes: - .:/code ports: - 8000:8000 depends_on: - db db: image: postgres:15 volumes: - postg

**B · 78097071** — How can I set up a database through an npm package in a Docker container?  
tags: `postgresql`, `docker`, `npm`, `docker-compose`, `prisma`

> errors out when i build the project. dockerfile (project a) arg owner from node:20-buster-slim env node_env 'development' env owner "username" run apt-get update && apt-get install libssl-dev ca-certificates -y # create app directory workdi

*Surfaced because: shares 2 site tag(s) beyond the query tag, rarest 'postgresql' (rarity 2.9); shares 2 title token(s).*

**Your label:** `____________`

---

### 16. `78092648::78100915` — holdout

**A · 78092648** — How to Make Batch Jobs Logs Available When the Jobs Run Inside Ephemeral Docker Containers?  
tags: `python`, `docker`, `google-cloud-platform`, `logging`, `cron`

> Context So, basically I am running a cron job (python ETL script) via a docker container. That means, every day at 12.30 am my cron job runs docker run $IMAGE In the Dockerfile I have the script like # Run the script at container boot time. CMD ["./run_manager.sh"] This is how the run_manager.sh looks like. python3 mai

**B · 78100915** — Executing airflow tasks that are themselves in docker containers  
tags: `python`, `docker`, `airflow`, `docker-volume`

> cannot execute the bash script, why doesn't it fail? if the task can execute the bash script, why does it succeed in less than a second? here is the log from one of the 'successful' task runs: bdb1f78ac8d2 *** found local files: *** * /opt/

*Surfaced because: shares 1 site tag(s) beyond the query tag, rarest 'python' (rarity 2.1); shares 2 title token(s).*

**Your label:** `____________`

---

### 17. `78086323::78097216` — holdout

**A · 78086323** — Getting ETIMEDOUT while running Telegraf bot in docker container with network mode host  
tags: `node.js`, `docker`, `docker-network`, `telegraf`

> error instantly: fetcherror: request to https://api.telegram.org/bot6411340281:[redacted]/setmycommands failed, reason: at clientrequest.<anonymous> (/usr/src/app/node_modules/node-fetch/lib/index.js:1501:11) at clientrequest.emit (node:eve

**B · 78097216** — Postman Requests From Host Machine Are Not Able to Reach Tomcat Server Running On Docker Container  
tags: `java`, `docker`, `rest`, `servlets`, `containers`

> error. i tried removing the first stage of building the .war file in the container itself by copying the .war file generated in local to the webapps folder of the tomcat container. and surprisingly that time when i started the docker contai

*Surfaced because: shares 4 title token(s).*

**Your label:** `____________`

---

### 55. `78089171::78098380` — development

*Pinned to development: the rubric's qualifying worked example, quoted by id with its decision stated.*

**A · 78089171** — In the nextjs project environment variable in k8s is undefined  
tags: `kubernetes`, `next.js`, `dockerfile`, `environment-variables`

> not found") } ... } async function fetchdata() { const apitest = process.env['next_public_bff_orm_status'] if (!apitest) { console.log("api teste sem valor") } ... } dockerfile: from node:lts as dependencies workdir /front copy package.json

**B · 78098380** — Make docker env variables from an `.env` file available in build step (Dockerfile) & during run-time in container  
tags: `docker`, `docker-compose`, `dockerfile`, `environment-variables`

> error during the precompile task since the env variables are not available in the dockerfile (where we execute the precompile task). that's exactly the problem ;)

*Surfaced because: shares 2 site tag(s) beyond the query tag, rarest 'environment-variables' (rarity 3.4).*

**Your label:** `____________`

---

### 240. `78086542::78099680` — development

*Pinned to development: the rubric's non-qualifying worked example, quoted by id with its decision stated.*

**A · 78086542** — Docker compose/ failed to create task for container  
tags: `python`, `docker`, `pycharm`

> error: shop-backend-database | 2024-03-01 08:31:53.031 utc [1] log: database system is ready to accept connections error response from daemon: failed to create task for container: failed to create shim task: oci runtime create failed: runc 

**B · 78099680** — Unable to run uvicorn under gunicorn in a Docker container  
tags: `docker`, `fastapi`, `gunicorn`, `uvicorn`

> error: (.venv) bob /volumes/2tbwdb/code/uvitest [main] $ docker compose up -d [+] running 0/1 ⠹ container uvitest-uvitest-1 starting 0.2s error response from daemon: failed to create task for container: failed to create shim task: oci runti

*Surfaced because: shares 2 title token(s); shares a 104-character diagnostic fragment, which qualifies the pair and promotes it by nothing: a shared wrapper is not a shared goal.*

**Your label:** `____________`

---

### 731. `78093369::78105004` — development

*Pinned to development: the rubric's borderline worked example, quoted by id with its decision stated.*

**A · 78093369** — installing psycopg in alpine docker image  
tags: `docker`, `dockerfile`, `psycopg2`, `docker-image`

> error occurs when the image is loaded: error: failed to solve: process "/bin/sh -c pip install -r ./requirements/local.txt" did not complete successfully: exit code: 1 i tried to install various dependencies in my dockerfile. but always the

**B · 78105004** — Docker build fails because unable to install `libc-bin`  
tags: `ruby-on-rails`, `docker`, `kamal`

> error processing package libc-bin (--configure): 63.34 installed libc-bin package post-installation script subprocess returned error exit status 139 63.44 errors were encountered while processing: 63.44 libc-bin 63.54 e: sub-process /usr/bi

*Surfaced because: shares a 45-character diagnostic fragment, which qualifies the pair and promotes it by nothing: a shared wrapper is not a shared goal.*

**Your label:** `____________`

---
