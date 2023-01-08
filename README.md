# ML-tinkoff
An introduction task to ML school 2023 from Tinkoff

## Installation
To install the project, you need to clone this project from repository dy using command:
```bash
git clone https://github.com/predprof/ML-tinkoff.git
```

## Usage
Create file **input.txt** and write down pairs of names of files that you want to compare.
Example
```
files/main.py plagiat1/main.py
files/lossy.py plagiat2/lossy.py
files/lossy.py files/lossy.py
```
In command line run the follow script:
```bash
python compare.py input.txt scores.txt
```
In file **scores.txt** you will get the next data:
```
0.9819655521783182
0.4116824440619621
1.0
```
