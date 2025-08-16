# Commands used in the bootcamp

To create a virtual environment, run:

```bash
# For Linux and macOS
python3 -m venv .env
# For Windows
python -m venv .env
```

To activate the virtual environment, use the following command:

```bash
source .env/bin/activate
```

Once you have activated the virtual environment, you can install the required packages using the following command provided 'requirements.txt' is present in the same directory:

```bash
pip install -r requirements.txt
```
or you can install the packages individually:

```bash
pip install flask
pip install flask_sqlalchemy
```

To run the Flask application, use the following command:

```bash
python app.py
```
provided 'app.py' is the main file of your Flask application.

