from prefect import flow, task
import papermill as pm

@task
def execute_notebook(input_nb, output_nb, parameters={}):
    pm.execute_notebook(
        input_nb,
        output_nb,
        parameters=parameters,
        kernel_name='python3'
    )

@flow
def run_notebooks_with_papermill():
    notebooks = [("sample_1.ipynb", "sample_1_output.ipynb"), ("sample_2.ipynb", "sample_2_output.ipynb")]
    for input_nb, output_nb in notebooks:
        execute_notebook(input_nb, output_nb, parameters={})

run_notebooks_with_papermill()
