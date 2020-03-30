SHELL = /bin/bash
ROOT_PATH ?= $(PWD)
PROJECT_NAME = $$(basename $(ROOT_PATH))

include $(ROOT_PATH)/Makefile.conf

BUILD_VENV_PATH ?= "$(ROOT_PATH)/venv_build"
DEV_VENV_PATH ?= "$(ROOT_PATH)/venv_dev"

PYTHON_PATH = $$(STR="$(ROOT_PATH)"; for DEP in $(PROJECT_DEPENDENCIES); do STR=$$STR":$(ROOT_PATH)/"$$(echo $$DEP | awk -F/ '{print $$NF}'); done; echo $$STR)

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
	source $(DEV_VENV_PATH)/bin/activate;            \
	export PYTHONPATH=$(PYTHON_PATH);                \
	pylint --rcfile=./pylint.conf $(PROJECT_MODULES) \
	deactivate;

bandit: init_ci
	@echo "Static code analysis..."
	source $(DEV_VENV_PATH)/bin/activate; \
	export PYTHONPATH=$(PYTHON_PATH);     \
	bandit -r -l $(PROJECT_MODULES)       \
	deactivate;
	#bandit -s B101,B110 -r -l ./$(PROJECT_NAME)  \
	#deactivate;

ci: bandit pylint

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


#help:
#	@echo ''
#	@echo 'Usage:'
#	@echo '  make <target>'
#	@echo ''
#	@echo 'Targets:'
#	@echo '  deps       Get all project dependencies'
#	@echo '  env        Initialize user environment'
#	@echo '  devenv     Initialize development environment'
#	@echo '  pylint     Execute static code analysis'
#	@echo '  tests      Execute tests'
#	@echo '  doc        Build documetation'
#	@echo '  clean      Clean all generated files'
#	@echo '  clean-all  Clean all generated files and remove development environment'
#	@echo '  help       Show this help'
#	@echo ''
#	@echo 'See README for more informations'
#	@echo ''

#clean:
#	@echo "Clean..."
#	find ./$(PROJECT_NAME) | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf
#	find ./tests | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf
#	rm -f ./.coverage
#	rm -rf ./htmlcov
#	rm -rf ./.pytest_cache
#	rm -rf ./pylint.log
#	for DEP in $(PROJECT_DEPENDENCIES); do																	\
#		if [ -d "$(ROOT_PATH)/$$DEP" ]; then																\
#			ROOT_PATH=$(ROOT_PATH) USER_VENV_PATH=$(USER_VENV_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP clean;	\
#		fi																									\
#	done
#	cd docs && $(MAKE) clean
#
#clean-all: clean
#	@echo "Clean all..."
#	rm -rf $(USER_VENV_PATH)
#	rm -rf $(DEV_VENV_PATH)
#	# TODO: add sub project clean-all with ROOT_PATH...
#	for DEP in $(PROJECT_DEPENDENCIES); do 	\
#		rm -rf $(ROOT_PATH)/$$DEP; 						\
#	done
#
#deps:
#	# install project dependencies
#	for DEP in $(PROJECT_DEPENDENCIES); do                                  				\
#		if [ ! -d "$(ROOT_PATH)/$$DEP" ]; then												\
#			git clone git@gitlab.outscale.internal:qa-produit/$$DEP.git $(ROOT_PATH)/$$DEP; \
#		else																				\
#			pushd $(ROOT_PATH)/$$DEP; git pull; popd;										\
#		fi;																					\
#		ROOT_PATH=$(ROOT_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP deps;							\
#	done
#
#env: 
#	@echo "Init environment..."
#	# create venv
#	if [ ! -d "$(USER_VENV_PATH)" ]; then			\
#		if [ "$$(uname)" = "Darwin" ]; then		\
#			python3 -m venv $(USER_VENV_PATH);		\
#		else										\
#			python36 -m venv $(USER_VENV_PATH);		\
#		fi											\
#	fi
#	# install python dependencies
#	source $(USER_VENV_PATH)/bin/activate;	\
#	pip install -r requirements.txt;		\
#	deactivate;
#	
#	# install project dependencies
#	for DEP in $(PROJECT_DEPENDENCIES); do 															\
#		source $(USER_VENV_PATH)/bin/activate;														\
#		pip install -r $(ROOT_PATH)/$$DEP/requirements.txt;											\
#		deactivate;																					\
#		ROOT_PATH=$(ROOT_PATH) USER_VENV_PATH=$(USER_VENV_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP env;	\
#	done

#devenv: deps
#	@echo "Init environment..."
#	echo $(DEV_VENV_PATH)
#	# create venv
#	if [ ! -d "$(DEV_VENV_PATH)" ]; then	\
#		python3 -m venv $(DEV_VENV_PATH);	\
#	fi
#	# install python dependencies
#	source $(DEV_VENV_PATH)/bin/activate;	\
#	pip install -r requirements.txt;		\
#	pip install -r requirements.dev.txt;	\
#	deactivate;
#	
#	# install project dependencies
#	for DEP in $(PROJECT_DEPENDENCIES); do															\
#		source $(DEV_VENV_PATH)/bin/activate;														\
#		pip install -r $(ROOT_PATH)/$$DEP/requirements.txt;											\
#		deactivate;																					\
#		ROOT_PATH=$(ROOT_PATH) USER_VENV_PATH=$(DEV_VENV_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP env;	\
#	done
#
#pylint: devenv 
#	@echo "Static code analysis..."												
#	source $(DEV_VENV_PATH)/bin/activate;										\
#	export PYTHONPATH=$(PYTHON_PATH);											\
#	pylint --rcfile ./.pylintrc ./$(PROJECT_NAME) ./tests | tee ./pylint.log;	\
#	deactivate
#	#if (( $$(echo "$$(grep rated ./pylint.log | sed 's/.*at //g;s/\/.*//g')<9" | bc -l) )); then echo "pylint must be greater than 9"; exit 1; fi
#
#tests: clean devenv
#	@echo "Exec tests"
#	@echo "/!\ Not implemented..."
#	#source $(DEV_VENV_PATH)/bin/activate;												\
#	#export PYTHONPATH=$(PYTHON_PATH);													\
#	#pytest -s -vv --cov-report term --cov-report html --cov=$(PROJECT_NAME) ./tests/;	\
#	#deactivate
#	#if (( $$(echo "$$(grep pc_cov htmlcov/index.html | sed 's/.*\">//g;s/%.*//g')<95" | bc -l) )); then echo "coverage must be greater than 90%"; exit 1; fi
#
#doc: clean devenv
#	@echo "Generate documentation"
#	source $(DEV_VENV_PATH)/bin/activate;	\
#	export PYTHONPATH=$(PYTHON_PATH);		\
#	$(MAKE) -C ./docs html;					\
#	deactivate
