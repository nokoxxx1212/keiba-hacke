from kfp import dsl
from kfp.v2.dsl import ContainerSpec

# コンポーネントを定義
@dsl.container_component
def train_lgb_component() -> ContainerSpec:
    return ContainerSpec(
        image='gcr.io/keiba-hacke/khtrain_lgbdocker',
        command=["python3", "train_lgb.py", "--year_start", "2024", "--year_end", "2024"],
    )