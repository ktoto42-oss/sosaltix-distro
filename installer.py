import os
import sys
import getpass
import subprocess

base_packages = [
    "base",
    "base-devel",
    "linux-firmware",
    "linux-headers",
    "networkmanager",
    "grub",
    "efibootmgr",
    "nano",
    "vim",
    "git",
    "fastfetch"
]

kde_packages = [
    "plasma-login-manager",
    "plasma-desktop",
    "plasma-pa",
    "plasma-nm",
    "dolphin",
    "alacritty",
    "ark",
    "firefox"
]

services = ["NetworkManager", "plasma-login-manager"]

def run(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        print(f"\n[!] Error: {command}")
        sys.exit(1)

def install():
    print("=== Installation Sosaltix Linux ===")
    drive = input("Installation disk (example /dev/sda): ")
    username = input("User name: ")
    user_password = getpass.getpass("User password: ")
    root_password = getpass.getpass("Root password: ")

    print("=== Disk preparation ===")
    run(f"parted -s {drive} mklabel gpt")
    run(f"parted -s {drive} mkpart primary fat32 1MiB 513MiB")
    run(f"parted -s {drive} set 1 esp on")
    run(f"parted -s {drive} mkpart primary ext4 513MiB 100%")

    p1 = f"{drive}p1" if "nvme" in drive else f"{drive}1"
    p2 = f"{drive}p2" if "nvme" in drive else f"{drive}2"

    run(f"mkfs.vfat -F32 {p1} > /dev/null")
    run(f"mkfs.ext4 -F {p2} > /dev/null")

    run(f"mount {p2} /mnt")
    os.makedirs("/mnt/boot", exist_ok=True)
    run(f"mount {p1} /mnt/boot")

    print("=== Installation packages === ")
    all_pkgs = " ".join(BASE_PACKAGES + GUI_PACKAGES)
    run(f"pacstrap -K /mnt {all_pkgs}")
    run("genfstab -U /mnt >> /mnt/etc/fstab")

    print("=== Final setup ===")
    chroot_script = f"""
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
    echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen
    locale-gen
    echo "LANG=ru_RU.UTF-8" > /etc/locale.conf

    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
    echo "Sosaltix" > /etc/hostname

    echo "root:{root_password}" | chpasswd
    useradd -m -G wheel -s /bin/bash {username}
    echo "{username}:{password}" | chpasswd
    echo "%wheel ALL=(ALL) ALL" > /etc/sudoers.d/wheel

    grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=Sosaltix
    grub-mkconfig -o /boot/grub/grub.cfg
    {enable_services}
    """
    run(f"arch-chroot /mnt /bin/bash -c '{chroot_script}'")

    print(f"\n[COMPLETE] Sosaltix installed. User: {username}")

def apply_sosaltix_branding():
    new_name = "Sosaltix"
    ascii_path = "/logo.txt"

    subprocess.run(['hostnamectl', 'set-hostname', new_name], check=False)

    os_data = (
        f'NAME="{new_name}"\n'
        f'PRETTY_NAME="{new_name} Linux"\n'
        f'ID={new_name.lower()}\n'
        f'ID_LIKE=arch\n'
        'ANSI_COLOR="0;34"\n'
        f'LOGO={new_name.lower()}\n'
    )
    with open('/etc/os-release', 'w') as f:
        f.write(os_data)

    with open('/etc/lsb-release', 'w') as f:
        f.write(f'DISTRIB_ID={new_name}\nDISTRIB_RELEASE=rolling\nDISTRIB_DESCRIPTION="{new_name} Linux"\n')

    if os.path.exists(ascii_path):
        with open(ascii_path, 'r') as l, open('/etc/issue', 'w') as i:
            i.write(f"{l.read()}\n{new_name} Linux \\r (\\l)\n\n")

    grub_def = '/etc/default/grub'
    if os.path.exists(grub_def):
        subprocess.run(['sed', '-i', f's/GRUB_DISTRIBUTOR=.*/GRUB_DISTRIBUTOR="{new_name}"/', grub_def])
        subprocess.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'], capture_output=True)

    ff_config_dir = '/etc/fastfetch'
    os.makedirs(ff_config_dir, exist_ok=True)
    ff_config_path = os.path.join(ff_config_dir, 'config.jsonc')
    ff_json = (
        '{\n'
        '    "$schema": "https://github.com",\n'
        '    "logo": {\n'
        f'        "source": "{ascii_path}",\n'
        '        "type": "auto"\n'
        '    }\n'
        '}\n'
    )
    with open(ff_config_path, 'w') as f:
        f.write(ff_json)

if __name__ == "__main__":
    if os.getuid() != 0: sys.exit("Need root!")
    install()
    apply_sosaltix_branding()