FROM ubuntu:latest
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && apt-get install -y --no-install-recommends apt-utils && apt-get -y upgrade
RUN apt-get install -y build-essential git python3 python3-pip python3-venv graphviz z3 cvc4

# clone ZaligVinder for benchmarks
WORKDIR /zaligvinder
RUN git clone https://github.com/zaligvinder/zaligvinder.git .

# install BASC
WORKDIR /BASC
COPY bin bin/
COPY data data/
COPY smtquery smtquery/
COPY setup.py ./

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies:
RUN python3 setup.py develop
RUN pip3 install sqlalchemy pyyaml z3-solver graphviz celery matplotlib tabulate

# Link benchmarks
RUN mkdir -p /BASC/data/smtfiles
RUN ln -sn /zaligvinder/models/appscan /BASC/data/smtfiles/
RUN ln -sn /zaligvinder/models/joacosuite /BASC/data/smtfiles/
RUN ln -sn /zaligvinder/models/pisa /BASC/data/smtfiles/
RUN ln -sn /zaligvinder/models/woorpje /BASC/data/smtfiles/

# Initialise DB
RUN python3 bin/smtquery initdb

#ENTRYPOINT ["python3", "bin/smtquery"]
