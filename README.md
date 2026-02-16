# autopve

## Demo

https://github.com/natankeddem/autopve/assets/44515217/9439e2e2-a7bf-4677-aea8-0684318bea6c

## Information

GUI configurable web server for Proxmox automated installation. More information about the automated installation feature built into the Proxmox installation media can be found [here](https://pve.proxmox.com/wiki/Automated_Installation).

## Features

- **Dynamic Answers**: Allows multiple answers to be accessable at the same address by responding only to matching system information.
- **Answer Inheritance**: Allows defining common configurations in the "Default" answer and then only needing to specify alterations in other answers.
- **History**: All answer requests are logged and all system and response information is displayed.
- **Live Notifications**: Request activity displayed in realtime.

### Using Docker

1. Download `docker-compose.yml`.

2. Customize the `docker-compose.yml` file to suit your requirements.

3. Run the application using Docker Compose:

   ```bash
   docker-compose up -d
   ```

### Using Proxmox LXC Container

1. Download `pve-install.yml` and `inv.yml`.

2. Ensure you have a compatible Debian template available and updated `inv.yml` accordingly.

3. Customize the `inv.yml` file to match your specific setup requirements.

4. Execute the Ansible playbook for Proxmox LXC container installation against your Proxmox host:

   ```bash
   ansible-playbook -i inv.yml pve-install.yml
   ```

## Usage

The configuration GUI can be accessed at `http://host:8080`. Answers are hosted at `http://host:8080/answer`.

### Automated Post-Installation with Ansible Playbooks

`autopve` can automatically trigger an Ansible playbook upon a successful Proxmox installation. This is achieved by using the `post-installation-webhook` feature available in Proxmox VE.

When the installation is complete, the Proxmox installer sends a POST request containing detailed system information to a specified URL. You can configure this URL to be an `autopve` endpoint that executes a playbook, passing the received system information to it as an extra variable.

#### How to Use

**1. Create and Manage Your Playbook in `autopve`**

A new "Playbooks" section is available in the UI. Here you can create a new playbook, which establishes a dedicated directory at `data/playbooks/<playbook_name>/`. Within the UI, you can then edit the `playbook.yaml` and `inventory.yaml` files for that playbook.

**2. Accessing System Information in Your Playbook**

The system information sent by the Proxmox installer is passed directly to your playbook as a JSON string via the `-e` or `--extra-vars` flag. Ansible automatically parses this into a variable named `system_info`. You can then access any of the data points from the webhook in your tasks.

For example, to access the Proxmox product version, you would use `{{ system_info.product.version }}`.

```yaml
---
- name: Playbook to print the proxmox version
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:        
    - name: Print Version
      ansible.builtin.debug:
        msg: "The Proxmox version is: {{ system_info.product.version }}"

    - name: Show all received system info
      ansible.builtin.debug:
        var: system_info
```

**3. Configure the Proxmox Answer File**

In your `answer`, configure the `post-installation-webhook` section to point to the `autopve` endpoint. The URL must be in the format `http://<your-autopve-ip>:8080/playbook/<playbook_name>`.
```toml
[post-installation-webhook]
url = "http://host:8080/playbook/my-playbook"
# cert-fingerprint = "..." # Optional: if autopve is behind HTTPS
```

When this installation completes, `autopve` will execute the playbook located at `data/playbooks/my-first-playbook/`. The command will be structured like this:
```bash
ansible-playbook data/playbooks/my-playbook/playbook.yaml -i data/playbooks/my-playbook/inventory.yaml -e '{"product": {"fullname": "Proxmox VE", ...}}'
```

### Hosting First-Boot Scripts & Files

`autopve` now includes a simple file management system that can host scripts, executables, or any other files. This is particularly useful for the `first-boot-hook` feature in Proxmox, which can download and execute a script from a URL after installation.

#### How to Use

**1. Upload Files to `autopve`**

In the UI's side drawer, there is a "FILES" section. You can upload files here, and they will be stored in the `data/files` directory.

**2. Configure the Proxmox Answer File**

In your `answer`, configure the `first-boot` section. Set the `source` to `from-url` and provide the URL where `autopve` is hosting your file. Files are served from the `/files/` endpoint.
```toml
[first-boot]
source = "from-url"
ordering = "network-online" # Ensure network is up before downloading
url = "http://host:8080/files/my-first-boot-script.sh"
# cert-fingerprint = "..." # Optional: if autopve is behind HTTPS
```
This configuration will cause the new Proxmox node to download `my-first-boot-script.sh` from `autopve` and execute it on its first boot.

**Note:** As per the Proxmox documentation, scripts intended for the first-boot hook must start with a shebang (e.g., `#!/bin/bash`) and should only use interpreters that are available in a default Proxmox installation.

### Ansible Playbook Example
```
---
# Make sure you added AutoPVE host to Global > root-ssh-keys
# PLAY 1: Parse System Info & Wait for Reboot
- name: Prepare and Wait for Target
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    # -------------------------------------------------------------
    # 1. Extract the IP from system_info
    # -------------------------------------------------------------
    - name: Parse Management IP from system_info
      set_fact:
        target_ip: >-
          {{ 
            (system_info['network-interfaces'] 
            | selectattr('is-management', 'defined') 
            | selectattr('is-management', 'equalto', true) 
            | map(attribute='address') 
            | first).split('/')[0] 
          }}

    # Optional: Log what we found based on the webhook data
    - name: Display System Details
      ansible.builtin.debug:
        msg: 
          - "Targeting IP: {{ target_ip }}"
          - "Proxmox Version: {{ system_info.product.version }}"
          - "Kernel: {{ system_info['kernel-version'].release }}"
          - "Boot Mode: {{ system_info['boot-info'].mode }}"

    # -------------------------------------------------------------
    # 2. Add the dynamic host to the inventory
    # -------------------------------------------------------------
    - name: Add host to in-memory inventory
      add_host:
        name: "{{ target_ip }}"
        groups: new_proxmox_install
        ansible_ssh_common_args: '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
        # Persist system_info to the host so it's available in Play 2
        system_info: "{{ system_info }}"

    # -------------------------------------------------------------
    # 3. Wait for the physical reboot
    # -------------------------------------------------------------
    - name: Wait for SSH on {{ target_ip }}
      ansible.builtin.wait_for:
        host: "{{ target_ip }}"
        port: 22
        state: started
        timeout: 60 # Wait up to 20 mins
        delay: 10     # Critical: Wait for installer to shut down first
      delegate_to: localhost

# PLAY 2: Configure the New System
- name: Configure Proxmox
  hosts: new_proxmox_install
  user: root
  gather_facts: yes
  
  tasks:
    - name: Verify Connection and Context
      ansible.builtin.debug:
        msg: "Configuring host {{ inventory_hostname }} (ID: {{ system_info['machine-id'] }})"

    - name: Add PVE No-Subscription Repository
      ansible.builtin.apt_repository:
        repo: "deb http://download.proxmox.com/debian/pve trixie pve-no-subscription"
        state: present
        filename: pve-no-subscription
        update_cache: no

    - name: Add Ceph No-Subscription Repository
      ansible.builtin.apt_repository:
        repo: "deb http://download.proxmox.com/debian/ceph-squid trixie no-subscription"
        state: present
        filename: ceph-no-subscription
        update_cache: no

    - name: Disable Enterprise Repos (Search & Comment)
      ansible.builtin.shell: |
        # Find files containing enterprise.proxmox.com and comment those lines out
        grep -rl "enterprise.proxmox.com" /etc/apt/sources.list.d/ | xargs sed -i 's/^\([^#]\)/# \1/g'
      register: disable_enterprise
      failed_when: disable_enterprise.rc != 0 and disable_enterprise.rc != 123
      changed_when: disable_enterprise.rc == 0
        
    - name: Update System
      ansible.builtin.apt:
        update_cache: yes
        upgrade: dist
```

### OPNsense Setup

For Unbound you will need to enable TXT records and make an appropriate host override entry.
![image](https://github.com/natankeddem/autopve/assets/44515217/997f15b7-e46f-4320-9d19-23feffcb4fdc)
![image](https://github.com/natankeddem/autopve/assets/44515217/e680fff0-e8b0-4236-88e9-0cd45ce1088c)


