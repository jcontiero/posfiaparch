variable "environment" {
  description = "Ambiente de deploy (local, staging, production)"
  type        = string
  default     = "local"
}

variable "cluster_name" {
  description = "Nome do cluster Kubernetes"
  type        = string
  default     = "oficina-api"
}

variable "kubernetes_version" {
  description = "Versão do Kubernetes para o cluster kind"
  type        = string
  default     = "v1.32.0"
}

variable "kubeconfig_path" {
  description = "Caminho onde o kubeconfig será gerado"
  type        = string
  default     = ""
}

variable "http_host_port" {
  description = "Porta no host para mapeamento HTTP do cluster kind"
  type        = number
  default     = 8080
}

variable "https_host_port" {
  description = "Porta no host para mapeamento HTTPS do cluster kind"
  type        = number
  default     = 8443
}

variable "registry_name" {
  description = "Nome do container do registry local"
  type        = string
  default     = "oficina-api-registry"
}

variable "registry_port" {
  description = "Porta no host para o registry local"
  type        = number
  default     = 5000
}

variable "postgres_namespace" {
  description = "Namespace para o PostgreSQL no cluster"
  type        = string
  default     = "oficina-api"
}

variable "postgres_release_name" {
  description = "Nome do release Helm do PostgreSQL"
  type        = string
  default     = "postgres"
}

variable "postgres_chart_version" {
  description = "Versão do chart Bitnami PostgreSQL"
  type        = string
  default     = "16.0.0"
}

variable "postgres_database" {
  description = "Nome do banco de dados inicial"
  type        = string
  default     = "oficina_db"
}

variable "postgres_username" {
  description = "Usuário do PostgreSQL"
  type        = string
  default     = "oficina_user"
}

variable "postgres_password" {
  description = "Senha do PostgreSQL"
  type        = string
  default     = "oficina_pass"
  sensitive   = true
}

variable "postgres_persistence_size" {
  description = "Tamanho do volume de persistência do PostgreSQL"
  type        = string
  default     = "5Gi"
}
