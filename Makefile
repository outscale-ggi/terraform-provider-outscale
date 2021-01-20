SHELL = /bin/bash
ROOT_PATH ?= $(PWD)
DEPS_PATH ?= $(ROOT_PATH)
VENV_PATH ?= "$(ROOT_PATH)/.venv"

MR_SRC ?= ""
MR_DST ?= ""

PROJECT_MODULES = ""
PROJECT_DEPENDENCIES = ""

PROJECT_NAME = $$(basename $(ROOT_PATH))

PYTHON_PATH = $$(STR="$(ROOT_PATH)"; for DEP in $(PROJECT_DEPENDENCIES); do STR=$$STR":$(DEPS_PATH)/"$$(echo $$DEP | awk -F/ '{print $$NF}'); done; echo $$STR)

include $(ROOT_PATH)/Makefile.conf

help:
	@echo ''
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@echo '  clean'
	@echo '  python-path'
	@echo '  init-deps'
	@echo '  init-venv'
	@echo '  init-dev'
	@echo '  init-build'
	@echo '  init-ci'
	@echo '  check-init'
	@echo '  pylint'
	@echo '  pylint-mr'
	@echo '  check-todo'
	@echo '  bandit'
	@echo '  bandit-mr'
	@echo '  test'
	@echo '  ci'
	@echo '  build'
	@echo '  update-deps'
	@echo '  update-req'
	@echo ''
	@echo 'See README for more informations'
	@echo ''

clean:
	rm -rf ./build;
	rm -rf ./osc_$(PROJECT_NAME)*.egg-info;

python-path:
	@echo $(PYTHON_PATH)

ifneq ($(ROOT_PATH), $(DEPS_PATH))
init-deps:
	@echo "Dependencies cannot be cloned outside current directory"
else
init-deps:
	@echo "Get dependencies from Git..."
#	mkdir -p $$HOME/mirrors;
	# install project dependencies
#	for DEP in $(PROJECT_DEPENDENCIES); do                                                                  \
#        DEP_DIR=$(ROOT_PATH)/$$(echo $$DEP | awk -F/ '{print $$NF}');                                       \
#        if [ ! -d "$$DEP_DIR" ]; then                                                                       \
#            MIRROR_DIR="$$HOME/mirrors/$$(echo $$DEP | awk -F/ '{print $$NF}')";                            \
#            if [ ! -d "$$MIRROT_DIR" ]; then                                                                \
#                git clone --mirror git@gitlab.outscale.internal:qa-produit/$$DEP.git $$MIRROR_DIR;          \
#            fi;                                                                                             \
#            git clone --reference $$MIRROR_DIR git@gitlab.outscale.internal:qa-produit/$$DEP.git $$DEP_DIR; \
#        else                                                                                                \
#            pushd $$DEP_DIR; git checkout master; git pull; popd;                                           \
#        fi;                                                                                                 \
#        pushd $$DEP_DIR;                                                                                    \
#        git checkout $$(grep $$(echo $$DEP | awk -F/ '{print $$NF}')= $(ROOT_PATH)/internal_deps.txt | cut -d '=' -f2); \
#        popd;                                                                                               \
#    done
	for DEP in $(PROJECT_DEPENDENCIES); do                                                                  \
        DEP_DIR=$(ROOT_PATH)/$$(echo $$DEP | awk -F/ '{print $$NF}');                                       \
        if [ ! -d "$$DEP_DIR" ]; then                                                                       \
            git clone  git@gitlab.outscale.internal:qa-produit/$$DEP.git $$DEP_DIR;                         \
        else                                                                                                \
            pushd $$DEP_DIR; git checkout master; git pull; popd;                                           \
        fi;                                                                                                 \
        pushd $$DEP_DIR;                                                                                    \
        git checkout $$(grep $$(echo $$DEP | awk -F/ '{print $$NF}')= $(ROOT_PATH)/internal_deps.txt | cut -d '=' -f2); \
        popd;                                                                                               \
    done
endif

ifneq ($(VENV_PATH), "$(ROOT_PATH)/.venv")

init-venv:
	@echo "environment cannot be managed outside .venv"
init-dev:
	@echo "environment cannot be managed outside .venv"
init-build:
	@echo "environment cannot be managed outside .venv"
init-ci:
	@echo "environment cannot be managed outside .venv"
check-init:
	@echo "environment cannot be managed outside .venv"

else

init-venv:
	@echo "Init environment..."
	# create venv
	if [ ! -d "$(VENV_PATH)" ]; then  \
        python3 -m venv $(VENV_PATH); \
    fi

init-dev:
	@echo "Init development environment..."
	pip install pip==20.3.3;
	pip install setuptools==51.3.3;
	pip install --quiet --editable .;

