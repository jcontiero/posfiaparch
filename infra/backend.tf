# Backend local para simplificar o Tech Challenge.
# Em ambiente de equipe, recomenda-se usar backend remoto (S3 + DynamoDB, GCS, Azure Storage, etc.).
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
