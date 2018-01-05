
# ipytunnel

[![Build Status](https://travis-ci.org/vidartf/ipytunnel.svg?branch=master)](https://travis-ci.org/vidartf/ipytunnel)
[![codecov](https://codecov.io/gh/vidartf/ipytunnel/branch/master/graph/badge.svg)](https://codecov.io/gh/vidartf/ipytunnel)


A Jupyter notebook/lab extension for optimally pushing many comm open messages in one batch.

## Installation

A typical installation requires the following commands to be run:

```bash
pip install ipytunnel
jupyter nbextension enable --py [--sys-prefix|--user|--system] ipytunnel
```

Or, if you use jupyterlab:

```bash
pip install ipytunnel
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```
