SHELL:=/bin/bash
VERSION=3.11.5
PROJECT=peter-art
VENV=${PROJECT}-${VERSION}
VENV_DIR=$(shell pyenv root)/versions/${VENV}/bin/activate
PYTHON=${VENV_DIR}/bin/python

setup:
	brew install pyenv pyenv-virtualenv
	pyenv install ${VERSION}
	exec $SHELL
	eval "$(pyenv init -)"
	eval "$(pyenv virtualenv-init -)"

shell:
	pyenv virtualenv ${VENV}

activate:
	. ${VENV_DIR} 

install:
	pip install -r requirements.txt



