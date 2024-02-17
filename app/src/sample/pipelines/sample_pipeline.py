from google.cloud import aiplatform
from kfp import dsl
from kfp.v2 import compiler
from kfp.v2.dsl import ContainerSpec
from dotenv import load_dotenv
import os

# コンポーネントを定義
@dsl.container_component
def sample_component() -> ContainerSpec:
    return ContainerSpec(
        image='gcr.io/keiba-hacke/khsampledocker',
        command=["python3", "sample.py", "--number", "3"],
        # command=["ls"],
    )

# パイプラインを定義
@dsl.pipeline(
    name='sample-pipeline',
    description='A pipeline that runs the sample.py script.'
)
def sample_pipeline():
    # コンポーネントのインスタンスを作成
    sample_task = sample_component()

# パイプラインを実行
def run_pipeline(project: str, location: str, pipeline_root: str):
    # Vertex AI clientを初期化
    aiplatform.init(project=project, location=location)

    # パイプラインを実行
    job = aiplatform.PipelineJob(
        display_name='sample-pipeline',
        template_path='sample_pipeline_job.json',
        pipeline_root=pipeline_root,
    )
    job.run()

if __name__ == '__main__':
    # パイプラインを実行するためのパラメータ
    env_path = f".env.{os.getenv('APP_ENV', 'dev')}"
    load_dotenv(dotenv_path=env_path)
    PROJECT_ID = os.getenv('PROJECT_ID')
    LOCATION = os.getenv('LOCATION')
    PIPELINE_ROOT = os.getenv('PIPELINE_ROOT')

    # パイプラインをコンパイル
    compiler.Compiler().compile(
        pipeline_func=sample_pipeline,
        package_path='sample_pipeline_job.json'
    )

    # パイプラインを実行
    run_pipeline(PROJECT_ID, LOCATION, PIPELINE_ROOT)