#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SERVICE : openvpn-cli.py                              #
#           Commandline interface for automating        #
#           openvpn for commandline or app.             #
#           I. Helwegen 2021                            #
#########################################################

####################### IMPORTS #########################
import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from zipfile import ZipFile
import json
import subprocess
import netifaces
import socket
import random
import string

#########################################################

####################### GLOBALS #########################
VERSION        = "0.84"
OVPNNAME       = "openvpn"
DAEMONOVPN     = OVPNNAME
DAEMONOVPNSRV  = OVPNNAME + "@server"
DAEMONOVPNIPT  = OVPNNAME + "-iptables"
SYSTEMDDIR     = "/etc/systemd/system/"
SYSTEMDOVPNIPT = SYSTEMDDIR + DAEMONOVPNIPT + ".service"
CMDNOTEXIST    = 127
CMDTIMEOUT     = 124
SYSTEMCTL      = "systemctl"
CTLSTART       = SYSTEMCTL + " start"
CTLSTOP        = SYSTEMCTL + " stop"
CTLRELOAD      = SYSTEMCTL + " reload"
CTLRESTART     = SYSTEMCTL + " restart"
CTLENABLE      = SYSTEMCTL + " enable"
CTLDISABLE     = SYSTEMCTL + " disable"
CTLSTATUS      = SYSTEMCTL + " status"
CTLISACTIVE    = SYSTEMCTL + " is-active"
CTLISENABLED   = SYSTEMCTL + " is-enabled"
XML_FILENAME   = OVPNNAME + ".xml"
ENCODING       = 'utf-8'

SERVICE_SYSCTL_CONF      = "/etc/sysctl.d/99-" + OVPNNAME + ".conf"
SERVICE_FORWARD_PROC     = "/proc/sys/net/ipv4/ip_forward"
SERVICE_FORWARD_PROC_IP6 = "/proc/sys/net/ipv6/conf/all/forwarding"
#SERVICE_IPTABLES_CONF = "/etc/network/if-pre-up.d/" + OVPNNAME
SERVICE_OPENVPN_DIR      = "/etc/" + OVPNNAME
SERVICE_OPENVPN_CONF     = SERVICE_OPENVPN_DIR + "/server.conf"
USR_DIR                  = "/usr/share"
TMP_DIR                  = "/tmp"
EASY_RSA_DIR             = USR_DIR + "/easy-rsa"
EASY_RSA_CMD             = EASY_RSA_DIR + "/easyrsa"
EASY_RSA_KEY_DIR         = SERVICE_OPENVPN_DIR + "/pki"

OVPN_PROTOCOL = ["tcp", "udp"]
OVPN_DEVICE   = ["tun", "tap"]
OVPN_LOGLEVEL = {0: "No output except fatal errors",
                 2: "Normal usage output",
                 5: "Log each packet",
                 7: "Debug"}
OVPN_DNS      = {"None": [],
                 "Current system resolvers" : [], # to be resolved later
	             "Google" : ["8.8.8.8","8.8.4.4"],
	             "1.1.1.1" : ["1.1.1.1","1.0.0.1"],
	             "OpenDNS" : ["208.67.222.222","208.67.220.220"],
	             "Quad9" : ["9.9.9.9","149.112.112.112"],
	             "AdGuard" : ["94.140.14.14","94.140.15.15"]}

LISTKEYS       = ["extra_options", "dns", "dns_domains", "wins"]

#########################################################

###################### FUNCTIONS ########################

#########################################################
# Class : shell                                         #
#########################################################
class shell(object):
    def __init__(self):
        pass

    def __del__(self):
        pass

    def runCommand(self, cmd, input = None, timeout = None):
        retval = CMDNOTEXIST, "", ""
        if input:
            input = input.encode("utf-8")
        try:
            if timeout == 0:
                timout = None
            out = subprocess.run(cmd, shell=True, capture_output=True, input = input, timeout = timeout)
            retval = out.returncode, out.stdout.decode("utf-8"), out.stderr.decode("utf-8")
        except subprocess.TimeoutExpired:
            retval = CMDTIMEOUT, "", ""

        return retval

    def command(self, cmd, retcode = 0, input = None, timeout = None, timeoutError = False):
        returncode, stdout, stderr = self.runCommand(cmd, input, timeout)

        if returncode == CMDTIMEOUT and not timeoutError:
            returncode = 0
        if retcode != returncode:
            self.handleError(returncode, stderr)

        return stdout

    def commandExists(self, cmd):
        returncode, stdout, stderr = self.runCommand(cmd)

        return returncode != CMDNOTEXIST

    def handleError(self, returncode, stderr):
        exc = ("External command failed.\n"
               "Command returned: {}\n"
               "Error message:\n{}").format(returncode, stderr)
        raise Exception(exc)

