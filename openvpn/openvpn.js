/*********************************************************
 * SCRIPT : openvpn.js                                   *
 *          Javascript for openvpn Cockpit               *
 *          web-gui                                      *
 *          I. Helwegen 2020                             *
 *********************************************************/

////////////////////
// Common classes //
////////////////////

class ovpnSettings {
    constructor(el) {
        this.el = el;
        this.name = "OpenVPN settings";
        this.pane = new tabPane(this, el, this.name);
        this.update = [];
        this.btnUpdate = null;
    }

    displayContent(el) {
        this.displaySettings();
        this.getSettings();
    }

    displaySettings(text = "") {
        this.pane.dispose();
        this.pane.build(text, true);
        this.pane.getTitle().innerHTML = this.name.charAt(0).toUpperCase() + this.name.slice(1);
        this.btnUpdate = this.pane.addButton("Update", "Update", this.btnUpdateCallback, true, (Object.keys(this.update).length == 0), false);
    }

    getSettings(callback) {
        var optCb = function(oData) {
            var getCb = function(aData) {
                this.pane.setButtonDisabled(this.btnUpdate, (Object.keys(this.update).length == 0));
                var ioData = JSON.parse(oData);
                var iaData = JSON.parse(aData);
                this.buildEditForm(iaData, ioData);
            }
            runCmd.call(this, getCb, ['get']);
        }
        this.update = [];
        runCmd.call(this, optCb, ['getopt']);
    }

    buildEditForm(aData, oData) {
        var settingsCallback = function(param, value) {
            this.update = buildOpts(this.pane.getSettingsEditForm().getData(), aData);
            this.pane.setButtonDisabled(this.btnUpdate, (Object.keys(this.update).length == 0));
        }
        //aData={"port": 1194, "protocol": "udp", "deviceovpn": "tun", "compression": true,
        //"duplicate_cn": false, "pam_authentication": false, "extra_options": "",
        //"loglevel": "Errors and info", "vpn_network": "10.8.0.0", "vpn_mask": "255.255.255.0",
        //"gateway_interface": "wlan0", "default_gateway": true, "default_route": true,
        //"client_to_client": false, "dns_server": "Google", "dns": "", "dns_domains": "",
        //"wins": "", "public_address": ""}
        //oData={"protocol": ["tcp", "udp"], "device": ["tun", "tap"],
        //"loglevel": ["No output except fatal errors", "Normal usage output", "Log each packet", "Debug"],
        //"DNS_server": ["None", "Current system resolvers", "Google", "1.1.1.1", "OpenDNS", "Quad9", "AdGuard"],
        //"gateway": ["lo", "wlan0", "eth0"],  "users": ["xxxx"]}
        var dlgData = [{
                param: "port",
                text: "Port",
                value: aData.port,
                type: "number",
                min: 0,
                max: 30000,
                step: 1,
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "OpenVPN internal port."
            }, {
                param: "protocol",
                text: "Protocol",
                value: aData.protocol,
                type: "select",
                opts: oData.protocol,
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Protocol to use for OpenVPN."
            }, {
                param: "deviceovpn",
                text: "Device",
                value: aData.deviceovpn,
                type: "select",
                opts: oData.device,
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "OpenVPN device."
            }, {
                param: "compression",
                text: "Compression",
                value: aData.compression,
                type: "boolean",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Use data compression."
            }, {
                param: "duplicate_cn",
                text: "Duplicate CN",
                value: aData.duplicate_cn,
                type: "boolean",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Simultaneous login per CN."
            }, {
                param: "pam_authentication",
                text: "PAM authentication",
                value: aData.pam_authentication,
                type: "boolean",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Authenticate with server using username/password (client certificate and key are still required)."
            }, {
                param: "extra_options",
                text: "Extra options",
                value: aData.extra_options,
                type: "multi",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Extra OpenVPN options (separate by ,)"
            }, {
                param: "loglevel",
                text: "Log level",
                value: aData.loglevel,
                type: "select",
                opts: oData.loglevel,
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Logging level."
            }, {
                param: "vpn_network",
                text: "VPN network",
                value: aData.vpn_network,
                type: "ip",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                showmask: false,
                comment: "VPN network"
            }, {
                param: "vpn_mask",
                text: "VPN mask",
                value: aData.vpn_mask,
                type: "ip",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                showmask: false,
                comment: "VPN network mask"
            }, {
                param: "gateway_interface",
                text: "Gateway interface",
                value: aData.gateway_interface,
                type: "select",
                opts: oData.gateway,
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Gateway interface for OpenVPN connection."
            }, {
                param: "default_gateway",
                text: "Default gateway",
                value: aData.default_gateway,
                type: "boolean",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "If enabled, this directive will configure all clients to redirect their default network gateway through the VPN."
            }, {
                param: "default_route",
                text: "Default route",
                value: aData.default_route,
                type: "boolean",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "If enabled, a static route to the private subnet is configured on all clients."
            }, {
                param: "client_to_client",
                text: "Client to client",
                value: aData.client_to_client,
                type: "boolean",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Allow client to client communication."
            }, {
                param: "dns_server",
                text: "DNS server",
                value: aData.dns_server,
                type: "select",
                opts: oData.DNS_server,
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "Default DNS server to use."
            }, {
                param: "dns",
                text: "DNS servers",
                value: aData.dns,
                type: "multiip",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                showmask: false,
                comment: "Specific DNS server(s)"
            }, {
                param: "dns_domains",
                text: "DNS domains",
                value: aData.dns_domains,
                type: "multiip",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                showmask: false,
                comment: "DNS search domain(s)"
            }, {
                param: "wins",
                text: "WINS servers",
                value: aData.wins,
                type: "multiip",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                showmask: false,
                comment: "WINS server(s)"
            }, {
                param: "public_address",
                text: "Public address",
                value: aData.public_address,
                type: "text",
                onchange: settingsCallback,
                disabled: false,
                readonly: false,
                comment: "This is the address which external clients can connect to your VPN with. This is automatically used in the generated configuration."
            }
        ];
        this.pane.getSettingsEditForm().setData(dlgData);
    }

