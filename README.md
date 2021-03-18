# Flow Results

An implementation of the flow results https://floip.gitbook.io/flow-results-specification/ API

## Development
Install dependencies:
```bash
pip install -e .[dev]
```

Auto format and run tests:
```bash
./format_and_test.sh
```

Run dev server:
```bash
python manage.py migrate
python manage.py runserver
```