#########################################################
# Class : systemdctl                                    #
#########################################################
class systemdctl(object):
    def __init__(self):
        self.hasSystemd = False
        try:
            self.hasSystemd = self.checkInstalled()
        except Exception as e:
            print("Error reading systemd information")
            print(e)
            exit(1)

    def __del__(self):
        pass

    def available(self):
        return self.hasSystemd

    def start(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLSTART, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

    def stop(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLSTOP, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

    def reload(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLRELOAD, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

    def restart(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLRESTART, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

    def enable(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLENABLE, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

    def disable(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLDISABLE, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

    def status(self, service):
        retval = []
        if self.available():
            cmd = "{} {}".format(CTLSTATUS, service)
            try:
                retcode, stdout, stderr = shell().runCommand(cmd)
                retval = stdout.splitlines()
            except:
                pass
        return retval

    def isActive(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLISACTIVE, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

    def isEnabled(self, service):
        retval = False
        if self.available():
            cmd = "{} {}".format(CTLISENABLED, service)
            try:
                shell().command(cmd)
                retval = True
            except:
                pass
        return retval

################## INTERNAL FUNCTIONS ###################

    def checkInstalled(self):
        return shell().commandExists(SYSTEMCTL)

#########################################################
# Class : database                                      #
#########################################################
class database(object):
    def __init__(self):
        self.db = {}
        if not self.getXMLpath(False):
            # only create xml if super user, otherwise keep empty
            self.createXML()
            self.getXML()
        else:
            self.getXML()

    def __del__(self):
        del self.db
        self.db = {}

    def __call__(self):
        return self.db

    def update(self):
        self.updateXML()

    def reload(self):
        del self.db
        self.db = {}
        self.getXML()

    def bl(self, val):
        retval = False
        try:
            f = float(val)
            if f > 0:
                retval = True
        except:
            if val.lower() == "true" or val.lower() == "yes" or val.lower() == "1":
                retval = True
        return retval

################## INTERNAL FUNCTIONS ###################

    def gettype(self, text, txtype = True):
        try:
            retval = int(text)
        except:
            try:
                retval = float(text)
            except:
                if text:
                    if text.lower() == "false":
                        retval = False
                    elif text.lower() == "true":
                        retval = True
                    elif txtype:
                        retval = text
                    else:
                        retval = ""
                else:
                    retval = ""

        return retval

    def settype(self, element):
        retval = ""
        if type(element) == bool:
            if element:
                retval = "true"
            else:
                retval = "false"
        elif element != None:
            retval = str(element)

        return retval

    def getXML(self):
        XMLpath = self.getXMLpath()
        try:
            tree = ET.parse(XMLpath)
            root = tree.getroot()
            self.db = self.parseKids(root, True)
        except Exception as e:
            print("Error parsing xml file")
            print("Check XML file syntax for errors")
            print(e)
            exit(1)

    def parseKids(self, item, isRoot = False):
        db = {}
        if self.hasKids(item):
            for kid in item:
                if self.hasKids(kid):
                    db[kid.tag] = self.parseKids(kid)
                else:
                    db.update(self.parseKids(kid))
        elif not isRoot:
            db[item.tag] = self.gettype(item.text)
        return db

    def hasKids(self, item):
        retval = False
        for kid in item:
            retval = True
            break
        return retval

    def updateXML(self):
        db = ET.Element('settings')
        pcomment = self.getXMLcomment("settings")
        if pcomment:
            comment = ET.Comment(pcomment)
            db.append(comment)
        self.buildXML(db, self.db)

        XMLpath = self.getXMLpath(dowrite = True)

        with open(XMLpath, "w") as xml_file:
            xml_file.write(self.prettify(db))

    def buildXML(self, xmltree, item):
        if isinstance(item, dict):
            for key, value in item.items():
                kid = ET.SubElement(xmltree, key)
                self.buildXML(kid, value)
        else:
            xmltree.text = self.settype(item)

    def createXML(self):
        #print("Creating new XML file")
        db = ET.Element('settings')
        comment = ET.Comment("This XML file contains the settings for openvpn automation.\n"
        "            Do not edit this file manually!!!")
        db.append(comment)

        XMLpath = self.getNewXMLpath()

        with open(XMLpath, "w") as xml_file:
            xml_file.write(self.prettify(db))

    def getXMLcomment(self, tag):
        comment = ""
        XMLpath = self.getXMLpath()
        with open(XMLpath, 'r') as xml_file:
            content = xml_file.read()
            if tag:
                xmltag = "<{}>".format(tag)
                xmlend = "</{}>".format(tag)
                begin = content.find(xmltag)
                end = content.find(xmlend)
                content = content[begin:end]
            cmttag = "<!--"
            cmtend = "-->"
            begin = content.find(cmttag)
            end = content.find(cmtend)
            if (begin > -1) and (end > -1):
                comment = content[begin+len(cmttag):end]
        return comment

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, ENCODING)
        reparsed = parseString(rough_string)
        return reparsed.toprettyxml(indent="\t").replace('<?xml version="1.0" ?>','<?xml version="1.0" encoding="%s"?>' % ENCODING)

    def getXMLpath(self, doexit = True, dowrite = False):
        etcpath = "/etc/"
        XMLpath = ""
        # first look in etc
        if os.path.isfile(os.path.join(etcpath,XML_FILENAME)):
            XMLpath = os.path.join(etcpath,XML_FILENAME)
            if dowrite and not os.access(XMLpath, os.W_OK):
                print("No valid writable XML file location found")
                print("XML file cannot be written, please run as super user")
                if doexit:
                    exit(1)
        else: # Only allow etc location
            #print("No XML file found")
            if doexit:
                exit(1)
        return XMLpath

    def getNewXMLpath(self):
        etcpath = "/etc/"
        XMLpath = ""
        # first look in etc
        if os.path.exists(etcpath):
            if os.access(etcpath, os.W_OK):
                XMLpath = os.path.join(etcpath,XML_FILENAME)
        if (not XMLpath):
            print("No valid writable XML file location found")
            print("XML file cannot be created, please run as super user")
            exit(1)
        return XMLpath

#########################################################

#########################################################
# Class : sfccli                                        #
#########################################################
class sfccli(object):
    def __init__(self):
        self.name = ""

    def __del__(self):
        pass

    def __str__(self):
        return "{}: commandline interface for openvpn".format(self.name)

    def __repr__(self):
        return self.__str__()

    def run(self, argv):
        if len(os.path.split(argv[0])) > 1:
            self.name = os.path.split(argv[0])[1]
        else:
            self.name = argv[0]

        for arg in argv:
            if arg[0] == "-":
                if arg == "-h" or arg == "--help":
                    self.printHelp()
                    exit()
                elif arg == "-v" or arg == "--version":
                    print(self)
                    print("Version: {}".format(VERSION))
                    exit()
                else:
                    self.parseError(arg)
        if len(argv) < 2:
            self.lst()
        elif argv[1] == "setup":
            opt = argv[1]
            if len(argv) < 3:
                opt += " <json options>"
                self.parseError(opt)
            self.setup(argv[2])
        elif argv[1] == "get":
            opt = argv[1]
            self.get()
        elif argv[1] == "add":
            opt = argv[1]
            if len(argv) < 3:
                opt += " <json options>"
                self.parseError(opt)
            self.cadd(argv[2])
        elif argv[1] == "del":
            opt = argv[1]
            if len(argv) < 3:
                opt += " <json options>"
                self.parseError(opt)
            self.cdel(argv[2])
        elif argv[1] == "download":
            opt = argv[1]
            if len(argv) < 3:
                opt += " <json options>"
                self.parseError(opt)
            self.cdownload(argv[2])
        elif argv[1] == "setup_cert":
            opt = argv[1]
            self.setup_cert()
        elif argv[1] == "getopt":
            opt = argv[1]
            self.getopt()
        elif argv[1] == "ctl":
            opt = argv[1]
            if len(argv) < 3:
                opt += " <name>"
                self.parseError(opt)
            self.ctl(argv[2])
        else:
            self.parseError(argv[1])

    def printHelp(self):
        print(self)
        print("Usage:")
        print("    {} {}".format(self.name, "<argument> <json options>"))
        print("    <arguments>")
        print("        setup         : setup/ update openvpn with <json options>")
        print("        get           : gets current settings")
        print("        add           : add an openvpn certificate <json options>")
        print("                        Options: name       : unique name for certificate")
        print("                                 users      : list of users allowed to download")
        print("        del           : deletes/ revokes an openvpn certificate <json options>")
        print("                        Options: name       : unique name for certificate")
        print("        download      : downloads an openvpn certificate <json options>")
        print("                        Options: name       : unique name for certificate")
        print("        setup_cert    : setup certificates only")
        print("        getopt        : gets options specific for this server")
        print("        ctl           : controls daemon (start, stop, enable, disable, restart,")
        print("                                         reload, isactive, isenabled)")
        print("        <no arguments>: lists current certificates")
        print("")
        print("JSON options may be entered as single JSON string using full name, e.g.")
        print("{}".format(self.name), end="")
        print(" setup \'{\"port\": 1194}\'")
        print("Mind the single quotes to bind the JSON string.")

    def parseError(self, opt = "", opt_msg = True, msg = True):
        print(self)
        if opt_msg:
            print("Invalid option entered")
        if opt:
            print(opt)
        if msg:
            print("Enter '{} -h' for help".format(self.name))
        exit(1)

    def lst(self):
        vals = []
        db = self.getdB()
        #only show clients in this list
        if 'clients' in db():
            if not db()['clients']:
                db()['clients'] = {}
            for key, client in db()['clients'].items():
                val = {}
                val['name'] = client['name']
                if client['users'] == "":
                    val['users'] = []
                else:
                    val['users'] = client['users'].split(",")
                vals.append(val)
        print(json.dumps(vals))

    def setup(self, opt):
        opts = {}
        db = self.getdB()
        if not self.certExists():
            self.setup_cert(db)
        try:
            opts = json.loads(opt)
        except:
            self.parseError("Invalid JSON format")
        try:
            for key, value in opts.items():
                if key in db():
                    if type(db()[key]) == bool:
                        db()[key] = db.bl(value)
                    elif isinstance(value, list):
                        db()[key] = ",".join(value)
                    else: # don't do further type checking to prevent int-float mismatches
                        db()[key] = value
            db.update()
        except:
            self.parseError("Invalid settings format")

        if self.setupOpenVpn(db()):
            self.ctl("enable")
            self.ctl("restart")

    def get(self):
        db = self.getdB()
        #don't show clients in this list
        if 'clients' in db():
            del db()['clients']
        opts = {}
        for key, value in db().items():
            if key in LISTKEYS:
                if value == "":
                    opts[key] = []
                else:
                    opts[key] = value.split(',')
            else:
                opts[key] = value
        print(json.dumps(opts))

    def cadd(self, opt):
        opts = {}
        db = self.getdB()
        if not self.certExists():
            self.parseError("Certificate doesn't exist, setup certificates first!", opt_msg = False)
        try:
            opts = json.loads(opt)
        except:
            self.parseError("Invalid JSON format")
        nameExists = self.checkCertName(db(), opts)
        if nameExists:
            #update users list only
            for key, client in db()['clients'].items():
                if 'name' in client and client['name'] == opts['name']:
                    if 'users' in opts:
                        if isinstance(opts['users'], list):
                            client['users'] = ",".join(opts['users'])
                        else:
                            client['users'] = opts['users']
                    else:
                        client['users'] = ""
                    break
            db.update()
        else:
            #generate user
            if not db()['clients']:
                db()['clients'] = {}
            key = self.getRandomString(16)
            client={}
            client['name'] = opts['name']
            if 'users' in opts:
                client['users'] = opts['users']
            else:
                client['users'] = ""
            db()['clients'][key] = client
            # build-key for the client.
            cmd = "{} --pki-dir={} build-client-full {} nopass".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR, client['name'])
            try:
                shell().command(cmd)
            except:
                self.parseError("Error executing build client command", opt_msg = False, msg = False)
            db.update()
        return

    def cdel(self, opt):
        opts = {}
        db = self.getdB()
        if not self.certExists():
            self.parseError("Certificate doesn't exist, setup certificates first!", opt_msg = False)
        try:
            opts = json.loads(opt)
        except:
            self.parseError("Invalid JSON format")
        if not self.checkCertName(db(), opts):
            self.parseError("Invalid name, certificate doesn't exist", opt_msg = False, msg = False)

        for key, client in db()['clients'].items():
            if 'name' in client and client['name'] == opts['name']:
                db()['clients'].pop(key)
                break
        # revoke-full returns error code 23 when the certificate is revoked.
        cmd = "{} --batch --pki-dir={} revoke {}".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR, opts['name'])
        try:
            shell().command(cmd)
        except:
            pass # Nothing to be done when certificate is revoked

        # Update the control revokation list
        cmd = "{} --batch --pki-dir={} gen-crl".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR)
        try:
            shell().command(cmd)
        except:
            pass # Nothing to be done when certificate is revoked

        ## Delete the files associated with client
        files = [EASY_RSA_KEY_DIR + "/pki/private/" + opts['name'] + ".key",
                 EASY_RSA_KEY_DIR + "/pki/issued/" + opts['name'] + ".crt",
                 EASY_RSA_KEY_DIR + "/pki/reqs/" + opts['name'] + ".req"]
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

        db.update()
        return

    def cdownload(self, opt):
        opts = {}
        db = self.getdB()
        if not self.certExists():
            self.parseError("Certificate doesn't exist, setup certificates first!", opt_msg = False)
        try:
            opts = json.loads(opt)
        except:
            self.parseError("Invalid JSON format")
        if not self.checkCertName(db(), opts):
            self.parseError("Invalid name, certificate doesn't exist", opt_msg = False, msg = False)

        name = opts['name']
        ZipFileLocation = TMP_DIR + "/{}-client.zip".format(name)

        ca = EASY_RSA_KEY_DIR + "/ca.crt";
        cert = EASY_RSA_KEY_DIR + "/issued/{}.crt".format(name);
        key = EASY_RSA_KEY_DIR + "/private/{}.key".format(name);

        zipObj = ZipFile(ZipFileLocation, 'w')
        with open(ca, 'r') as ca_file:
            zipObj.writestr('{}-ca.crt'.format(name), ca_file.read())
        with open(cert, 'r') as cert_file:
            zipObj.writestr('{}-client.crt'.format(name), cert_file.read())
        with open(key, 'r') as key_file:
            zipObj.writestr('{}-client.key'.format(name), key_file.read())
        zipObj.writestr('{}-client.conf'.format(name), "\n".join(self.generateClientConf(name, db())))
        zipObj.writestr('{}-client.ovpn'.format(name), "\n".join(self.generateClientConf(name, db(), ca, cert, key)))
        zipObj.close()

        vals = {}
        vals['zip'] = ZipFileLocation
        print(json.dumps(vals))

    def setup_cert(self, db = None):
        if not db:
            db = self.getdB()
            db()["clients"] = {}
            db.update()
        else:
            db()["clients"] = {}

        if not os.path.isdir(EASY_RSA_KEY_DIR):
            os.mkdir(EASY_RSA_KEY_DIR, mode=0o755)

        # Clean the pki directory
        cmd = "{} --batch --pki-dir={} init-pki".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR)
        try:
            shell().command(cmd)
        except:
            self.parseError("Error executing init-pki command", opt_msg = False, msg = False)

        # Build the CA root certificates
        cmd = "{} --batch --pki-dir={} build-ca nopass".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR)
        try:
            shell().command(cmd)
        except:
            self.parseError("Error executing building ca command", opt_msg = False, msg = False)

        # Create the server certificate/key
        cmd = "{} --batch --pki-dir={} build-server-full {} nopass".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR, self.getHostname())
        try:
            shell().command(cmd)
        except:
            self.parseError("Error executing building server command", opt_msg = False, msg = False)

        # Initialize the CRL by revoking a non-existant cert. Returns the error code
        # 23 when the certificate is revoked.
        cmd = "{} --pki-dir={} gen-crl".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR)
        try:
            shell().command(cmd)
        except:
            pass # Nothing to be done when certificate is revoked

        # Generate Diffie Hellman parameter for the server side.
        cmd = "{} --pki-dir={} gen-dh".format(EASY_RSA_CMD, EASY_RSA_KEY_DIR)
        try:
            shell().command(cmd)
        except:
            self.parseError("Error executing generating dh parameter command", opt_msg = False, msg = False)

        return

    def getopt(self):
        vals = {}
        vals['protocol'] = OVPN_PROTOCOL
        vals['device'] = OVPN_DEVICE
        vals['loglevel'] = list(OVPN_LOGLEVEL.values())
        vals['DNS_server'] = list(OVPN_DNS.keys())
        vals['gateway'] = self.getGateways()
        vals['users'] = self.getLinuxUsers()
        print(json.dumps(vals))

    def ctl(self, opt):
        result = {}
        sctl = systemdctl()
        if not sctl.available():
            print("Reason: systemd unavailable on your distro")
            print("{} cannot automatically restart the {} service".format(self.name, DAEMONOVPN))
            print("You can try it yourself using a command like 'service {} restart'".format(DAEMONOVPN))
            self.parseError()
        if opt == "start":
            result['result'] = sctl.start(DAEMONOVPN)
            if result['result']:
                result['result'] = sctl.start(DAEMONOVPNSRV)
            if result['result']:
                result['result'] = sctl.start(DAEMONOVPNIPT)
        elif opt == "stop":
            result['result'] = sctl.stop(DAEMONOVPN)
            if result['result']:
                result['result'] = sctl.stop(DAEMONOVPNSRV)
            if result['result']:
                result['result'] = sctl.stop(DAEMONOVPNIPT)
        elif opt == "restart":
            result['result'] = sctl.restart(DAEMONOVPN)
            if result['result']:
                result['result'] = sctl.restart(DAEMONOVPNSRV)
            if result['result']:
                result['result'] = sctl.restart(DAEMONOVPNIPT)
        elif opt == "reload":
            result['result'] = sctl.reload(DAEMONOVPN)
            if result['result']:
                result['result'] = sctl.reload(DAEMONOVPNSRV)
            if result['result']:
                result['result'] = sctl.reload(DAEMONOVPNIPT)
        elif opt == "enable":
            result['result'] = sctl.enable(DAEMONOVPN)
            if result['result']:
                result['result'] = sctl.enable(DAEMONOVPNSRV)
            if result['result']:
                result['result'] = sctl.enable(DAEMONOVPNIPT)
        elif opt == "disable":
            result['result'] = sctl.disable(DAEMONOVPN)
            if result['result']:
                result['result'] = sctl.disable(DAEMONOVPNSRV)
            if result['result']:
                result['result'] = sctl.disable(DAEMONOVPNIPT)
        elif opt == "isactive":
            result['result'] = sctl.isActive(DAEMONOVPN)
            if result['result']:
                result['result'] &= sctl.isActive(DAEMONOVPNSRV)
            if result['result']:
                result['result'] &= sctl.isActive(DAEMONOVPNIPT)
        elif opt == "isenabled":
            result['result'] = sctl.isEnabled(DAEMONOVPN)
            if result['result']:
                result['result'] &= sctl.isEnabled(DAEMONOVPNSRV)
            if result['result']:
                result['result'] &= sctl.isActive(DAEMONOVPNIPT)
        else:
            self.parseError("Invalid ctl option: {}".format(opt))
        print(json.dumps(result))

