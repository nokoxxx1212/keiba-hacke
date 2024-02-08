# BigQuery dataset resources
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  friendly_name               = var.friendly_name
  description                 = var.description
  location                    = var.dataset_location

  labels = var.labels
}

# Notebooks instance resources
# resource "google_notebooks_instance" "instance" {
#   name          = var.instance_name
#   location      = var.location
#   machine_type  = var.machine_type
# 
#   boot_disk_type = var.boot_disk_type
#   boot_disk_size_gb = var.boot_disk_size_gb
# 
#   container_image {
#     repository = var.repository
#     tag = "latest"
#   }
# 
#   no_remove_data_disk = var.no_remove_data_disk
# 
#   no_public_ip = var.no_public_ip
#   no_proxy_access = var.no_proxy_access
# 
#   instance_owners = var.instance_owners
# }

resource "google_workbench_instance" "instance" {
  name = var.instance_name
  location = var.location
  gce_setup {
    machine_type = var.machine_type
    boot_disk {
      disk_type = var.boot_disk_type
      disk_size_gb  = var.boot_disk_size_gb
    }
    container_image {
     repository = var.repository
     tag = "latest"
   }
    shielded_instance_config {
      enable_integrity_monitoring = true
      enable_secure_boot = true
      enable_vtpm = true
    }
    disable_public_ip = var.disable_public_ip
    disable_proxy_access = var.disable_proxy_access
    instance_owners  = var.instance_owners
    metadata {
      idle-timeout-seconds = var.idle_timeout_seconds
    }
  }
}