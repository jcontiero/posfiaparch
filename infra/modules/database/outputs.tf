output "namespace" {
  description = "Namespace do PostgreSQL"
  value       = kubernetes_namespace_v1.this.metadata[0].name
}

output "release_name" {
  description = "Nome do release Helm"
  value       = var.release_name
}

output "service_name" {
  description = "Nome do service interno do PostgreSQL"
  value       = "postgres"
}

output "connection_string" {
  description = "String de conexão com o PostgreSQL (driver pg8000)"
  value       = "postgresql+pg8000://${var.username}:${var.password}@postgres.${kubernetes_namespace_v1.this.metadata[0].name}.svc.cluster.local:5432/${var.database}"
  sensitive   = true
}
