FROM docker.io/resolwe/base:ubuntu-18.04

MAINTAINER 'resolwe-server project authors https://github.com/biolab/resolwe-server'

# Package manifests
ADD packages-*.txt /home/

# install packages
RUN apt-get update && \
    if [ -f /home/packages-system.txt ]; then \
        echo "Installing distribution packages (build requirements)..." && \
        sed -e 's/^#.*$//g' -e '/^$/d' /home/packages-system.txt | \
            xargs apt-get --no-install-recommends -y install ;\
    fi && \
	if [ -f /home/packages-requirements.txt ]; then \
		echo "Installing requirements..." && \
		pip3 install --require-hashes --requirement /home/packages-requirements.txt ;\
    fi && \
    if [ -f /home/packages-tools.txt ]; then \
    	echo "Installing Python toolss..." && \
        pip3 install --require-hashes --requirement /home/packages-tools.txt ;\
    fi && \
    echo "Cleaning up packages..." && \
    if [ -f /home/packages-system.txt ]; then \
        sed -e 's/^#.*$//g' -e '/^$/d' /home/packages-system.txt | \
            xargs apt-get -y purge ;\
    fi && \
    apt-get autoremove --purge -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip && \
    rm -rf /tmp/*

# docker build --no-cache -t open_tsne .
# docker run -ti open_tsne
