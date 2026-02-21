import os
import sys
import getpass
import subprocess

base_packages = [
    "linux",
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
        return False
    return True

def install_with_retry(packages, target_dir):
    max_retries = 3
    retry_count = 0
    all_pkgs = " ".join(packages)
    
    while retry_count < max_retries:
        if retry_count > 0:
            print(f"\n=== Retry attempt {retry_count}/{max_retries-1} ===")
            time.sleep(3)
        
        print(f"Installing packages (attempt {retry_count + 1}/{max_retries})...")
        success = run(f"pacstrap -K {target_dir} {all_pkgs}", ignore_errors=True)
        
        if success:
            print("Packages installed successfully!")
            return True
        else:
            retry_count += 1
            print(f"\n[!] Installation failed. {'Retrying...' if retry_count < max_retries else 'Maximum retries reached.'}")
    
    return False

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
    os.makedirs("/mnt/boot/efi", exist_ok=True)
    run(f"mount {p1} /mnt/boot/efi")

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
    enable_services = " && ".join([f"systemctl enable {s}" for s in services])
    
    chroot_commands = [
        f'echo "en_US.UTF-8 UTF-8" > /etc/locale.gen',
        f'echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen',
        f'locale-gen',
        f'echo "LANG=ru_RU.UTF-8" > /etc/locale.conf',
        f'ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime',
        f'echo "Sosaltix" > /etc/hostname',
        f'passwd root',
        f'"{root_password}"',
        f'useradd -m -G wheel -s /bin/bash {username}',
        f'passwd "{username}',
        f'"{user_password}"',
        f'echo "%wheel ALL=(ALL) ALL" > /etc/sudoers.d/wheel',
        f'grub-install "{drive}" --bootloader-id=Sosaltix',
        f'grub-mkconfig -o /boot/grub/grub.cfg',
        enable_services
    ]
    
    chroot_cmd = " && ".join(chroot_commands)
    run(f'arch-chroot /mnt /bin/bash -c "{chroot_cmd}"')

    print(f"\n[COMPLETE] Sosaltix installed. User: {username}")
    print("You can now reboot into your new system.")



if __name__ == "__main__":
    if os.getuid() != 0: sys.exit("Need root!")
    install()