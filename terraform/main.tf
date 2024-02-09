# BigQuery dataset resources
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  friendly_name               = var.friendly_name
  description                 = var.description
  location                    = var.dataset_location

  labels = var.labels
}

# Notebooks instance resources
resource "google_workbench_instance" "instance" {
  name = var.instance_name
  location = var.location
  gce_setup {
    machine_type = var.machine_type
    boot_disk {
      disk_type = var.boot_disk_type
      disk_size_gb  = var.boot_disk_size_gb
    }
    disable_public_ip = var.disable_public_ip
  }
  disable_proxy_access = var.disable_proxy_access
  instance_owners  = var.instance_owners
}