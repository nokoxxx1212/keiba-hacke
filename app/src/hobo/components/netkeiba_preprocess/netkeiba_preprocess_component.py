from kfp import dsl
from kfp.v2.dsl import ContainerSpec

# コンポーネントを定義
@dsl.container_component
def netkeiba_preprocess_component() -> ContainerSpec:
    return ContainerSpec(
        image='gcr.io/keiba-hacke/khnetkeiba_preprocessdocker',
        command=["python3", "netkeiba_preprocess.py", "--update_time_threshold", "2024-03-10 00:00:00"],
    )