locals {
    target_node = "glarakis"
    storage_name = "local-lvm"

    iso_name = "ubuntu-22.04.4-live-server-amd64.iso"
    iso_file = "local:iso/${local.iso_name}"

    ssh_user = "glarakis"
    sshkeys  = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCjr8Uqla5/IbTK+nB0nivIlcZOhepABmi6o3c8pbkK7ykdK9l2J+aNCHeJlM91yKpaqEtspBjrl49kt4ugVq2wl/vGKuoAM3Tsm6ZPei7fdmGzyyu7vTjkhiW+PFHv8g25YfJqgk7d5CS/QWS3AZVJMGugjvF+tgnnkAffEaaVjk6SSj7goYD4IzfLSs3oyhW5X4xw3jIMMHgWFUTiRZB0TjdgahNpIrcRP9O9yQvEvmp0pRJAlROnhLvlSHPFd+u98OA0xxAdl7z5WEFNQre/1QDj2ssB1AsotFQVqgngMRNSYThUxiTK7MTEb2aMGXLptwT7OKKfnawvCT/+izgt wsl-Ubuntu"

    vm_qemu = {
        master = {
            nameserver = "master"

            memory = 3072
            cpu_cores = 2

            disks = {
                iso_file = local.iso_file
                disk_size = "32G" 
            }
        },
        worker-1 = {
            nameserver = "worker-1"

            memory = 2048
            cpu_cores = 2
            disks = {
                iso_file = local.iso_file
                disk_size = "32G" 
            }
        },
        # worker-2 = {
        #     nameserver = "worker-2"

        #     memory = 1024
        #     cpu_cores = 1

        #     disks = {
        #         iso_file = local.iso_file
        #         disk_size = "32G" 
        #     }
        # },
    }

    tags = "managed_by_terraform"
}