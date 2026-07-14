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

output "client_certificate" {
  description = "Client certificate para autenticação"
  value       = kind_cluster.this.client_certificate
}

output "client_key" {
  description = "Client key para autenticação"
  value       = kind_cluster.this.client_key
}

output "cluster_ca_certificate" {
  description = "CA certificate do cluster"
  value       = kind_cluster.this.cluster_ca_certificate
}
