import os
import sys
import getpass
import subprocess
import time

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

def run(command, ignore_errors=False):
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"\n[!] Error: {command}")
            print(f"Error: {e}")
        return False

def install_with_retry(packages, target_dir):
    max_retries = 100
    retry_count = 0
    all_pkgs = " ".join(packages)
    
    while retry_count < max_retries:
        if retry_count > 0:
            print(f"\n=== Retry attempt {retry_count}/{max_retries-1} ===")
            time.sleep(3)
        
        print(f"Installing packages (attempt {retry_count + 1}/{max_retries})...")
        success = run(f"pacstrap -K {target_dir} {all_pkgs}")
        
        if success:
            print("Packages installed successfully!")
            return True
        else:
            retry_count += 1
            print(f"\n[!] Installation failed. {'Retrying...' if retry_count < max_retries else 'Maximum retries reached.'}")
    
    return False

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

    p1 = f"{drive}p1" if "nvme" in drive or "mmcblk" in drive else f"{drive}1"
    p2 = f"{drive}p2" if "nvme" in drive or "mmcblk" in drive else f"{drive}2"

    run(f"mkfs.vfat -F32 {p1}")
    run(f"mkfs.ext4 -F {p2}")

    run(f"mount {p2} /mnt")
    os.makedirs("/mnt/boot/efi", exist_ok=True)
    run(f"mount {p1} /mnt/boot/efi")

    print("=== Installation packages === ")
    all_pkgs = base_packages + kde_packages

    if not install_with_retry(all_pkgs, "/mnt"):
        print("\n[!] Package installation failed after maximum retries.")
        run("umount -R /mnt", ignore_errors=True)
        sys.exit(1)
    
    run("genfstab -U /mnt >> /mnt/etc/fstab")

    print("=== Final setup with Sosaltix branding ===")
    
    # Основные команды настройки
    chroot_commands = [
        # Локализация
        "echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen",
        "echo 'ru_RU.UTF-8 UTF-8' >> /etc/locale.gen",
        "locale-gen",
        "echo 'LANG=ru_RU.UTF-8' > /etc/locale.conf",
        
        # Время и хост
        "ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime",
        "echo 'Sosaltix' > /etc/hostname",
        
        # Пароли и пользователи
        f"echo 'root:{root_password}' | chpasswd",
        f"useradd -m -G wheel -s /bin/bash {username}",
        f"echo '{username}:{user_password}' | chpasswd",
        "echo '%wheel ALL=(ALL) ALL' > /etc/sudoers.d/wheel",
        
        # Grub
        f"grub-install {drive} --bootloader-id=Sosaltix",
        "grub-mkconfig -o /boot/grub/grub.cfg",
    ]
    
    # Создаем файлы через отдельные команды, чтобы избежать проблем с кавычками
    os_release_content = '''cat > /etc/os-release << 'EOF'
NAME="Sosaltix Linux"
PRETTY_NAME="Sosaltix Linux"
ID=sosaltix
ID_LIKE=arch
BUILD_ID=rolling
ANSI_COLOR="38;2;23;147;209"
HOME_URL="https://sosaltix.org"
DOCUMENTATION_URL="https://wiki.sosaltix.org"
SUPPORT_URL="https://support.sosaltix.org"
BUG_REPORT_URL="https://bugs.sosaltix.org"
LOGO=sosaltix
EOF'''
    chroot_commands.append(os_release_content)
    
    issue_content = '''cat > /etc/issue << 'EOF'
Sosaltix Linux \\r (\\l)

EOF'''
    chroot_commands.append(issue_content)
    
    motd_content = '''cat > /etc/motd << 'EOF'
Welcome to Sosaltix Linux!
Documentation: https://wiki.sosaltix.org

EOF'''
    chroot_commands.append(motd_content)
    
    sddm_content = f'''cat > /etc/sddm.conf << 'EOF'
[Theme]
Current=breeze

[General]
HaltCommand=/usr/bin/systemctl poweroff
RebootCommand=/usr/bin/systemctl reboot

[Users]
DefaultUser={username}
EOF'''
    chroot_commands.append(sddm_content)
    
    # Создание директории
    chroot_commands.append("mkdir -p /usr/share/sosaltix")
    
    # Настройка fastfetch
    fastfetch_content = f'''mkdir -p /home/{username}/.config/fastfetch
cat > /home/{username}/.config/fastfetch/config.jsonc << 'EOF'
{{
  "logo": {{
    "source": "sosaltix",
    "type": "builtin"
  }},
  "display": {{
    "separator": "➜",
    "color": {{
      "keys": "cyan",
      "title": "blue"
    }}
  }}
}}
EOF
chown -R {username}:{username} /home/{username}/.config'''
    chroot_commands.append(fastfetch_content)
    
    # Настройка bashrc
    bashrc_content = f'''echo '
# Sosaltix welcome message
if [ -f /etc/motd ]; then
    cat /etc/motd
fi

# Custom prompt
PS1="\\[\\033[01;34m\\][Sosaltix\\[\\033[01;37m\\] \\u\\[\\033[01;34m\\] \\w\\[\\033[01;34m\\]]\\[\\033[00m\\] \\$ "
' >> /home/{username}/.bashrc
chown {username}:{username} /home/{username}/.bashrc'''
    chroot_commands.append(bashrc_content)
    
    # Настройка pacman
    chroot_commands.append("sed -i 's/Arch Linux/Sosaltix Linux/g' /etc/pacman.conf")
    chroot_commands.append("sed -i 's/Arch/Sosaltix/g' /etc/pacman.conf")
    
    # Настройка grub
    chroot_commands.append("sed -i 's/Arch Linux/Sosaltix Linux/g' /boot/grub/grub.cfg")
    
    # Включаем сервисы
    for service in services:
        chroot_commands.append(f"systemctl enable {service}")
    
    # Выполняем все команды
    for i, cmd in enumerate(chroot_commands, 1):
        print(f"Executing command {i}/{len(chroot_commands)}")
        run(f'arch-chroot /mnt /bin/bash -c "{cmd}"')

    # Создаем файл с информацией о системе (вне chroot)
    with open("/mnt/etc/sosaltix-release", "w") as f:
        f.write("Sosaltix Linux release 2024 (Rolling)\n")

    print(f"\n=== Sosaltix Linux successfully installed! ===")
    print(f"User: {username}")
    print(f"Hostname: Sosaltix")
    print("\nSystem has been fully rebranded from Arch to Sosaltix.")
    print("\nTo reboot, run: umount -R /mnt && reboot")

if __name__ == "__main__":
    if os.getuid() != 0:
        sys.exit("Need root!")
    install()