################## INTERNAL FUNCTIONS ###################

    def getdB(self):
        db = database()
        if not db():
            newDb = {}
            newDb["enable_ipv6"] = True
            newDb["port"] = 1194
            newDb["protocol"] = "udp"
            newDb["deviceovpn"] = "tun"
            newDb["compression"] = True
            newDb["duplicate_cn"] = False
            newDb["pam_authentication"] = False
            newDb["extra_options"] = ""
            newDb["loglevel"] = "Normal usage output"
            newDb["vpn_network"] = "10.8.0.0"
            newDb["vpn_mask"] = "255.255.255.0"
            newDb["gateway_interface"] = "wlan0"
            newDb["default_gateway"] = True
            newDb["default_route"] = True
            newDb["client_to_client"] = False
            newDb["dns_server"] = "Google"
            newDb["dns"] = ""
            newDb["dns_domains"] = ""
            newDb["wins"] = ""
            newDb["public_address"] = ""
            newDb["clients"] = ""
            db().update(newDb)
            db.update()
        else:
            if not "enable_ipv6" in db():
                db()["enable_ipv6"] = True
                db.update()
        return db

    def getLog(self, lvalue):
        level = 0
        for key, value in OVPN_LOGLEVEL.items():
            if value == lvalue:
                level = key
                break
        return level

    def getDns(self, key):
        servers = []
        if key == "Current system resolvers":
            lines = []
            if os.path.isfile("/etc/resolv.conf"):
                with open("/etc/resolv.conf", 'r') as file1:
                    lines = file1.readlines()
            contains = False
            for line in lines:
                if "nameserver" in line:
                    contains = True
                    break
            if not contains:
                if os.path.isfile("/run/systemd/resolve/resolv.conf"):
                    with open("/run/systemd/resolve/resolv.conf", 'r') as file1:
                        lines = file1.readlines()
            for line in lines:
                if "nameserver" in line:
                    s = line.find("nameserver") + len ("nameserver")
                    c = line.find("#")
                    if c<0 or c>s:
                        servers.append(line[(s):].split()[0].strip())
        elif key in OVPN_DNS:
            servers = OVPN_DNS[key]
        return servers

    def getGateways(self):
        gateways = netifaces.interfaces()
        return gateways

    def getIp(self, gateway):
        ip = ""
        try:
            addr = netifaces.ifaddresses(gateway)[2]
            ip = addr[0]['addr']
        except:
            pass
        return ip

    def getIpv6(self, gateway):
        ip6 = ""
        try:
            addr = netifaces.ifaddresses(gateway)[10]
            ip6 = addr[0]['addr']
        except:
            pass
        return ip6

    def getMask(self, gateway):
        mask = ""
        try:
            addr = netifaces.ifaddresses(gateway)[2]
            mask = addr[0]['netmask']
        except:
            pass
        return mask

    def getSubnet(self, ip, mask):
        retval = ""
        try:
            retval = ".".join(map(str, [i & m for i,m in zip(map(int, ip.split(".")), map(int, mask.split(".")))]))
        except:
            pass
        return retval

    def getHostname(self):
        hostname = ""
        try:
            with open("/etc/hostname", 'r') as file1:
                hostname = file1.read().strip()
        except:
            pass
        if not hostname:
            hostname = "server"
        return hostname

    def certExists(self):
        retval = False
        if os.path.isfile(EASY_RSA_KEY_DIR + "/private/ca.key") or os.path.isfile(EASY_RSA_KEY_DIR + "/private/" + self.getHostname() + ".key"):
            retval = True
        return retval

    def checkCertName(self, db, opts):
        retval = False
        if not 'name' in opts:
            self.parseError("No certificate name given")
        try:
            for key, client in db['clients'].items():
                if 'name' in client and client['name'] == opts['name']:
                    retval = True
                    break
        except:
            pass #empty list
        return retval

    def getLinuxUsers(self):
        #only lists normal users
        cmd = "grep -E '^UID_MIN|^UID_MAX' /etc/login.defs"
        lines = []
        try:
            lines = shell().command(cmd).splitlines()
        except:
            pass
        uidsel = {}
        for line in lines:
            try:
                l = line.split()
                uidsel[l[0]]=int(l[1])
            except:
                pass
        if not 'UID_MIN' in uidsel:
            uidsel['UID_MIN'] = 1000
        if not 'UID_MAX' in uidsel:
            uidsel['UID_MAX'] = 60000

        cmd = "cat /etc/passwd"
        lines = []
        try:
            lines = shell().command(cmd).splitlines()
        except:
            pass
        users = []
        for line in lines:
            l = line.split(":")
            try:
                uid = int(l[2])
                if (uid >= uidsel['UID_MIN']) and (uid <= uidsel['UID_MAX']):
                    user = l[0]
                    users.append(user)
            except:
                pass

        return users

    def getRandomString(self, length):
        # Random string with the combination of lower and upper case
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(length))

    def setupIpTables(self, db, ip, ip6):
        retval = True
        iptablesPath = "/usr/sbin/iptables"
        ip6tablesPath = "/usr/sbin/ip6tables"

        #get path
        cmd = "command -v iptables"
        try:
            iptablesPath = shell().command(cmd).splitlines()[0]
        except:
            pass
        cmd = "command -v ip6tables"
        try:
            ip6tablesPath = shell().command(cmd).splitlines()[0]
        except:
            pass

        ipTablesConf = []
        ipTablesConf.append("[Unit]")
        ipTablesConf.append("Before=network.target")
        ipTablesConf.append("[Service]")
        ipTablesConf.append("Type=oneshot")
        ipTablesConf.append("ExecStart={} -t nat -A POSTROUTING -s {}/24 ! -d {}/24 -j SNAT --to {}".format(iptablesPath, db['vpn_network'], db['vpn_network'], ip))
        ipTablesConf.append("ExecStart={} -I INPUT -p {} --dport {} -j ACCEPT".format(iptablesPath, db['protocol'], db['port']))
        ipTablesConf.append("ExecStart={} -I FORWARD -s {}/24 -j ACCEPT".format(iptablesPath, db['vpn_network']))
        ipTablesConf.append("ExecStart={} -I FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT".format(iptablesPath))
        ipTablesConf.append("ExecStop={} -t nat -D POSTROUTING -s {}/24 ! -d {}/24 -j SNAT --to {}".format(iptablesPath, db['vpn_network'], db['vpn_network'], ip))
        ipTablesConf.append("ExecStop={} -D INPUT -p {} --dport {} -j ACCEPT".format(iptablesPath, db['protocol'], db['port']))
        ipTablesConf.append("ExecStop={} -D FORWARD -s {}/24 -j ACCEPT".format(iptablesPath, db['vpn_network']))
        ipTablesConf.append("ExecStop={} -D FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT".format(iptablesPath))
        if ip6:
            v6vpn = "fddd:{}:{}:{}::/64".format(db['port'],db['port'],db['port'])
            ipTablesConf.append("ExecStart={} -t nat -A POSTROUTING -s {} ! -d {} -j SNAT --to {}".format(ip6tablesPath, v6vpn, v6vpn, ip6))
            ipTablesConf.append("ExecStart={} -I FORWARD -s {} -j ACCEPT".format(ip6tablesPath, v6vpn))
            ipTablesConf.append("ExecStart={} -I FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT".format(ip6tablesPath))
            ipTablesConf.append("ExecStop={} -t nat -D POSTROUTING -s {} ! -d {} -j SNAT --to {}".format(ip6tablesPath, v6vpn, v6vpn, ip6))
            ipTablesConf.append("ExecStop={} -D FORWARD -s {} -j ACCEPT".format(ip6tablesPath, v6vpn))
            ipTablesConf.append("ExecStop={} -D FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT".format(ip6tablesPath))
        ipTablesConf.append("RemainAfterExit=yes")
        ipTablesConf.append("[Install]")
        ipTablesConf.append("WantedBy=multi-user.target")

        with open(SYSTEMDOVPNIPT, "w") as iptables_file:
            for line in ipTablesConf:
                iptables_file.write(line + "\n")
        # enabling and restarting is done automatically when finished all
        return retval

    def setupOpenVpn(self, db):
        retval = True

        ip = self.getIp(db['gateway_interface'])
        ip6 = ""
        if db["enable_ipv6"]:
            ip6 = self.getIpv6(db['gateway_interface'])

        compression = "comp-lzo"
        if not db['compression']:
            compression = ";" + compression

        pamLoc = "/usr/lib/openvpn/openvpn-plugin-auth-pam.so"
        if not os.path.isfile(pamLoc):
            for path in Path('/usr/lib').rglob('openvpn-plugin-auth-pam.so'):
                pamLoc = path
                break

        pam_authentication = "plugin {} login".format(pamLoc)
        if not db['pam_authentication']:
            pam_authentication = ";" + pam_authentication

        if ip6:
            default_gateway = "push \"redirect-gateway def1 ipv6 bypass-dhcp\""
        else:
            default_gateway = "push \"redirect-gateway def1 bypass-dhcp\""
        if not db['default_gateway']:
            default_gateway = ";" + default_gateway

        mask = self.getMask(db['gateway_interface'])
        static_route="push \"route {} {}\"".format(self.getSubnet(ip, mask), mask)
        if not db['default_route']:
            static_route = ";" + static_route

        client_to_client = "client-to-client"
        if not db['client_to_client']:
            client_to_client = ";" + client_to_client

        persist_tun = "persist-tun"
        if db['deviceovpn'] != "tun":
            persist_tun = ";" + persist_tun

        if db['duplicate_cn']:
            duplicate_cn = "duplicate-cn"
        else:
            duplicate_cn = "ifconfig-pool-persist ipp.txt"

        # Enable net.ipv4.ip_forward and net.ipv6.conf.all.forwarding.
        with open(SERVICE_SYSCTL_CONF, "w") as sysctl_file:
            sysctl_file.write("net.ipv4.ip_forward=1")
            if ip6:
                sysctl_file.write("net.ipv6.conf.all.forwarding=1")
        with open(SERVICE_FORWARD_PROC, "w") as ipfwd_proc:
            ipfwd_proc.write("1")
        if ip6:
            with open(SERVICE_FORWARD_PROC_IP6, "w") as ipfwd_proc:
                ipfwd_proc.write("1")

        self.setupIpTables(db, ip, ip6)

        openVpnConf = []
        openVpnConf.append("port {}".format(db['port']))
        openVpnConf.append("proto {}".format(db['protocol']))
        openVpnConf.append("dev {}".format(db['deviceovpn']))
        openVpnConf.append("ca \"{}/ca.crt\"".format(EASY_RSA_KEY_DIR))
        openVpnConf.append("cert \"{}/issued/{}.crt\"".format(EASY_RSA_KEY_DIR, self.getHostname()))
        openVpnConf.append("key \"{}/private/{}.key\" # This file should be kept secret".format(EASY_RSA_KEY_DIR, self.getHostname()))
        openVpnConf.append("dh \"{}/dh.pem\"".format(EASY_RSA_KEY_DIR))
        openVpnConf.append("topology subnet")
        openVpnConf.append("server {} {}".format(db['vpn_network'], db['vpn_mask']))
        openVpnConf.append(duplicate_cn)
        openVpnConf.append(static_route)
        if ip6:
            openVpnConf.append("server-ipv6 fddd:{}:{}:{}::/64".format(db['port'],db['port'],db['port']))
        openVpnConf.append(default_gateway)

        dns = self.getDns(db['dns_server'])
        if db['dns']:
            dns.extend(db['dns'].split(','))
        for address in dns:
            openVpnConf.append("push \"dhcp-option DNS {}\"".format(address))
        if db['dns_domains']:
            for address in db['dns_domains'].split(','):
                openVpnConf.append("push \"dhcp-option DOMAIN {}\"".format(address))
        if db['wins']:
            for address in db['wins'].split(','):
                openVpnConf.append("push \"dhcp-option WINS {}\"".format(address))

        openVpnConf.append(client_to_client)
        openVpnConf.append("keepalive 10 120")
        openVpnConf.append(compression)
        openVpnConf.append(pam_authentication)
        openVpnConf.append("user nobody")
        openVpnConf.append("group nogroup")
        openVpnConf.append("persist-key")
        openVpnConf.append(persist_tun)
        openVpnConf.append("status /var/log/openvpn-status.log")
        openVpnConf.append("log /var/log/openvpn.log")
        openVpnConf.append("verb {}".format(self.getLog(db['loglevel'])))
        openVpnConf.append("mute 10")
        openVpnConf.append("crl-verify \"{}/crl.pem\"".format(EASY_RSA_KEY_DIR))
        openVpnConf.append("")
        if db['extra_options']:
            openVpnConf.append("# Extra options")
            for extra_option in db['extra_options'].split(','):
                openVpnConf.append(extra_option)
            openVpnConf.append("")

        with open(SERVICE_OPENVPN_CONF, "w") as openvpnconf_file:
            for line in openVpnConf:
                openvpnconf_file.write(line + "\n")

        return retval

    def generateClientConf(self, name, db, ca = None, cert = None, key = None):
        clientConf = []

        persist_tun = "persist-tun"
        if db['deviceovpn'] != "tun":
            persist_tun = ";" + persist_tun

        compression = "comp-lzo"
        if not db['compression']:
            compression = ";" + compression

        pam_authentication = "auth-user-pass"
        if not db['pam_authentication']:
            pam_authentication = ";" + pam_authentication

        clientConf.append("client")
        clientConf.append("remote {} {}".format(db['public_address'], db['port']))
        clientConf.append("proto {}".format(db['protocol']))
        clientConf.append("dev {}".format(db['deviceovpn']))
        clientConf.append("remote-cert-tls server")
        clientConf.append(compression)
        clientConf.append(pam_authentication)
        clientConf.append("persist-key")
        clientConf.append(persist_tun)
        clientConf.append("nobind")
        clientConf.append("resolv-retry infinite")
        clientConf.append("auth-nocache")
        clientConf.append("verb 3")
        clientConf.append("mute 10")

        if ca:
            clientConf.append("<ca>")
            with open(ca, 'r') as ca_file:
                clientConf.append(ca_file.read())
            clientConf.append("</ca>")
        else:
            clientConf.append("ca   {}-ca.crt".format(name))

        if cert:
            clientConf.append("<cert>")
            with open(cert, 'r') as cert_file:
                clientConf.append(cert_file.read())
            clientConf.append("</cert>")
        else:
            clientConf.append("cert {}-client.crt".format(name))

        if key:
            clientConf.append("<key>")
            with open(key, 'r') as key_file:
                clientConf.append(key_file.read())
            clientConf.append("</key>")
        else:
            clientConf.append("key  {}-client.key".format(name))

        clientConf.append("")
        clientConf.append("")

        return clientConf

######################### MAIN ##########################
if __name__ == "__main__":
    sfccli().run(sys.argv)
