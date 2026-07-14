output "cluster_name" {
  description = "Nome do cluster provisionado"
  value       = kind_cluster.this.name
}

output "kubeconfig_path" {
  description = "Caminho do kubeconfig gerado"
  value       = var.kubeconfig_path
}

output "endpoint" {
  description = "Endpoint do cluster Kubernetes"
  value       = kind_cluster.this.endpoint
}
