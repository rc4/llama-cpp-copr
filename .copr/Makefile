# Fedora COPR SRPM build Makefile
# Invoked by COPR as:
#   make -f .copr/Makefile srpm outdir="<outdir>" spec="<spec>"
#
# Can also be run locally:
#   make -f .copr/Makefile update
#   make -f .copr/Makefile srpm outdir="$(pwd)/build"

TOPDIR      := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
spec        ?= $(TOPDIR)/llama-cpp.spec
outdir      ?= $(TOPDIR)/build
AUTO_UPDATE ?= 0

WORKDIR     := $(abspath $(outdir))/.rpmbuild
SOURCEDIR   := $(WORKDIR)/SOURCES

.PHONY: srpm update deps

deps:
	@missing=""; \
	for cmd in curl jq rpmbuild spectool; do \
		command -v "$$cmd" >/dev/null 2>&1 || missing="$$missing $$cmd"; \
	done; \
	if [ -n "$$missing" ]; then \
		if [ "$$(id -u)" -eq 0 ] && command -v dnf >/dev/null 2>&1; then \
			dnf -y install curl jq rpm-build rpmdevtools; \
		else \
			printf 'Error: missing required tools:%s\n' "$$missing" >&2; \
			exit 1; \
		fi; \
	fi

update: deps
	sh "$(TOPDIR)/scripts/update-version.sh" "$(spec)"

srpm: deps
	@if [ "$(AUTO_UPDATE)" = "1" ]; then \
		sh "$(TOPDIR)/scripts/update-version.sh" "$(spec)"; \
	fi
	mkdir -p "$(SOURCEDIR)" "$(outdir)"
	spectool -g -C "$(SOURCEDIR)" "$(spec)"
	rpmbuild -bs \
		--define "_topdir $(WORKDIR)" \
		--define "_sourcedir $(SOURCEDIR)" \
		--define "_specdir $(dir $(abspath $(spec)))" \
		--define "_srcrpmdir $(abspath $(outdir))" \
		"$(spec)"
	rm -rf "$(WORKDIR)"
