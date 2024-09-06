sudo swapoff -a

# sudo apt install docker.io -y

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

wget https://github.com/containernetworking/plugins/releases/download/v1.4.1/cni-plugins-linux-amd64-v1.4.1.tgz
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.4.1.tgz

# curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add

# sudo apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main"

# sudo mkdir -m 0755 -p /etc/apt/keyrings/

# wget -O- https://packages.cloud.google.com/apt/doc/apt-key.gpg |
#     gpg --dearmor |
#     sudo tee /etc/apt/keyrings/google.gpg > /dev/null
#     sudo chmod 644 /etc/apt/keyrings/google.gpg

# echo "deb [signed-by=/etc/apt/keyrings/google.gpg] http://apt.kubernetes.io/ kubernetes-xenial main" |
#     sudo tee /etc/apt/sources.list.d/kubernetes.list
#     sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | 
    sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | 
    sudo tee /etc/apt/sources.list.d/kubernetes.list

# Optional (you can find the email address / ID using `apt-key list`)
# sudo apt-key del support@example.com

# Forwarding IPv4 and letting iptables see bridged traffic
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl params required by setup, params persist across reboots
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply sysctl params without reboot
sudo sysctl --system
# ---

# Verify that the br_netfilter, overlay modules are loaded by running the following commands:
lsmod | grep br_netfilter
lsmod | grep overlay
sysctl net.bridge.bridge-nf-call-iptables net.bridge.bridge-nf-call-ip6tables net.ipv4.ip_forward



sudo apt-get update

# sudo apt install kubeadm kubelet kubectl kubernetes-cni -y
sudo apt-get install -y kubelet kubeadm kubectl kubernetes-cni
sudo apt-mark hold kubelet kubeadm kubectl kubernetes-cni

sudo nano /etc/containerd/config.toml
# comment out `disabled_plugins = ["cri"]`

# Source:
#     https://github.com/containerd/containerd/issues/6964
#     https://github.com/containerd/containerd/blob/main/docs/cri/config.md?plain=1#L278-L282

version = 2
[plugins."io.containerd.grpc.v1.cri"]
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
            runtime_type = "io.containerd.runc.v2"
            [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
                SystemdCgroup = true


sudo systemctl restart containerd

# containerd config default > /etc/containerd/config.toml

master: sudo kubeadm init --pod-network-cidr=10.244.0.0/16

worker: sudo kubeadm join

master: mkdir -p $HOME/.kube
        sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
        sudo chown $(id -u):$(id -g) $HOME/.kube/config


sudo kubeadm join 10.0.100.148:6443 --token i1o7rp.yzh19xv35wf5rhn6 \
        --discovery-token-ca-cert-hash sha256:cd5d732e89bd3711b75fb384eb8eb7ff7222fdb0317670c55fb9f972ff4a86e4

# master: kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/master/manifests/calico.yaml


# ------------------------------------

# Add cloudflare gpg key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# Add this repo to your apt repositories
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

# install cloudflared
sudo apt-get update && sudo apt-get install cloudflared

# ------------------------------------

sudo snap install helm --classic

# Add kubernetes-dashboard repository
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
# Deploy a Helm Release named "kubernetes-dashboard" using the kubernetes-dashboard chart
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard

kubectl -n kubernetes-dashboard port-forward --address='0.0.0.0' svc/kubernetes-dashboard-kong-proxy 8443:443
https://10.0.100.148:8443/#/login

kubectl -n kubernetes-dashboard create token admin-user