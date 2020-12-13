FROM python:3.7 AS base

# This docker file sets up and runs elastic-logger
# in a docker container. This is useful if running
# on an environment that doesn't have Python3/Pip3/Pipenv
# set up

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_SRC=/src \
    PIPENV_HIDE_EMOJIS=true \
    PIPENV_COLORBLIND=true \
    PIPENV_NOSPIN=true

RUN pip install pipenv

WORKDIR /app
COPY ./ ./
RUN pipenv install --deploy --ignore-pipfile --dev

ENTRYPOINT ["pipenv", "run", "python", "-m", "elastic_logger", "kafka"]