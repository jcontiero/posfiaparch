locals {
  kubeconfig_path = var.kubeconfig_path != "" ? var.kubeconfig_path : "${path.module}/kubeconfig"
}

# -----------------------------------------------------------------------------
# Cluster Kubernetes local via kind
# -----------------------------------------------------------------------------
module "cluster" {
  source = "./modules/cluster"

  cluster_name       = var.cluster_name
  kubernetes_version = var.kubernetes_version
  kubeconfig_path    = local.kubeconfig_path
  http_host_port     = var.http_host_port
  https_host_port    = var.https_host_port
}

# Registry será o Docker Hub (conforme definido no plano)

# -----------------------------------------------------------------------------
# PostgreSQL dentro do cluster via Helm
# -----------------------------------------------------------------------------
module "database" {
  source = "./modules/database"

  kubeconfig_path  = module.cluster.kubeconfig_path
  namespace        = var.postgres_namespace
  release_name     = var.postgres_release_name
  chart_version    = var.postgres_chart_version
  database         = var.postgres_database
  username         = var.postgres_username
  password         = var.postgres_password
  persistence_size = var.postgres_persistence_size
}
