output "environment" {
  description = "Ambiente provisionado"
  value       = var.environment
}

output "cluster_name" {
  description = "Nome do cluster Kubernetes"
  value       = module.cluster.cluster_name
}

output "kubeconfig_path" {
  description = "Caminho do kubeconfig gerado"
  value       = module.cluster.kubeconfig_path
}

output "kubectl_command" {
  description = "Comando para acessar o cluster com kubectl"
  value       = "kubectl --kubeconfig=${module.cluster.kubeconfig_path} cluster-info"
}

output "registry_url" {
  description = "URL do registry local de imagens"
  value       = module.registry.registry_url
}

output "postgres_namespace" {
  description = "Namespace do PostgreSQL"
  value       = module.database.namespace
}

output "postgres_service_name" {
  description = "Nome do service interno do PostgreSQL"
  value       = module.database.service_name
}

output "postgres_connection_string" {
  description = "String de conexão com o PostgreSQL (driver pg8000)"
  value       = module.database.connection_string
  sensitive   = true
}

output "next_steps" {
  description = "Próximos passos após o provisionamento"
  value       = <<EOT
1. Configure o kubectl: export KUBECONFIG=${module.cluster.kubeconfig_path}
2. Verifique o cluster: kubectl cluster-info
3. Verifique o PostgreSQL: kubectl get pods -n ${module.database.namespace}
4. Faça push da imagem para o registry local:
   docker tag oficina-api:v0.2.0 ${module.registry.registry_url}/oficina-api:v0.2.0
   docker push ${module.registry.registry_url}/oficina-api:v0.2.0
5. Aplique os manifestos em /k8s (ajuste a imagem para usar ${module.registry.registry_url}/oficina-api:v0.2.0)
EOT
}
