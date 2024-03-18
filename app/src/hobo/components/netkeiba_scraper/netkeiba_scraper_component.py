from kfp import dsl
from kfp.v2.dsl import ContainerSpec

# コンポーネントを定義
@dsl.container_component
def netkeiba_scraper_component() -> ContainerSpec:
    return ContainerSpec(
        image='gcr.io/keiba-hacke/khnetkeiba_scraperdocker',
        command=["python3", "netkeiba_scraper.py", "--year_start", "2024", "--year_end", "2024"],
    )