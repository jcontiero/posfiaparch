resource "kubernetes_namespace_v1" "this" {
  metadata {
    name = var.namespace

    labels = {
      app = "oficina-api"
      env = "production"
    }
  }
}

resource "helm_release" "postgres" {
  depends_on = [kubernetes_namespace_v1.this]

  name       = var.release_name
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  version    = var.chart_version
  namespace  = kubernetes_namespace_v1.this.metadata[0].name
  timeout    = 600

  set = [
    {
      name  = "auth.database"
      value = var.database
    },
    {
      name  = "auth.username"
      value = var.username
    },
    {
      name  = "auth.password"
      value = var.password
    },
    {
      name  = "auth.postgresPassword"
      value = var.password
    },
    {
      name  = "primary.persistence.enabled"
      value = "false"
    },
    {
      name  = "volumePermissions.enabled"
      value = "false"
    },
    {
      name  = "primary.readinessProbe.enabled"
      value = "false"
    },
    {
      name  = "primary.livenessProbe.enabled"
      value = "false"
    },
    {
      name  = "primary.resources.requests.memory"
      value = "256Mi"
    },
    {
      name  = "primary.resources.requests.cpu"
      value = "250m"
    },
    {
      name  = "primary.resources.limits.memory"
      value = "512Mi"
    },
    {
      name  = "primary.resources.limits.cpu"
      value = "500m"
    },
  ]
}
