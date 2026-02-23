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
    
    chroot_commands.append("mkdir -p /usr/share/sosaltix")
    
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
    
    chroot_commands.append("sed -i 's/Arch Linux/Sosaltix Linux/g' /etc/pacman.conf")
    chroot_commands.append("sed -i 's/Arch/Sosaltix/g' /etc/pacman.conf")
    chroot_commands.append("sed -i 's/Arch Linux/Sosaltix Linux/g' /boot/grub/grub.cfg")
    
    for service in services:
        chroot_commands.append(f"systemctl enable {service}")
    
    for cmd in chroot_commands:
        print(f"Executing: {cmd[:50]}..." if len(cmd) > 50 else f"Executing: {cmd}")
        run(f'arch-chroot /mnt /bin/bash -c "{cmd}"')

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
