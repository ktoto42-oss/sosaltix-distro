import os
import sys
import getpass
import subprocess

base_packages = [
    "base",
    "base-devel",
    "linux",
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
    "sddm",
    "plasma-desktop",
    "plasma-pa",
    "plasma-nm",
    "dolphin",
    "alacritty",
    "ark",
    "firefox"
]

services = ["NetworkManager", "sddm"]

def run(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        print(f"\n[!] Error: {command}")
        sys.exit(1)

def install():
    print("=== Installation Sosaltix Linux ===")
    run(f"lsblk")
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
    all_pkgs = " ".join(base_packages + kde_packages)
    while True:
        success = run(f"pacstrap -K /mnt {all_pkgs}")
        
        if success:
            print("Packages installed successfully!")
            break
        else:
            print("\n[!] Package installation failed.")
            choice = input("Press 'r' to retry or any other key to abort: ").lower()
            if choice != 'r':
                print("Installation aborted by user.")
                run("umount -R /mnt", ignore_errors=True)
                sys.exit(1)
            print("\nRetrying installation...\n")
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

    sed -i 's/Arch Linux/Sosaltix Linux/g; s/ID=arch/ID=sosaltix' /etc/os-release
    echo "Sosaltix" > /etc/arch-release

    grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=Sosaltix
    sed -i 's/Arch/Sosaltix/g' /etc/default/grub
    grub-mkconfig -o /boot/grub/grub.cfg
    {enable_services}
    """
    run(f"arch-chroot /mnt /bin/bash -c '{chroot_script}'")

    print(f"\n[COMPLETE] Sosaltix installed. User: {username}")

if __name__ == "__main__":
    if os.getuid() != 0: sys.exit("Need root!")
    install()
