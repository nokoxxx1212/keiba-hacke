variable "gcp_project" {
  description = "The ID of the project in which the resource belongs."
}
 
variable "gcp_region" {
  description = "The region of GCP to work in."
  default     = "us-central1"
}

# BigQuery dataset variables
variable "dataset_id" {
  description = "The ID of the BigQuery dataset."
}

variable "friendly_name" {
  description = "A friendly name for the BigQuery dataset."
}

variable "description" {
  description = "A description of the BigQuery dataset."
}

variable "dataset_location" {
  description = "The location of the BigQuery dataset."
  default     = "US"
}

variable "labels" {
  description = "A set of key/value label pairs to assign to the BigQuery dataset."
  type        = map(string)
  default     = {}
}

# Notebooks instance variables
variable "instance_name" {
  description = "The name of the Vertex AI Workbench instance."
  type        = string
}

variable "location" {
  description = "The location of the Vertex AI Workbench instance."
  type        = string
}

variable "machine_type" {
  description = "The machine type of the Vertex AI Workbench instance."
  type        = string
}

variable "boot_disk_type" {
  description = "The type of the boot disk of the Vertex AI Workbench instance."
  type        = string
}

variable "boot_disk_size_gb" {
  description = "The size of the boot disk of the Vertex AI Workbench instance."
  type        = number
}

variable "repository" {
  description = "The repository of the Vertex AI Workbench instance."
  type        = string
}

variable "disable_public_ip" {
  description = "Whether to disable public IP of the Vertex AI Workbench instance."
  type        = bool
}

variable "disable_proxy_access" {
  description = "Whether to disable proxy access of the Vertex AI Workbench instance."
  type        = bool
}

variable "instance_owners" {
  description = "The owners of the Vertex AI Workbench instance."
  type        = list(string)
}

variable "idle_timeout_seconds" {
  description = "The idle timeout of the Vertex AI Workbench instance."
  type        = number
}