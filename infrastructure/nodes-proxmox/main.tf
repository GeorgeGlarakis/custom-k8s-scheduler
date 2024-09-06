resource "proxmox_vm_qemu" "this" {
    for_each = local.vm_qemu

    name        = each.key
    target_node = local.target_node

    define_connection_info = true
    
    nameserver = each.value.nameserver
    ssh_user   = local.ssh_user
    sshkeys    = local.sshkeys

    onboot   = true
    vm_state = "running"

    memory = each.value.memory
    cpu    = "x86-64-v2-AES"
    cores  = each.value.cpu_cores

    os_type = "ubuntu"
    scsihw  = "virtio-scsi-single"

    disks {
        ide {
            ide2 {
                cdrom {
                    iso = each.value.disks.iso_file
                }
            }
        }
        scsi {
            scsi0 {
                disk {
                    storage = local.storage_name
                    size    = each.value.disks.disk_size

                    asyncio  = "io_uring"
                    cache    = "none"
                    iothread = true
                }
            }
        }
    }

    efidisk {
        efitype = "4m"
        storage = local.storage_name
    }

    network {
        model       = "virtio"
        bridge      = "vmbr0"
        firewall    = true
    }

    tags = local.tags
}