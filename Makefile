# Single entry point. `make` builds, `make serve` previews at http://localhost:8000
.PHONY: all serve publish
all:
	.venv/bin/python build.py
serve: all
	cd _site && python3 -m http.server 8000
publish:
	./publish.sh "$(m)"
