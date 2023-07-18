# initial setup script for fresh raspberry pi (besides cloning the repo, etc.)
sudo apt update
sudo apt upgrade
sudo apt install -y apt-transport-https curl python3 fonts-noto python3-pip pigpio libopenjp2-7 python3-venv gsfonts xrdp
sudo sed -i s/#dtparam=spi=on/dtparam=spi=on/ /boot/config.txt  # enables SPI
curl -sL https://dtcooper.github.io/raspotify/install.sh | sh
sudo pip3 install -r ../requirements.txt
sudo pip3 install RPi.GPIO
echo "Installation complete. Manual steps below:"
echo "1. Configure raspotify:"
echo "   - Config file is at /etc/raspotify/conf"
echo "   - Guide at https://github.com/dtcooper/raspotify/wiki/Basic-Setup-Guide"
echo "   - After manual configuration, run sudo systemctl restart raspotify to test"
echo "2. Configure .env file:"
echo "   - located in this repo, see README.md for more info"
echo "3. sudo reboot then reconnect"
echo "4. Run beba /your/path/to/startup.sh to authenticate + verify everything is working"
echo "5. Configure .bashrc to launch beba on boot"
echo "   - chmod a+x /your/path/to/startup.sh"
echo "   - edit the file ~/.bashrc"
echo "   - add a line at bottom to sudo /your/path/to/startup.sh"
echo "6. Configure raspberry pi to launch shell on boot"
echo "   - sudo raspi-config"
echo "   - System Options -> Boot -> Console Autologin"
echo "7. sudo reboot"