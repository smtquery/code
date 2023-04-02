FROM ubuntu:latest
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && apt-get install -y --no-install-recommends apt-utils && apt-get -y upgrade
RUN apt-get install -y build-essential git python3 python3-pip python3-venv graphviz z3 wget

# install smtquery
WORKDIR /smtquery
COPY bin bin/
COPY data data/
COPY smtquery smtquery/
COPY setup.py ./

# download cvc5
RUN wget https://github.com/cvc5/cvc5/releases/latest/download/cvc5-Linux -P /usr/bin
RUN chmod +x /usr/bin/cvc5-Linux

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies:
RUN python3 setup.py develop
RUN pip3 install sqlalchemy pyyaml z3-solver graphviz celery matplotlib tabulate pathos pythomata automata-lib copy stopit sklearn dtreeviz==1.3.7

# Link benchmarks used in the paper
# uncomment the following lines to use our benchmarks, database, and cached ASTS
#RUN wget informatik.uni-kiel.de/~mku/smtquery_data.tar.gz -P /tmp
#RUN tar xf /tmp/smtquery_data.tar.gz -C /tmp
#RUN mv /tmp/smtqueryData/db.sql /smtquery
#RUN mv /tmp/smtqueryData/data/smtfiles /smtquery/data/
#RUN mv /tmp/smtqueryData/smtquery/data/pickle /smtquery/smtquery/data/

# Only use the benchmarks
# uncomment the following lines to only use our benchmarks
RUN wget informatik.uni-kiel.de/~mku/smtquery_instances.tar.gz -P /tmp
RUN tar xf /tmp/smtquery_instances.tar.gz -C /tmp
RUN mv /tmp/smtqueryData/data/smtfiles /smtquery/data/
RUN python3 bin/smtquery initdb

ENTRYPOINT ["python3", "bin/smtquery"]