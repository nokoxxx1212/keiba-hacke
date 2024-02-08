# BigQuery dataset resources
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  friendly_name               = var.friendly_name
  description                 = var.description
  location                    = var.dataset_location

  labels = var.labels
}

# Notebooks instance resources
resource "google_notebooks_instance" "instance" {
  name          = var.instance_name
  location      = var.location
  machine_type  = var.machine_type

  boot_disk_type = var.boot_disk_type
  boot_disk_size_gb = var.boot_disk_size_gb

  container_image {
    repository = var.repository
    tag = "latest"
  }

  no_remove_data_disk = var.no_remove_data_disk

  no_public_ip = var.no_public_ip
  no_proxy_access = var.no_proxy_access

  instance_owners = var.instance_owners
}