    btnUpdateCallback() {
        var cbYes = function() {
            var settings = {};
            settings = this.update;
            this.pane.dispose();
            this.displaySettings("Updating settings...");
            runCmd.call(this, this.getSettings, ['setup'], settings);
        };
        if (Object.keys(this.update).length > 0) {
            var txt = "Are you sure to update settings and restart OpenVPN services?"
            new confirmDialog(this, "Update settings", txt, cbYes);
        } else {
            new msgBox(this, "No settings changed", "No update required!");
        }
    }
}

class ovpnCertificates {
    constructor(el) {
        this.el = el;
        this.name = "OpenVPN certificates";
        this.pane = new tabPane(this, el, this.name);
        this.dropdownContent = [
            {name : "Download", disable: "!allowed", disableValue: false, callback: this.download},
            {name : "Delete", disable: "!allowed", disableValue: false, callback: this.delete}
        ];
        this.certs = [];
    }

    displayContent(el) {
        this.pane.dispose();
        this.pane.build();
        this.pane.getTitle().innerHTML = this.name.charAt(0).toUpperCase() + this.name.slice(1);
        this.pane.addButton("add", "Add", this.addCerificate, true, false, false);
        this.pane.getTable().setOnClick(this.tableClickCallback);
        this.pane.getTable().setDropDown(this.dropdownContent);
        this.getCertificates();
    }

    getCertificates() {
        var cbThen = function(user) {
            var cb = function(data) {
                var lData = JSON.parse(data);
                this.certs = [];
                lData.forEach(datum => {
                    if (datum.users.length > 0) {
                        datum['!allowed'] = ((datum.users.includes(user.name)) || (user.name == "root"));
                    } else {
                        datum['!allowed'] = true;
                    }
                    this.certs.push(datum.name);
                });
                this.pane.getTable().setData(lData);
            }
            runCmd.call(this, cb);
        }
        cockpit.user().then(cbThen.bind(this));
    }

