# keiba-hacke

Horse Racing Forecast App

## Getting Started

* Set up a container

```
$ cd app
$ docker build -t khdocker .
$ docker run -itd -v $(pwd):/opt/mnt -p 18888:8888 khdocker
```

* Run Python

```
# login container
$ docker ps -a | grep khdocker
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

### develop Vertex AI Pipelines
大元の khdocker コンテナは立ち上がっている前提

![vap drawio](https://github.com/nokoxxx1212/keiba-hacke/assets/13251279/ffd5bf76-b12a-4022-9fd2-45c8168e3899)

* ①Dockerfile作成
    * pyproject.tomlも合わせて作成
* pyproject.toml移動: `cp ../../../../pyproject.toml ./`
* ①Dockerfile確認: `docker build -t khsampledocker .`
* ②pythonスクリプト作成
* ②pythonスクリプト確認: `docker run python3 sample.py --number 3`
* ③componentファイル作成
* コンテナ準備
    * `docker build -t gcr.io/your-project-id/khsampledocker .`
    * `gcloud auth configure-docker`
    * `docker push gcr.io/your-project-id/your-image-name`
* ④pipelineファイル作成
    * envファイルも合わせて作成
* ④pipelineファイル実行: `python sample_pipeline.py`

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
