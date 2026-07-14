resource "kind_cluster" "this" {
  name            = var.cluster_name
  node_image      = "kindest/node:${var.kubernetes_version}"
  wait_for_ready  = true
  kubeconfig_path = var.kubeconfig_path

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"

      kubeadm_config_patches = [
        <<EOT
kind: InitConfiguration
nodeRegistration:
  kubeletExtraArgs:
    node-labels: "ingress-ready=true"
EOT
      ]

      extra_port_mappings {
        container_port = 80
        host_port      = var.http_host_port
      }

      extra_port_mappings {
        container_port = 443
        host_port      = var.https_host_port
      }
    }
  }
}
