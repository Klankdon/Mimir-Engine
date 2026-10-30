# Draft memory boundary fixture for #24

This offline fixture follows the maintainer's invitation to use mocks around `db.py` or `app.py`.
Source baseline: `b0451ca732d5969cb5195f330ee9559805d73f4f`.
It adds tests and this case card; production files and schema stay unchanged.

From the repository root, using Python 3.10 or newer:

```sh
python -B -m unittest discover -s tests -p test_memory_contract.py -v
