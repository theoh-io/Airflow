FROM openfoam/openfoam8-paraview56

ARG USER_UID=1000
ARG USER_GID=1000

USER root

# Align the OpenFOAM user/group with the host so bind mounts stay writable
RUN groupmod -o -g ${USER_GID} openfoam && \
    usermod  -o -u ${USER_UID} -g ${USER_GID} openfoam && \
    mkdir -p /workspace && \
    chown -R openfoam:openfoam /workspace /home/openfoam

WORKDIR /workspace
COPY src/ ./src/
RUN chown -R openfoam:openfoam /workspace

# Source OpenFOAM in the OpenFOAM user's bashrc so it's always available
RUN echo ". /opt/openfoam8/etc/bashrc" >> /home/openfoam/.bashrc

USER openfoam

CMD ["/bin/bash"]