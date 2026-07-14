variable "namespace" {
  description = "Namespace onde o PostgreSQL será instalado"
  type        = string
  default     = "oficina-api"
}

variable "release_name" {
  description = "Nome do release Helm do PostgreSQL"
  type        = string
  default     = "postgres"
}

variable "chart_version" {
  description = "Versão do chart Bitnami PostgreSQL"
  type        = string
  default     = "16.0.0"
}

variable "database" {
  description = "Nome do banco de dados inicial"
  type        = string
  default     = "oficina_db"
}

variable "username" {
  description = "Usuário do PostgreSQL"
  type        = string
  default     = "oficina_user"
}

variable "password" {
  description = "Senha do PostgreSQL"
  type        = string
  sensitive   = true
}

variable "persistence_size" {
  description = "Tamanho do volume de persistência"
  type        = string
  default     = "5Gi"
}

variable "kubeconfig_path" {
  description = "Caminho do kubeconfig do cluster"
  type        = string
}