    addCerificate() {
        var jData = {};
        jData.name = "";
        jData.users = [];
        this.pane.disposeSpinner();
        this.buildEditDialog(jData, true);

    }

    tableClickCallback(data) {
        this.pane.getTable().loadingDone();
        this.pane.disposeSpinner();
        this.buildEditDialog(data, false);
    }

    buildEditDialog(aData, newCert) {
        if (!aData.users) {
            aData.users = [];
        }
        var optCb = function(oData) {
            var users = JSON.parse(oData).users;
            var dlgData = [{
                    param: "users",
                    text: "Users",
                    value: aData.users,
                    type: "disk",
                    opts: users,
                    optslabel: [],
                    optssingle: false,
                    disabled: false,
                    readonly: false,
                    labelonly: false,
                    comment: "Associated user(s)"
                }
            ];
            var title = "";
            if (newCert) {
                dlgData.splice(0, 0, {
                    param: "name",
                    text: "Name",
                    value: this.tryName(aData.users),
                    type: "text",
                    disabled: false,
                    readonly: false,
                    comment: "Enter a unique name for the certificate"
                });
                title = "Add certificate";
            } else {
                title = "Edit certificate: " + aData.name;
            }
            var dialog = new editDialog(this);
            var cbOk = function(rData) {
                if ('name' in aData) {
                    aData.name = aData.name.replace(/[^a-zA-Z0-9]/g,'_');
                }
                if ('name' in rData) {
                    rData.name = rData.name.replace(/[^a-zA-Z0-9]/g,'_');
                }
                this.addEdit(rData, aData, newCert);
            }
            dialog.build(title, dlgData, cbOk);
        }
        runCmd.call(this, optCb, ['getopt']);
    }

    tryName(users) {
        var name = "";
        var baseName = "";
        var unique = false;
        var i = 1;
        if (users.length > 0) {
            baseName = users.join("_");
        } else {
            baseName = "myCertificate";
        }
        name = baseName;
        while (!unique) {
            if (this.certs.includes(name)) {
                name = baseName + i.toString();
                i++;
            } else {
                unique = true;
            }
        }
        return name;
    }

    addEdit(rData, aData, newCert) {
        var opts = {};
        var name = "";
        if (newCert) {
            name = rData.name;
            aData = {};
        } else {
            name = aData.name;
            rData.name = name;
            aData.name = "";
        }
        opts = buildOpts(rData, aData);
        if (name) {
            if ((newCert) && (this.certs.includes(name))) {
                new msgBox(this, "Existing certificate " + name, "Please enter a unique name for the certificate");
            } else if (opts.length == 0) {
                new msgBox(this, "No changes to the certificate", "Certificate not edited");
            } else {
                var cbYes = function() {
                    this.pane.showSpinner("Adding/ editing...");
                    runCmd.call(this, this.displayContent, ["add"], opts);
                };
                var txt = "";
                if (newCert) {
                    txt = "Are you sure to add " + name + " as certificate?";
                } else {
                    txt = "Are you sure to edit " + name + " as certificate?";
                }
                new confirmDialog(this, "Add/ edit certificate " + name, txt, cbYes);
            }
        } else {
            new msgBox(this, "Empty certificate name", "Please enter a valid name for the certificate");
        }
    }

    download(data) {
        var cbDl = function(result) {
            var iResult = JSON.parse(result);
            var filename = "";
            var zipname = "";
            if ('zip' in iResult) {
                filename = iResult.zip;
            }
            zipname = filename.substring(filename.lastIndexOf('/')+1);
            cockpit.file(filename, { binary: true }).read()
            .done(function (content, tag) {
                this.downloadFile(zipname, btoa(String.fromCharCode.apply(null, content)));
            }.bind(this))
            .fail(function (error) {
                new msgBox(this, "Download failed", "Command error: " + error.message + ", " + error.problem);
            }.bind(this));
            this.getCertificates();
        }
        this.pane.showSpinner("Downloading...");
        runCmd.call(this, cbDl, ["download"], {"name": data.name});
    }

