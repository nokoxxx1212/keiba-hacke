variable "gcp_project" {
  description = "The ID of the project in which the resource belongs."
}
 
variable "gcp_region" {
  description = "The region of GCP to work in."
  default     = "us-central1"
}

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