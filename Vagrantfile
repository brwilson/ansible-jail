# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.define "freebsd10" do |freebsd10|
    freebsd10.vm.box = "freebsd/FreeBSD-10.2-RELEASE"
    freebsd10.vm.hostname = "freebsd10"
    freebsd10.vm.network "private_network", ip: "10.0.16.24"
    freebsd10.ssh.shell = "/bin/sh"
    freebsd10.vm.base_mac = "080027D14C66"
    freebsd10.vm.synced_folder ".", "/vagrant", type: "nfs"
    freebsd10.vm.provision "shell",
      inline: "pkg install -y python2 vim-lite ansible sudo bash; ln -sf /usr/local/bin/bash /bin/bash; chpass -s /usr/local/bin/bash vagrant"
    freebsd10.vm.provision "ansible_local" do |alocal|
      alocal.playbook = "local.yml"
      #alocal.verbose = "vvv"
    end
  end
end
