SHELL = /bin/bash
ROOT_PATH ?= $(PWD)
PROJECT_NAME = $$(basename $(ROOT_PATH))

include $(ROOT_PATH)/Makefile.conf

BUILD_VENV_PATH ?= "$(ROOT_PATH)/venv_build"
DEV_VENV_PATH ?= "$(ROOT_PATH)/venv_dev"

PYTHON_PATH = $$(STR="$(ROOT_PATH)"; for DEP in $(PROJECT_DEPENDENCIES); do STR=$$STR":$(ROOT_PATH)/"$$(echo $$DEP | awk -F/ '{print $$NF}'); done; echo $$STR)


help:
	@echo ''
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@echo '  help          Show this help.'
	@echo '  init          Get all project dependencies.'
	@echo '  init_dev      Initialize a venv with development dependencies.'
	@echo '  init_build    Initialize a venv with dependencies needed to build package.'
	@echo '  init_ci       Add CI dependencies in development environment.'
	@echo '  pylint        Execute static code analysis.'
	@echo '  bandit        Execute static security check.'
	@echo '  ci            Execute pylint and bandit.'
	@echo '  build         Build package.'
	@echo '  check-todo    Check remaining TODO in source code.'
	@echo '  update-deps   Update internal dependencies sha1.'
	@echo '  update-req    Update external dependencies with latest version in development environment and requirements.txt.'
	@echo ''
	@echo 'See README for more informations'
	@echo ''


python-path:
	@echo $(PYTHON_PATH)

init:
	@echo "Get dependencies from Git..."
	# install project dependencies
	for DEP in $(PROJECT_DEPENDENCIES); do                                                  \
		DEP_DIR=$(ROOT_PATH)/$$(echo $$DEP | awk -F/ '{print $$NF}');                       \
		if [ ! -d "$$DEP_DIR" ]; then                                                       \
			git clone git@gitlab.outscale.internal:qa-produit/$$DEP.git $$DEP_DIR;          \
		else                                                                                \
			pushd $$DEP_DIR; git checkout master; git pull; popd;                           \
		fi;                                                                                 \
		pushd $$DEP_DIR;                                                                    \
		git checkout $$(grep $$(echo $$DEP | awk -F/ '{print $$NF}')= $(ROOT_PATH)/internal_deps.txt | cut -d '=' -f2); \
		popd;                                                                               \
	done

# retro-compat...
deps: init

init_dev: init
	@echo "Init development environment..."
	# create venv
	if [ ! -d "$(DEV_VENV_PATH)" ]; then  \
		python3 -m venv $(DEV_VENV_PATH); \
	fi
	# install python dependencies
	source $(DEV_VENV_PATH)/bin/activate; \
	pip install pip==19.3.1;              \
	pip install -r requirements.txt;      \
	deactivate;


init_build: init
	@echo "Init build environment..."
	# create venv
	if [ ! -d "$(BUILD_VENV_PATH)" ]; then  \
		python3 -m venv $(BUILD_VENV_PATH); \
	fi
	# install python dependencies
	source $(BUILD_VENV_PATH)/bin/activate; \
	pip install pip==19.3.1;                \
	pip install wheel==0.33.6;              \
	deactivate;

init_ci: init_dev
	@echo "Init test environment..."
	source $(DEV_VENV_PATH)/bin/activate; \
	pip install pylint==2.4.4;            \
	pip install bandit==1.6.2;            \
	deactivate;
	#prospector==1.2.0

pylint: init_ci
	@echo "Static code analysis..."
	source $(DEV_VENV_PATH)/bin/activate;             \
	export PYTHONPATH=$(PYTHON_PATH);                 \
	pylint --rcfile=./pylint.conf $(PROJECT_MODULES); \
	deactivate;

bandit: init_ci
	@echo "Static code analysis..."
	source $(DEV_VENV_PATH)/bin/activate;          \
	export PYTHONPATH=$(PYTHON_PATH);              \
	bandit $(BANDIT_CFG) -r -l $(PROJECT_MODULES); \
	deactivate;

ci: bandit pylint

build:
	@echo "TODO..."

check-todo: init_test
	@echo "Check TODO..."
	source $(DEV_VENV_PATH)/bin/activate;                     \
	export PYTHONPATH=$(PYTHON_PATH);                         \
	pylint --rcfile=./pylint.conf -e fixme $(PROJECT_MODULES) \
	deactivate;

update-deps: init
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

update-req: init_dev
	@echo "Update requirements"
	source $(DEV_VENV_PATH)/bin/activate;                       \
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
	done;                                                       \
	deactivate;
