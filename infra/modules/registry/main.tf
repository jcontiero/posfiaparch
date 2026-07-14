resource "docker_container" "this" {
  name  = var.registry_name
  image = "registry:2"

  ports {
    internal = 5000
    external = var.registry_port
  }

  restart = "unless-stopped"

  labels {
    label = "app"
    value = "oficina-api"
  }

  labels {
    label = "managed-by"
    value = "terraform"
  }
}
