FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.10-bullseye

RUN su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install lts/* 2>&1"

RUN pip3 --disable-pip-version-check --no-cache-dir install black isort flake8 \
   && rm -rf /tmp/pip-tmp
