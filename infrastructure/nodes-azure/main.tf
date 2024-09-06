resource "azurerm_resource_group" "this" {
  name     = "rg-${local.name}"
  location = "West Europe"
}

resource "azurerm_public_ip" "this" {
  for_each = { for index, vm in local.vm : index => vm }

  name                = "pip-${each.key}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  allocation_method   = "Dynamic"
  domain_name_label   = each.key

  tags = local.tags
}

resource "azurerm_network_interface" "this" {
  for_each = { for index, vm in local.vm : index => vm }

  name                = "nic-${each.key}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.this.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.this[each.key].id
  }

  tags = local.tags
}

resource "azurerm_linux_virtual_machine" "this" {
  for_each = local.vm

  name                = each.key
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  size                = each.value.sku
  admin_username      = each.value.admin_username
  network_interface_ids = [
    azurerm_network_interface.this[each.key].id
  ]

  admin_ssh_key {
    username   = each.value.admin_username
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "23_04-lts"
    version   = "latest"
  }

  tags = local.tags
}