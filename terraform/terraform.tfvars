# gcp_project = "aaa"
dataset_id = "sample"
friendly_name = "Sample BigQuery Dataset"
description = "This is a sample BigQuery dataset created with Terraform."
dataset_location = "asia-northeast1"
# labels = { "environment" = "prod", "owner" = "sampleteam" }
instance_name = "dev-kh-wb-01"
location      = "us-central1-a"
machine_type  = "n1-standard-1"
boot_disk_type = "PD_SSD"
boot_disk_size_gb = 150
repository = "gcr.io/deeplearning-platform-release/base-cpu"
disable_public_ip = false
disable_proxy_access = false
idle_timeout_seconds = 3600
# instance_owners = [ "my@service-account.com"]