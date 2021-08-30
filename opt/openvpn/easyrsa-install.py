#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SERVICE : easyrsa-install.py                          #
#           Script for installing easyRSA for openVPN   #
#                                                       #
#           I. Helwegen 2021                            #
#########################################################

####################### IMPORTS #########################
import sys
import os
import urllib.request
import tarfile
from shutil import rmtree

#########################################################

####################### GLOBALS #########################
#helly@helly-laptop:/usr/share/easy-rsa$

EASY_RSA_VERSION      = "3.0.8"
USR_DIR               = "/usr/share"
EASY_RSA_DIR          = USR_DIR + "/easy-rsa"
EASY_RSA_CMD          = EASY_RSA_DIR + "/easyrsa"
EASY_RSA_FILE         = "EasyRSA-" + EASY_RSA_VERSION
EASY_RSA_INSTDIR      = USR_DIR + "/" + EASY_RSA_FILE
EASY_RSA_TGZ_FILE     = EASY_RSA_FILE + ".tgz"
EASY_RSA_URL          = "https://github.com/OpenVPN/easy-rsa/releases/download/v" + EASY_RSA_VERSION + "/" + EASY_RSA_TGZ_FILE

#########################################################

######################### MAIN ##########################
if __name__ == "__main__":
    if os.getuid() != 0:
        print("This program needs to be run as super user")
        print("try: sudo easyrsa-install.py")
        exit(2)

    if len(sys.argv) > 1 and (sys.argv[1].lower() == '-u' or sys.argv[1].lower() == "--uninstall"):
        if os.path.isfile(EASY_RSA_CMD):
            print("Uninstalling Easy RSA v" + EASY_RSA_VERSION)
            rmtree(EASY_RSA_DIR)
        else:
            print("Easy RSA v" + EASY_RSA_VERSION + " not installed, nothing to uninstall")
    else:
        if not os.path.isfile(EASY_RSA_CMD):
            print("Installing Easy RSA v" + EASY_RSA_VERSION)
            ftpstream = urllib.request.urlopen(EASY_RSA_URL)
            thetarfile = tarfile.open(fileobj=ftpstream, mode="r|gz")
            thetarfile.extractall(USR_DIR)
            if os.path.isdir(EASY_RSA_INSTDIR):
                if os.path.isdir(EASY_RSA_DIR):
                    rmtree(EASY_RSA_DIR)
                os.rename(EASY_RSA_INSTDIR, EASY_RSA_DIR)
        else:
            print("Easy RSA v" + EASY_RSA_VERSION + " already installed")
    print("Ready")
