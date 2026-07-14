output "registry_url" {
  description = "URL do registry local"
  value       = "localhost:${var.registry_port}"
}

output "registry_container_name" {
  description = "Nome do container do registry"
  value       = docker_container.this.name
}
