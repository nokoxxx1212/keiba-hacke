# BigQuery dataset outputs
output "bigquery_dataset_id" {
  description = "Unique ID for the BigQuery dataset."
  value       = google_bigquery_dataset.dataset.dataset_id
}

output "bigquery_dataset_self_link" {
  description = "The URI of the created resource."
  value       = google_bigquery_dataset.dataset.self_link
}

# Notebooks instance outputs
output "instance_name" {
  description = "The name of the Vertex AI Workbench instance."
  value       = google_notebooks_instance.instance.name
}

output "instance_location" {
  description = "The location of the Vertex AI Workbench instance."
  value       = google_notebooks_instance.instance.location
}

output "instance_machine_type" {
  description = "The machine type of the Vertex AI Workbench instance."
  value       = google_notebooks_instance.instance.machine_type
}

output "instance_state" {
  description = "The state of the Vertex AI Workbench instance."
  value       = google_notebooks_instance.instance.state
}