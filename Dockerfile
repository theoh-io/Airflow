FROM openfoam/openfoam8-paraview56

WORKDIR /workspace
COPY src/ ./src/

# Source OpenFOAM in bashrc so it's always available
RUN echo ". /opt/openfoam/etc/bashrc" >> ~/.bashrc

CMD ["/bin/bash"]