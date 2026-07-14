variable "cluster_name" {
  description = "Nome do cluster Kubernetes"
  type        = string
}

variable "kubernetes_version" {
  description = "Versão do Kubernetes (imagem kindest/node)"
  type        = string
  default     = "v1.32.0"
}

variable "kubeconfig_path" {
  description = "Caminho onde o kubeconfig será gerado"
  type        = string
}

variable "http_host_port" {
  description = "Porta no host para mapeamento HTTP (extra)"
  type        = number
  default     = 8080
}

variable "https_host_port" {
  description = "Porta no host para mapeamento HTTPS (extra)"
  type        = number
  default     = 8443
}