    downloadFile(filename, data) {
        var element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;base64,' + data);
        element.setAttribute('download', filename);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    }

    delete(data) {
        var cbYes = function() {
            this.pane.showSpinner("Deleting...");
            runCmd.call(this, this.getCertificates, ["del"], {"name": data.name});
        };
        var txt = "Are you sure to delete " + data.name + "?" + "<br>" +
                    "This certificate is not valid anymore!"
        new confirmDialog(this, "Delete " + data.name, txt, cbYes);
    }
}

/////////////////////
// Common functions //
//////////////////////

function runCmd(callback, args = [], json = null, cmd = "/opt/openvpn/openvpn-cli.py") {
    var cbDone = function(data) {
        callback.call(this, data);
    };
    var cbFail = function(message, data) {
        callback.call(this, "[]");
        new msgBox(this, "OpenVPN command failed", "Command error: " + (data ? data : message + "<br>Please check the log file"));
    };
    var command = [cmd];
    command = command.concat(args);
    if (json) {
        command = command.concat(JSON.stringify(json));
    }
    return cockpit.spawn(command, { err: "out", superuser: "require" })
        .done(cbDone.bind(this))
        .fail(cbFail.bind(this));
}

function buildOpts(data, refData = {}, exclude = []) {
    var opts = {};

    for (let key in data) {
        let addKey = true;
        if (exclude.includes(key)) {
            addKey = false;
        } else if (key in refData) {
            if (data2str(data[key]) == data2str(refData[key])) {
                addKey = false;
            }
        }
        if (addKey) {
            opts[key] = data[key];
        }
    }
    return opts;
}

function data2str(data) {
    var str = "";
    if (Array.isArray(data)) {
        str = data.map(s => s.trim()).join(",");
    } else {
        str = data.toString();
    }
    return str;
}

function cs2arr(data, force = true) {
    var arr = [];
    if ((force) || (data.includes(","))) {
        arr = data.split(",").map(s => s.trim());
    } else {
        arr = data;
    }

    return arr;
}

///////////////////////////
// Tab display functions //
///////////////////////////

function clickTab() {
    // remove active class from all elements
    document.querySelectorAll('[role="presentation"]').forEach(function (el) {
        el.classList.remove("active");
        el.getElementsByTagName("a")[0].setAttribute("tabindex", -1);
        el.getElementsByTagName("a")[0].setAttribute("aria-selected", false);
    });

    // add class 'active' to this element
    this.classList.add("active")
    this.getElementsByTagName("a")[0].setAttribute("aria-selected", true);
    this.getElementsByTagName("a")[0].removeAttribute("tabindex");

    // hide all contents
    document.querySelectorAll('[role="tabpanel"]').forEach(function (el) {
        el.setAttribute("aria-hidden", true);
        el.classList.remove("active");
        el.classList.remove("in");
    });

    // show current contents
    contentId = this.getElementsByTagName("a")[0].getAttribute("aria-controls");
    el = document.getElementById(contentId);

    if (el != null) {
        el.setAttribute("aria-hidden", false);
        el.classList.add("active");
        el.classList.add("in");
        displayContent(el);
    }
}

function displayContent(el) {
    if (el.id.search("settings") >= 0) {
        let Settings = new ovpnSettings(el);
        Settings.displayContent();
    } else if (el.id.search("cert") >= 0) {
        let Cert = new ovpnCertificates(el);
        Cert.displayContent();
    } else if (el.id.search("log") >= 0) {
        let Logger = new logger(el, "/var/log/openvpn.log", true);
        Logger.displayContent();
    } else if (el.id.search("status") >= 0) {
        let Status = new logger(el, "/var/log/openvpn-status.log", true, false, false);
        Status.displayContent();
    }
}

function displayFirstPane() {
    displayContent(document.querySelectorAll('[role="tabpanel"]')[0]);
}

document.querySelectorAll('[role="presentation"]').forEach(function (el) {
    el.addEventListener("click", clickTab);
});

displayFirstPane();

// Send a 'init' message.  This tells integration tests that we are ready to go
cockpit.transport.wait(function() { });
