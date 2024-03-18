# keiba-hacke

Horse Racing Forecast App

## Getting Started
### hobo パイプライン開発・実行
#### 大元の開発コンテナ起動・ログイン
* ここからパイプラインを実行することになる
    * pyproject.toml はこれを共通で利用する

```
# build & run container
$ cd app
$ docker build -t khdocker .
$ docker run -itd -v $(pwd):/opt/mnt -p 18888:8888 khdocker

# login container
$ docker ps -a | grep khdocker
$ docker exec -it XXX /bin/bash
```

#### Develop Vertex AI Pipelines

![vap drawio](https://github.com/nokoxxx1212/keiba-hacke/assets/13251279/ffd5bf76-b12a-4022-9fd2-45c8168e3899)

* ①Component Dockerfile 作成
    * pyproject.tomlも合わせて作成
* pyproject.toml 移動: `cp ../../../../pyproject.toml ./`
* ①Component Dockerfile 確認: `docker build -t khsampledocker .`
* ②Component Pythonスクリプト 作成
* ②Component Pythonスクリプト 確認: `docker run python3 sample.py --number 3`
    * または、コンテナを立ち上げて、VS Code の devcontainer （左下マーク→実行中のコンテナにアタッチ）でデバッグ。一旦ソースコードをマウントするようにする（ Dockerfile の COPY をコメントアウト + docker run のときにマウントするようにする）
* ③componentファイル作成
* コンテナ準備
    * `docker build -t gcr.io/your-project-id/khsampledocker .`
    * `gcloud auth configure-docker`
    * `docker push gcr.io/your-project-id/your-image-name`
* ④pipelineファイル作成
    * envファイルも合わせて作成
* ④pipelineファイル実行@大元のコンテナ: `python sample_pipeline.py`

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

* Set up CI (GitHub Actions)

```
Settings
-> Secrets and variables
-> Repository secrets
DOCKER_PASSWORD
DOCKER_USERNAME
```

## Deployment

[TODO]Add additional notes about how to deploy this on a live system


