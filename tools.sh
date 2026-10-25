#!/bin/sh

#version 1.0

ROOT=$PWD

VENV=$ROOT/venv
VPIP=$VENV/bin/pip3

case "$1" in

    venv-install)

        echo 'venv-install'

        REQS=${2:-requirements.txt}
        rm -rf $VENV
        python3 -m venv $VENV
        $VPIP install --upgrade pip setuptools wheel
        $VPIP install -r $REQS
        ;;

    venv-update)

        echo 'venv-update'

        REQS=${2:-requirements.txt}
        $VPIP install -r $REQS
        ;;

    venv-freeze)

        echo 'venv-freeze'

        rm requirements.txt
        $VPIP freeze >> requirements.txt
        ;;

    venv-uninstall)

        echo 'venv-uninstall'

        rm -rf $VENV
        ;;

    pip-update)

        echo 'pip-update'

        $VPIP install --upgrade pip
        ;;

    *)
        echo 'enter option'
        ;;

esac
