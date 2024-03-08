

all: build start

.ONESHELL:
build:
	mkdir -p data
	python -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

start:
	jupyter notebook

clean:
	rm -f cookie.p
	rm -rf __pycache__
	rm -rf venv
	rm -rf data/*
