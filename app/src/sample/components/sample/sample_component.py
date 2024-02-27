from kfp import dsl
from kfp.v2.dsl import ContainerSpec

# コンポーネントを定義
@dsl.container_component
def sample_component() -> ContainerSpec:
    return ContainerSpec(
        image='gcr.io/keiba-hacke/khsampledocker',
        command=["python3", "sample.py", "--number", "3"],
    )