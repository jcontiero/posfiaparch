output "namespace" {
  description = "Namespace do PostgreSQL"
  value       = helm_release.postgres.namespace
}

output "release_name" {
  description = "Nome do release Helm"
  value       = helm_release.postgres.name
}

output "service_name" {
  description = "Nome do service interno do PostgreSQL"
  value       = "${helm_release.postgres.name}-postgresql"
}

output "connection_string" {
  description = "String de conexão com o PostgreSQL (driver pg8000)"
  value       = "postgresql+pg8000://${var.username}:${var.password}@${helm_release.postgres.name}-postgresql.${helm_release.postgres.namespace}.svc.cluster.local:5432/${var.database}"
  sensitive   = true
}
