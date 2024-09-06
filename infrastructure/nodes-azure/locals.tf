locals {
    name = "k8s-nodes-weu"

    admin = "glarakis"

    vm = {
        master = {
            sku = "B1s"
            admin_username = local.admin
        },
        worket-1 = {
            sku = "B1s"
            admin_username = local.admin
        },
        worker-2 = {
            sku = "B1s"
            admin_username = local.admin
        }
    }

    upnet_vpn = "150.140.0.0/16"

    tags = {

    }
}