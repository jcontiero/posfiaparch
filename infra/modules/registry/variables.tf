variable "registry_name" {
  description = "Nome do container do registry"
  type        = string
}

variable "registry_port" {
  description = "Porta no host para o registry"
  type        = number
  default     = 5000
}
