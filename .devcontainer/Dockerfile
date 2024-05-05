FROM python:3.12.2-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    NICEGUI_STORAGE_PATH=data

# Install packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    sudo git build-essential chromium chromium-driver python3-pip\
    && rm -rf /var/lib/apt/lists/*

# Create remote user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"
ENV CHROME_BINARY_LOCATION=/usr/bin/chromium

USER $USERNAME

CMD ["python", "wait.py"]