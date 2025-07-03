# Start with a standard Ubuntu image
FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install ALL system dependencies we have identified
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    zip \
    unzip \
    build-essential \
    python3-pip \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    autoconf \
    automake \
    libtool \
    cmake \
    m4 \
    wget \
    openjdk-17-jdk

# Install Python packages GLOBALLY. NO VENV.
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir \
    "cython<3.0" \
    git+https://github.com/kivy/buildozer.git

# Add the global python bin directory to the PATH for all users
ENV PATH="/usr/local/bin:$PATH"

# Create a non-root user for our work
RUN useradd -m -s /bin/bash builduser
USER builduser
WORKDIR /home/builduser

# Set the default command to an interactive shell
CMD ["/bin/bash"]