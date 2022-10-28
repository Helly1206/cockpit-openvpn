#!/bin/bash
NAME="openvpn"
LNAME="cockpit-$NAME"
USRDIR="/usr"
OPTDIR="/opt"
CKPTDIR="share/cockpit"
USRLOC="$USRDIR/$CKPTDIR/$NAME"
OPTLOC="$OPTDIR/$NAME"
DEBFOLDER="debian"
PIP_INSTALL="$OPTLOC/pip_install.sh"

minify_install () {
    echo "Installing and compiling files"

    which minify >/dev/null
    if [ $? -ne 0 ]; then
        echo "Minify not installed. Install minify first"
        echo "e.g. by: sudo apt install minify"
        exit
    fi

    if [ ! -d ".$USRLOC" ]; then
        mkdir -p ".$USRLOC"
    fi

    minify -o ".$USRLOC/$NAME.js" "$NAME/$NAME.js"
    #minify -r -o ".$USRLOC" --match="\.css" $NAME
    #minify -r -o ".$USRLOC" --match="\.html" $NAME
    cp "$NAME/$NAME.html" ".$USRLOC/"
    cp "$NAME/manifest.json" ".$USRLOC/"
}

if [ "$EUID" -ne 0 ]
then
	echo "Please execute as root ('sudo install.sh' or 'sudo make install')"
	exit
fi

if [ "$1" == "-u" ] || [ "$1" == "-U" ]
then
	echo "$LNAME uninstall script"

    echo "Removing files"
	if [ -d "$USRLOC" ]; then
        rm -rf "$USRLOC"
    fi
    if [ -d "$OPTLOC" ]; then
        rm -rf "$OPTLOC"
    fi

elif [ "$1" == "-h" ] || [ "$1" == "-H" ]
then
	echo "Usage:"
	echo "  <no argument>: install $NAME"
	echo "  -u/ -U       : uninstall $NAME"
	echo "  -h/ -H       : this help file"
	echo "  -d/ -D       : build debian package"
	echo "  -c/ -C       : Cleanup compiled files in install folder"
elif [ "$1" == "-c" ] || [ "$1" == "-C" ]
then
	echo "$LNAME Deleting compiled files in install folder"
	rm -rf ".$USRDIR"
	rm -f ./*.deb
	rm -rf "$DEBFOLDER"/$LNAME
	rm -rf "$DEBFOLDER"/.debhelper
	rm -f "$DEBFOLDER"/files
	rm -f "$DEBFOLDER"/files.new
	rm -f "$DEBFOLDER"/$LNAME.*
elif [ "$1" == "-d" ] || [ "$1" == "-D" ]
then
	echo "$LNAME build debian package"
	minify_install
	fakeroot debian/rules clean binary
	mv ../*.deb .
else
	echo "$LNAME install script"
    minify_install

    if [ ! -d "$USRLOC" ]; then
        mkdir "$USRLOC"
    fi
    if [ -d ".$USRLOC" ]; then
        cp -r ".$USRLOC/." "$USRLOC/"
    fi

    if [ ! -d "$OPTLOC" ]; then
        mkdir "$OPTLOC"
    fi
    if [ -d ".$OPTLOC" ]; then
        cp -r ".$OPTLOC/." "$OPTLOC/"
    fi

    if [ -f "$PIP_INSTALL" ]; then
        $PIP_INSTALL
    fi
fi
