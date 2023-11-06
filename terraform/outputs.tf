output "bigquery_dataset_id" {
  description = "Unique ID for the BigQuery dataset."
  value       = google_bigquery_dataset.dataset.dataset_id
}

output "bigquery_dataset_self_link" {
  description = "The URI of the created resource."
  value       = google_bigquery_dataset.dataset.self_link
}