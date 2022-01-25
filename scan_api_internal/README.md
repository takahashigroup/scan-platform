# SCAN API for Internal



## For local development

### Requirements

* conda
* [poetry](https://github.com/python-poetry/poetry)

### Setup environment

```shell
# init conda env
$ conda env create -f env.yaml
$ source activate scan-env

# install pip deps with poetry
$ poetry install

# start api app
$ uuvicorn app:api --reload

# or start with gunicorn
$ gunicorn app:api -w 4 -k uvicorn.workers.UvicornWorker

```

## Start with docker

```shell
$ docker-compose -f docker-compose-local.yml up -d --build
```

## Shut down the containers

```shell
$ docker-compose -f docker-compose-local.yml down --rmi all
```



## Data update scripts

### eq -> structure

```shell
# for dockerized db
$ ./update-eq-structures.sh

# for local db
$ python python-scripts/update-eq-structures_mp.py
```

### edge -> structure

```shell
# for dockerized db
$ ./update-edge-structures.sh

# for local db
$ python python-scripts/update-edge-structures_mp.py
```

### map -> graph

```shell
# for dockerized db
$ ./update-map-graphs.sh

# for local db
$ python python-scripts/update-map-graphs.py
```

### for all

```shell
$ ./update-all.sh
`