init-build:
	@echo "Init build environment..."
	pip install pip==20.3.3;
	pip install setuptools==51.3.3;
	pip install wheel==0.36.2;

init-ci: init-dev
	@echo "Init test environment..."
	pip install pylint==2.6.0;
	pip install bandit==1.7.0;

check-init: init-ci init-build
	@echo "Check init..."
	pip list --outdated | ( ! egrep  "pip|pylint|bandit|setuptools|^wheel")

endif

pylint: init-ci
	@echo "Static code analysis..."
	export PYTHONPATH=$(PYTHON_PATH);                 \
    pylint -j 4 --rcfile=./pylint.conf $(PROJECT_MODULES);

pylint-mr: init-ci
	@echo "Static code analysis..."
	export PYTHONPATH=$(PYTHON_PATH);                 \
    pylint -j 4 --rcfile=./pylint.conf $$(git diff --name-only $(MR_SRC) $(MR_DST) | grep "\.py$$");

check-todo: init-ci
	@echo "Check TODO..."
	export PYTHONPATH=$(PYTHON_PATH);                         \
    pylint --rcfile=./pylint.conf -e fixme $(PROJECT_MODULES)

bandit: init-ci
	@echo "Static code analysis..."
	export PYTHONPATH=$(PYTHON_PATH);                         \
    bandit -r -l --configfile bandit.conf $(PROJECT_MODULES);

bandit-mr: init-ci
	@echo "Static code analysis..."
	export PYTHONPATH=$(PYTHON_PATH);                         \
    bandit -r -l --configfile bandit.conf $$(git diff --name-only $(MR_SRC) $(MR_DST) | grep "\.py$$");

test: init-ci
	@echo "Test..."
#	cd tests/;                    \
#    pytest --verbose --tb=no -ra; \
#    pytest --cov-report term --cov-report html --cov=qa_billing_tools --disable-warnings -s -v test_billing_tools;

ci: bandit pylint test


build: init-build
	@echo "Build package..."
	tag_name=$$(git describe --tags --exact-match 2> /dev/null);                            \
    branch_name="$$CI_BUILD_REF_NAME";                                                      \
    if [ "$$tag_name" == "" ]; then                                                         \
    	tag_name="$$(git describe --tags --abbrev=4 | sed 's/-g.*//g')";                    \
        if [ "$$branch_name" == "" ]; then                                                  \
        	branch_name=$$(git branch | grep \* | cut -d ' ' -f2);                          \
        fi;                                                                                 \
    else                                                                                    \
        branch_name="";                                                                     \
    fi;                                                                                     \
    echo "\"\"\"GENERATED FILE - DO NOT PUSH UPDATES\"\"\"" > $(ROOT_PATH)/$(PROJECT_NAME)/version.py; \
    echo "__version__ = \"$$tag_name\"" >> $(ROOT_PATH)/$(PROJECT_NAME)/version.py;             \
    echo "__branch__ = \"$$branch_name\"" >> $(ROOT_PATH)/$(PROJECT_NAME)/version.py;
	python setup.py bdist_wheel;


ifneq ($(ROOT_PATH), $(DEPS_PATH))

update-deps:
	@echo "Dependencies references cannot be updated outside current directory"

else

update-deps: init-deps
	@echo "update deps..."
	echo "# Versionning informations" > $(ROOT_PATH)/internal_deps.txt;
	for DEP in $(PROJECT_DEPENDENCIES); do                                                                                                                                     \
        DEP_DIR=$(ROOT_PATH)/$$(echo $$DEP | awk -F/ '{print $$NF}');                                                                                                          \
        pushd $$DEP_DIR;                                                                                                                                                       \
        git checkout master;                                                                                                                                                   \
        git pull;                                                                                                                                                              \
        popd;                                                                                                                                                                  \
        echo $$(echo $$DEP | awk -F/ '{print $$NF}')=$$(pushd $$DEP_DIR > /dev/null; git --no-pager log -1 --format='%H'; popd > /dev/null) >> $(ROOT_PATH)/internal_deps.txt; \
    done

endif

ifneq ($(VENV_PATH), "$(ROOT_PATH)/.venv")

update-req:
	@echo "environment cannot be managed outside .venv"

else

update-req:
	@echo "Update requirements"
	for cur in $$(grep '==' ./requirements.txt); do             \
        pkg_name=$$(echo $$cur | cut -d '=' -f1);               \
        pip install $$pkg_name --upgrade;                       \
        new=$$(pip freeze | grep $$pkg_name"=");                \
        echo "$$cur ==> $$new";                                 \
        if [ "$$(uname)" == "Darwin" ]; then                    \
            sed -i '' 's/'$$cur'/'$$new'/g' ./requirements.txt; \
        else                                                    \
            sed -i 's/'$$cur'/'$$new'/g' ./requirements.txt;    \
        fi;                                                     \
     done;

endif
