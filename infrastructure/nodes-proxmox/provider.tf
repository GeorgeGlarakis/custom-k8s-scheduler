terraform {
  required_providers {
    proxmox = {
        source = "telmate/proxmox"
        version = "3.0.1-rc3"
    }
  }
}

provider "proxmox" {
  pm_api_url = "https://10.0.100.141:8006/api2/json"

  pm_log_enable = true
  pm_log_file   = "terraform-plugin-proxmox.log"
}