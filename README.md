# notebook-environments

![tests](https://github.com/vladpunko/notebook-environments/actions/workflows/tests.yml/badge.svg)

Manage python virtual environments on the working notebook server.

![usage-example](https://raw.githubusercontent.com/vladpunko/notebook-environments/master/notebook_environments.gif)

## Installation

It is recommended to use this package together with [virtualenv](https://github.com/pypa/virtualenv) and [virtualenvwrapper](https://bitbucket.org/virtualenvwrapper/virtualenvwrapper) to work with python virtual environments more suitable. Make sure the installed [python](https://wiki.archlinux.org/title/python) interpreters work without errors on the current operating system. To install this package as a standalone application with the command-line interface you are to run the following command:

```bash
sudo sh -c "$(curl https://raw.githubusercontent.com/vladpunko/notebook-environments/master/install.sh)"
```

Use the package manager [pip](https://pip.pypa.io/en/stable) to install notebook-environments without the command-line interface:

```bash
python3 -m pip install notebook-environments
```

You can also install this python package on your working machine (works for unix-like operating systems) from source code to `/usr/local/bin` as the standard system location for user's programs (this location can be changed at the user's discretion):

```bash
# Step -- 1.
git clone --depth=1 --branch=master https://github.com/vladpunko/notebook-environments.git

# Step -- 2.
cd ./notebook-environments/

# Step -- 3.
sudo install -m 755 n.sh /usr/local/bin/n

# Step -- 4.
sudo install -m 755 notebook_environments.py /usr/local/bin/notebook-environments
```

## Basic usage

Using this program allows you to run one instance of [notebook](https://github.com/jupyter/notebook) server on your working machine and add different python virtual environments as needed.
It protects you from the trouble of installing notebook packages in a new environment and running multiple servers.

```bash
# Step -- 1.
nohup jupyter notebook > /tmp/notebook.log 2>&1 &

# Step -- 2.
python3 -m venv .venv && source ./.venv/bin/activate && notebook-environments --add

# Step -- 3.
notebook-environments --show
```

## Contributing

Pull requests are welcome.
Please open an issue first to discuss what should be changed.

Please make sure to update tests as appropriate.

```bash
# Step -- 1.
python3 -m venv .venv && source ./.venv/bin/activate && pip install pre-commit tox

# Step -- 2.
pre-commit install --config .githooks.yml

# Step -- 3.
tox && tox -e lint
```

## License

[MIT](https://choosealicense.com/licenses/mit)
