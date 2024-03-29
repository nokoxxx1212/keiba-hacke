# keiba-hacke

Horse Racing Forecast App

## Getting Started
### 一馬入魂（ichiba）
#### 推論
* 事前準備
    * GCSバケット作成・データアップロード

```
gsutil cp -r pickle_data gs://${GCS_BUCKET}/ichiba/pickle_data
gsutil cp -r race_result_place gs://${GCS_BUCKET}/ichiba/race_result_place
gsutil cp -r train_data gs://${GCS_BUCKET}/ichiba/train_data
```

* 権限付与
* コンテナビルド
    * CIで自動でビルド
* Cloud Runデプロイ

```
$ gcloud run deploy ichiba --image asia-northeast1-docker.pkg.dev/PROJECT/ichiba/ichibadocker:latest --platform managed --project PROJECT --region asia-northeast1
```

* CLIアクセス

```
$ curl -X POST "https://ichiba-XXX.run.app:8080/predict" -H "Content-Type: application/json" -d "{"race_id": "202406020211"}"
```

* 画面アクセス

```
https://ichiba-XXX.run.app/form
```

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


