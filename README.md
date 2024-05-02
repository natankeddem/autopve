# autopve

## Demo

[autopve_demo.webm](https://github.com/natankeddem/autopve/assets/44515217/827bdd22-5311-43c1-9452-a56fa11998aa)

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

### OPNsense Setup

For Unbound you will need to enable TXT records and make an appropriate host override entry.
![image](https://github.com/natankeddem/autopve/assets/44515217/997f15b7-e46f-4320-9d19-23feffcb4fdc)
![image](https://github.com/natankeddem/autopve/assets/44515217/e680fff0-e8b0-4236-88e9-0cd45ce1088c)


