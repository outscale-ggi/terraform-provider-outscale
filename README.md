# QA TINA

This module contains tests for Tina.

## Status
[![pipeline status](https://gitlab.outscale.internal/qa-produit/qa_tina/badges/master/pipeline.svg)](https://gitlab.outscale.internal/qa-produit/qa_tina/commits/master)
[![coverage report](https://gitlab.outscale.internal/qa-produit/qa_tina/badges/master/coverage.svg)](https://gitlab.outscale.internal/qa-produit/qa_tina/commits/master)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This project use Python 3
All developments dependencies are listed in requirements.dev.txt

You can initialize a virtual environment for development with the following command:
```
make env
```

### Build documentation

```
make doc
```

### Running the tests

#### Static code analysis

For static code analysis we use pylint with a custom configuration file saved in this project.

```
make pylint
```

#### Module tests and coverage

/!\ Not implemented
```
make tests
```

## Deployment

This project just need Python .
There is no other module dependency.

/!\ Not implemented
```
python setup.py install
```

## Versioning

See [Branches](https://gitlab.outscale.internal/qa-produit/qa_tina/branches) and [Tags](https://gitlab.outscale.internal/qa-produit/qa_tina/tags) on this repository.

## Authors

[PQA Team](https://gitlab.outscale.internal/qa-produit/qa_tina/graphs/master)

