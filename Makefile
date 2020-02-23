SHELL = /bin/bash

PROJECT_NAME = qa_tina

PROJECT_DEPENDENCIES = qa_tools

ROOT_PATH ?= $$(pwd)
USER_VENV_PATH ?= "$$(pwd)/venv_p3"
DEV_VENV_PATH ?= "$$(pwd)/venv_p3_dev"

#PYTHON_PATH = $$(STR="$$(pwd)"; for DEP in $(PROJECT_DEPENDENCIES); do STR=$$STR":$$(pwd)/"$$DEP; done; echo $$STR)
PYTHON_PATH = $$(STR="$$(pwd)"; for DEP in $(PROJECT_DEPENDENCIES); do STR=$$STR":"$$(ROOT_PATH=$(ROOT_PATH) make -C $(ROOT_PATH)/$$DEP python-path); done; echo $$STR)

python-path:
	@echo $(PYTHON_PATH)

help:
	@echo ''
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@echo '  deps       Get all project dependencies'
	@echo '  env        Initialize user environment'
	@echo '  devenv     Initialize development environment'
	@echo '  pylint     Execute static code analysis'
	@echo '  tests      Execute tests'
	@echo '  doc        Build documetation'
	@echo '  clean      Clean all generated files'
	@echo '  clean-all  Clean all generated files and remove development environment'
	@echo '  help       Show this help'
	@echo ''
	@echo 'See README for more informations'
	@echo ''

clean:
	@echo "Clean..."
	find ./$(PROJECT_NAME) | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf
	find ./tests | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf
	rm -f ./.coverage
	rm -rf ./htmlcov
	rm -rf ./.pytest_cache
	rm -rf ./pylint.log
	for DEP in $(PROJECT_DEPENDENCIES); do																	\
		if [ -d "$(ROOT_PATH)/$$DEP" ]; then																\
			ROOT_PATH=$(ROOT_PATH) USER_VENV_PATH=$(USER_VENV_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP clean;	\
		fi																									\
	done
	cd docs && $(MAKE) clean

clean-all: clean
	@echo "Clean all..."
	rm -rf $(USER_VENV_PATH)
	rm -rf $(DEV_VENV_PATH)
	# TODO: add sub project clean-all with ROOT_PATH...
	for DEP in $(PROJECT_DEPENDENCIES); do 	\
		rm -rf $(ROOT_PATH)/$$DEP; 						\
	done

deps:
	# install project dependencies
	for DEP in $(PROJECT_DEPENDENCIES); do                                  				\
		if [ ! -d "$(ROOT_PATH)/$$DEP" ]; then												\
			git clone git@gitlab.outscale.internal:qa-produit/$$DEP.git $(ROOT_PATH)/$$DEP; \
		else																				\
			pushd $(ROOT_PATH)/$$DEP; git pull; popd;										\
		fi;																					\
		ROOT_PATH=$(ROOT_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP deps;							\
	done

env: 
	@echo "Init environment..."
	# create venv
	if [ ! -d "$(USER_VENV_PATH)" ]; then			\
		if [ "$$(uname)" = "Darwin" ]; then		\
			python3 -m venv $(USER_VENV_PATH);		\
		else										\
			python36 -m venv $(USER_VENV_PATH);		\
		fi											\
	fi
	# install python dependencies
	source $(USER_VENV_PATH)/bin/activate;	\
	pip install -r requirements.txt;		\
	deactivate;
	
	# install project dependencies
	for DEP in $(PROJECT_DEPENDENCIES); do 															\
		source $(USER_VENV_PATH)/bin/activate;														\
		pip install -r $(ROOT_PATH)/$$DEP/requirements.txt;											\
		deactivate;																					\
		ROOT_PATH=$(ROOT_PATH) USER_VENV_PATH=$(USER_VENV_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP env;	\
	done

devenv: deps
	@echo "Init environment..."
	echo $(DEV_VENV_PATH)
	# create venv
	if [ ! -d "$(DEV_VENV_PATH)" ]; then	\
		python3 -m venv $(DEV_VENV_PATH);	\
	fi
	# install python dependencies
	source $(DEV_VENV_PATH)/bin/activate;	\
	pip install -r requirements.txt;		\
	pip install -r requirements.dev.txt;	\
	deactivate;
	
	# install project dependencies
	for DEP in $(PROJECT_DEPENDENCIES); do															\
		source $(DEV_VENV_PATH)/bin/activate;														\
		pip install -r $(ROOT_PATH)/$$DEP/requirements.txt;											\
		deactivate;																					\
		ROOT_PATH=$(ROOT_PATH) USER_VENV_PATH=$(DEV_VENV_PATH) $(MAKE) -C $(ROOT_PATH)/$$DEP env;	\
	done

pylint: devenv 
	@echo "Static code analysis..."												
	source $(DEV_VENV_PATH)/bin/activate;										\
	export PYTHONPATH=$(PYTHON_PATH);											\
	pylint --rcfile ./.pylintrc ./$(PROJECT_NAME) ./tests | tee ./pylint.log;	\
	deactivate
	#if (( $$(echo "$$(grep rated ./pylint.log | sed 's/.*at //g;s/\/.*//g')<9" | bc -l) )); then echo "pylint must be greater than 9"; exit 1; fi

tests: clean devenv
	@echo "Exec tests"
	@echo "/!\ Not implemented..."
	#source $(DEV_VENV_PATH)/bin/activate;												\
	#export PYTHONPATH=$(PYTHON_PATH);													\
	#pytest -s -vv --cov-report term --cov-report html --cov=$(PROJECT_NAME) ./tests/;	\
	#deactivate
	#if (( $$(echo "$$(grep pc_cov htmlcov/index.html | sed 's/.*\">//g;s/%.*//g')<95" | bc -l) )); then echo "coverage must be greater than 90%"; exit 1; fi

doc: clean devenv
	@echo "Generate documentation"
	source $(DEV_VENV_PATH)/bin/activate;	\
	export PYTHONPATH=$(PYTHON_PATH);		\
	$(MAKE) -C ./docs html;					\
	deactivate
