# keiba-hacke

Horse Racing Forecast App

## Getting Started

* Set up a container

```
$ cd app
$ docker build -t khpythondocker .
$ docker run -itd -v $(pwd):/opt/mnt -p 18888:8888 khpythondocker
```

* Run Python

```
# login container
$ docker ps -a | grep khpythondocker
$ docker exec -it XXX /bin/bash

# (optional)VSCode devcontainer
左下マーク→実行中のコンテナにアタッチ

# run python
$ cd src
$ python sample.py 3
```

* Set up CI (GitHub Actions)

```
Settings
-> Secrets and variables
-> Repository secrets
DOCKER_PASSWORD
DOCKER_USERNAME
```

## Running the tests

* Execute linter, formatter

```
$ poetry run isort src tests
$ poetry run black src tests
$ poetry run flake8 src tests
```

* Execute tests

```
$ poetry install
$ poetry run pytest src tests
```

## Deployment

[TODO]Add additional notes about how to deploy this on a live system