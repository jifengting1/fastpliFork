.PHONY: help
help:
	@echo "make install -- installation of venv with fastpli"
	@echo "make build -- compilation of fastpli and providing of build/setup.py"
	@echo "make examples/requirements"
	@echo "make test"
	@echo "make clean-all"

BUILD := release
VENV := env

CMAKE.debug := cmake .. -DCMAKE_BUILD_TYPE=Debug
CMAKE.info := cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
CMAKE.release := cmake .. -DCMAKE_BUILD_TYPE=Release
CMAKE := ${CMAKE.${BUILD}}

MAKE.debug := make
MAKE.info := make -j
MAKE.release := make -j
MAKE := ${MAKE.${BUILD}}

INSTALL.debug := install build/.
INSTALL.info := install build/. -q
INSTALL.release := install build/. -q
INSTALL := ${INSTALL.${BUILD}}

${VENV}/bin/pip3:
	@rm -rf ${VENV}
	python3 -m venv ${VENV}/
	${VENV}/bin/pip3 install --upgrade pip -q

${VENV}/bin/python3:
	@rm -rf ${VENV}
	python3 -m venv ${VENV}/
	${VENV}/bin/pip3 install --upgrade pip -q

.PHONY: ${VENV}
${VENV}: ${VENV}/bin/pip3 ${VENV}/bin/python3

.PHONY: git-submodules
git-submodules:
	git submodule update --init

.PHONY: examples/requirements
examples/requirements:
	${VENV}/bin/pip3 install -r examples/requirements.txt -q

.PHONY: install
install: ${VENV} git-submodules uninstall build
	${VENV}/bin/pip3 ${INSTALL}

.PHONY: development
development: ${VENV} git-submodules uninstall build examples/requirements
	${VENV}/bin/pip3 install -e build/. -q
	${VENV}/bin/pip3 install yapf -q
	${VENV}/bin/pip3 install pylint -q

.PHONY: uninstall
uninstall:
	${VENV}/bin/pip3 uninstall fastpli -y

.ONESHELL:
build/:
	mkdir build

.ONESHELL:
build/Makefile: build/
	@if [ ! -f build/Makefile ]
	then
		cd build
		echo ${CMAKE}
		${CMAKE}
	fi

.PHONY: build
.ONESHELL:
build: build/ build/Makefile
	cd build
	${MAKE}

.PHONY: test
test:
	${VENV}/bin/python3 -m unittest discover -s tests -p '*_test.py'

.PHONY: h5py-serial
h5py-serial:
	${VENV}/bin/pip3 install h5py

.PHONY: h5py-mpi
h5py-mpi:
	${VENV}/bin/pip3 uninstall h5py
	HDF5_DIR=${HDF5_DIR} CC=mpicc HDF5_MPI="ON" ${VENV}/bin/pip3 install --no-binary=h5py h5py
	# e.g. HDF5_DIR=/usr/lib/x86_64-linux-gnu/hdf5/openmpi

.PHONY: h5py-clean
h5py-clean:
	${VENV}/bin/pip3 uninstall h5py -y

.PHONY: docker-build
docker-build:
	docker build -t fastpli .
	docker container rm fastpli-test
	docker create --name fastpli-test fastpli

.PHONY: docker
docker: docker-build
	rm -rf /tmp/fastpli
	git clone . /tmp/fastpli
	docker cp /tmp/fastpli fastpli-test:/code/
	rm -rf /tmp/fastpli
	docker start -i fastpli-test

.PHONY: clean
clean: clean-build clean-src

.PHONY: clean-all
clean-all: clean-build clean-src clean-venv

.PHONY: clean-build
clean-build:
	rm -rf build
	rm -f src/fastpli/version.py
	rm -f src/include/version.hpp

.PHONY: clean-venv
clean-venv:
	rm -rf ${VENV}

.PHONY: clean-src
clean-src:
	@echo clean src
	@find src/ -name "*egg-info" -exec rm -r {} +
	@find src/ -name "*.so" -exec rm {} +
	@find src/ -name "__pycache__" -exec rm -r {} +
	@find tests/ -name "__pycache__" -exec rm -r {} +
