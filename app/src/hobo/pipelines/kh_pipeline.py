from google.cloud import aiplatform
from kfp import dsl
from kfp.v2 import compiler
from dotenv import load_dotenv
import os
from src.hobo.components.netkeiba_scraper.netkeiba_scraper_component import netkeiba_scraper_component
from src.hobo.components.netkeiba_preprocess.netkeiba_preprocess_component import netkeiba_preprocess_component
from src.hobo.components.train_lgb.train_lgb_component import train_lgb_component


# パイプラインを定義
@dsl.pipeline(
    name='kh-pipeline',
    description='A pipeline that runs the kh script.'
)
def kh_pipeline():
    # コンポーネントのインスタンスを作成
    netkeiba_scraper_task = netkeiba_scraper_component()
    netkeiba_preprocess_task = netkeiba_preprocess_component()
    train_lgb_task = train_lgb_component()
    netkeiba_preprocess_task.after(netkeiba_scraper_task)
    train_lgb_task.after(netkeiba_preprocess_task)

# パイプラインを実行
def run_pipeline(project: str, location: str, pipeline_root: str):
    # Vertex AI clientを初期化
    aiplatform.init(project=project, location=location)

    # パイプラインを実行
    job = aiplatform.PipelineJob(
        display_name='kh-pipeline',
        template_path='kh_pipeline_job.json',
        pipeline_root=pipeline_root,
        enable_caching=False
    )
    job.run(service_account="exec-vap@keiba-hacke.iam.gserviceaccount.com")

if __name__ == '__main__':
    # パイプラインを実行するためのパラメータ
    env_path = f".env.{os.getenv('APP_ENV', 'dev')}"
    load_dotenv(dotenv_path=env_path)
    PROJECT_ID = os.getenv('PROJECT_ID')
    LOCATION = os.getenv('LOCATION')
    PIPELINE_ROOT = os.getenv('PIPELINE_ROOT')

    # パイプラインをコンパイル
    compiler.Compiler().compile(
        pipeline_func=kh_pipeline,
        package_path='kh_pipeline_job.json'
    )

    # パイプラインを実行
    run_pipeline(PROJECT_ID, LOCATION, PIPELINE_ROOT)