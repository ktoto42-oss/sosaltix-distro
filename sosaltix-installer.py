import os, sys, subprocessб, getpass

BASE_PACKAGES = [
    "base", 
    "base-devel",
    "linux", 
    "linux-firmware",
    "linux-headers",
    "networkmanager",
    "grub",
    "efibootmgr",
    "nano",
    "git",
    "fastfetch"
]

GUI_PACKAGES = [
    "sddm",
    "plasma-desktop",
    "plasma-pa",
    "plasma-nm",
    "alacritty",
    "dolphin",
    "ark",
    "firefox"
]

SERVICES = ["NetworkManager", "sddm"]

def run(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        print(f"\n[!] Ошибка: {command}")
        sys.exit(1)

def install():
    print("=== Установка Sosaltix Linux ===")
    
    # 1. Сбор данных
    drive = input("Диск (напр. /dev/sda): ")
    username = input("Имя пользователя: ")
    password = getpass.getpass("Пароль пользователя: ")
    root_password = getpass.getpass("Пароль root: ")
    
    # 2. Разметка и форматирование
    print("--> Подготовка диска...")
    run(f"parted -s {drive} mklabel gpt")
    run(f"parted -s {drive} mkpart primary fat32 1MiB 513MiB")
    run(f"parted -s {drive} set 1 esp on")
    run(f"parted -s {drive} mkpart primary ext4 513MiB 100%")

    p1 = f"{drive}p1" if "nvme" in drive else f"{drive}1"
    p2 = f"{drive}p2" if "nvme" in drive else f"{drive}2"
    
    run(f"mkfs.vfat -F32 {p1} > /dev/null")
    run(f"mkfs.ext4 -F {p2} > /dev/null")

    # 3. Установка базы
    run(f"mount {p2} /mnt")
    os.makedirs("/mnt/boot", exist_ok=True)
    run(f"mount {p1} /mnt/boot")
    
    print("--> Установка пакетов...")
    all_pkgs = " ".join(BASE_PACKAGES + GUI_PACKAGES)
    run(f"pacstrap -K /mnt {all_pkgs}")
    run("genfstab -U /mnt >> /mnt/etc/fstab")

    # 4. Настройка внутри chroot
    print("--> Финальная настройка...")
    
    # Подготовка команд для демонов
    enable_services = " ".join([f"systemctl enable {s}" for s in SERVICES])
    
    chroot_script = f"""
    # Локализация
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
    echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen
    locale-gen
    echo "LANG=ru_RU.UTF-8" > /etc/locale.conf

    # Часовой пояс и сеть
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
    echo "Sosaltix" > /etc/hostname

    # Пользователи
    echo "root:{root_password}" | chpasswd
    useradd -m -G wheel -s /bin/bash {username}
    echo "{username}:{password}" | chpasswd
    echo "%wheel ALL=(ALL) ALL" > /etc/sudoers.d/wheel

    # Загрузчик и сервисы
    grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=Sosaltix
    grub-mkconfig -o /boot/grub/grub.cfg
    {enable_services}
    """
    
    run(f"arch-chroot /mnt /bin/bash -c '{chroot_script}'")

    print(f"\n[ГОТОВО] Sosaltix установлена. Пользователь: {username}")

if __name__ == "__main__":
    if os.getuid() != 0: sys.exit("Нужен root!")
    install()