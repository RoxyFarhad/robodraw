#!/bin/bash
VERSION="3.11.5"
PROJECT="peter-art"
VENV="${PROJECT}-${VERSION}"

brew install pyenv pyenv-virtualenv
pyenv install ${VERSION} 

PYENV_ROOT=eval $(pyenv root)
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

VENV_DIR=${PYENV_ROOT}/versions/${VENV}/bin/activate
source VENV_DIR

