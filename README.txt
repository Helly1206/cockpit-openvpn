cockpit-openvpn v0.80

cockpit-openvpn -- cockpit UI openVPN setup and certificate management
=============== == ======= == ======= ===== === =========== ==========

This plugin not heavily documented yet, but that is probably not nessessary. It's a cockit UI to for
openVPN, based on https://github.com/Nyr/openvpn-install/blob/master/openvpn-install.sh.

The script '/opt/openvpn-cli.py' can also be used on its own without uing the graphical shell. Take into
account that settings need to be entered in JSON format in that case.
When no distribution versino of easy-rsa is available, the script '/opt/easyrsa-install.py' can be used to
install easy-rsa.

The current openVPN settings are stored in an XML databese in /etc/openvpn.xml

It uses cockpit-stdplgin as standard look and feel for this UI.

Setup of openvpn, based on settings and server status.
Certificate creation using easyRSA

That's all for now ...

Please send Comments and Bugreports to hellyrulez@home.nl
