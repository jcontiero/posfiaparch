resource "kubernetes_namespace_v1" "this" {
  metadata {
    name = var.namespace

    labels = {
      app = "oficina-api"
      env = "production"
    }
  }
}

# Helm release removido para evitar conflitos com os manifestos em k8s/
