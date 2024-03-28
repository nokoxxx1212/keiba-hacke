from prefect import flow, task
import time

@task
def add(x, y):
    return x + y

@task
def multiply(x, y):
    time.sleep(500)
    return x * y

@flow
def my_complex_flow(x, y, z):
    add_result = add(x, y)
    final_result = multiply(add_result, z)
    print(f"最終結果は {final_result} です。")

# フローの実行
my_complex_flow(1, 2, 3)