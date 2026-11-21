#!/bin/sh
# POSIX shell script to update llama-cpp.spec to the latest (or specified)
# upstream semantic version release (vX.Y.Z) and its pinned bXXXX nightly tag.
#
# Usage:
#   ./scripts/update-version.sh [path/to/llama-cpp.spec] [vX.Y.Z]
set -eu

SPEC_FILE=${1:-llama-cpp.spec}
TARGET_TAG=${2:-}
REPO=${LLAMA_REPO:-ggml-org/llama.cpp}
API_BASE="https://api.github.com/repos/${REPO}"

if [ ! -f "${SPEC_FILE}" ]; then
    printf 'Error: spec file not found: %s\n' "${SPEC_FILE}" >&2
    exit 1
fi

for cmd in curl jq sed tr; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        printf 'Error: required command not found: %s\n' "${cmd}" >&2
        exit 1
    fi
done

github_api_get() {
    url=$1
    token=${GH_TOKEN:-${GITHUB_TOKEN:-}}
    if [ -n "${token}" ]; then
        curl -fsSL \
            -H "Accept: application/vnd.github+json" \
            -H "Authorization: Bearer ${token}" \
            "${url}"
    else
        curl -fsSL \
            -H "Accept: application/vnd.github+json" \
            "${url}"
    fi
}

resolve_meta_tag() {
    if [ -n "${TARGET_TAG}" ]; then
        case "${TARGET_TAG}" in
            v[0-9]*) printf '%s\n' "${TARGET_TAG}" ;;
            [0-9]*)  printf 'v%s\n' "${TARGET_TAG}" ;;
            *)
                printf 'Error: invalid version tag "%s" (expected vX.Y.Z)\n' "${TARGET_TAG}" >&2
                exit 1
                ;;
        esac
        return 0
    fi

    # Check /releases/latest first; if a rolling bXXXX build was published
    # without the prerelease flag, fall back to scanning recent releases for
    # the newest vX.Y.Z release tag.
    latest_tag=$(github_api_get "${API_BASE}/releases/latest" | jq -r '.tag_name // empty' || true)
    case "${latest_tag}" in
        v[0-9]*.[0-9]*.[0-9]*)
            printf '%s\n' "${latest_tag}"
            return 0
            ;;
    esac

    sem_tag=$(github_api_get "${API_BASE}/releases?per_page=100" | jq -r '
        first(
            .[]
            | select((.draft | not) and (.tag_name | test("^v[0-9]+\\.[0-9]+\\.[0-9]+$")))
        )
        | .tag_name // empty
    ')
    case "${sem_tag}" in
        v[0-9]*.[0-9]*.[0-9]*)
            printf '%s\n' "${sem_tag}"
            return 0
            ;;
    esac

    printf 'Error: could not resolve latest vX.Y.Z release from %s\n' "${REPO}" >&2
    exit 1
}

META_TAG=$(resolve_meta_tag)
VERSION=${META_TAG#v}

NIGHTLY_TAG_URL="https://github.com/${REPO}/releases/download/${META_TAG}/nightly-tag.txt"
UPSTREAM_TAG=$(curl -fsSL "${NIGHTLY_TAG_URL}" | tr -d '[:space:]')

case "${UPSTREAM_TAG}" in
    b[0-9]*) ;;
    *)
        printf 'Error: nightly-tag.txt for %s did not return a valid bXXXX tag (got "%s")\n' \
            "${META_TAG}" "${UPSTREAM_TAG}" >&2
        exit 1
        ;;
esac

printf 'Resolved %s release %s -> upstream build %s\n' "${REPO}" "${META_TAG}" "${UPSTREAM_TAG}"

sed -i \
    -e "s/^Version:[[:space:]]*.*/Version:        ${VERSION}/" \
    -e "s/^%global upstream_tag[[:space:]]*.*/%global upstream_tag ${UPSTREAM_TAG}/" \
    "${SPEC_FILE}"

printf 'Updated %s (Version: %s, upstream_tag: %s)\n' "${SPEC_FILE}" "${VERSION}" "${UPSTREAM_TAG}"
