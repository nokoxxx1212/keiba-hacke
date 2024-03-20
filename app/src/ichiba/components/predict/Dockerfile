FROM python:3.11

ARG GCS_BUCKET
ARG GCP_SA_KEY
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/key.json
RUN echo $GCP_SA_KEY | base64 -d > $GOOGLE_APPLICATION_CREDENTIALS
RUN gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

# install python package
COPY pyproject.toml ./
RUN pip install poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --with test,lint,ichiba

# install google cloud sdk
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update -y && apt-get install -y google-cloud-sdk

# mount dir
RUN mkdir -p /opt/mnt
WORKDIR /opt/mnt

# copy all files into container
# COPY . /opt/mnt

# download data from gcs
RUN echo ${GCS_BUCKET}
RUN gsutil cp -r gs://${GCS_BUCKET}/ichiba/pickle_data /opt/mnt/pickle_data
RUN gsutil cp -r gs://${GCS_BUCKET}/ichiba/race_result_place /opt/mnt/race_result_place
RUN gsutil cp -r gs://${GCS_BUCKET}/ichiba/train_data /opt/mnt/train_data

# expose port
EXPOSE 8888

# run uvicorn command when the container starts
CMD ["uvicorn", "my_fastapi:app", "--reload"]