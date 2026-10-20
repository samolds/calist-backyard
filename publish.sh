#!/usr/bin/env bash
# Publish a PII-stripped, single-commit snapshot of `main` to the local `public` branch.
#
#   ./publish.sh
#   git push --force origin public      # when you're ready (this script never pushes)
#
# - Only COMMITTED `main` is published; uncommitted changes are ignored.
# - Everything under private/ stays in `main` only and is never published. PII patterns live in
#   private/pii-patterns.txt (override with PUBLISH_PII_FILE).
#   One Perl regex per line: `PATTERN => REPLACEMENT` (replacement defaults to "[redacted]").
#   Blank lines and lines starting with # are ignored.
# - Text files are scrubbed; then every file (binaries included) and every path is re-checked,
#   and the script stops if anything still matches.
# - `public` is replaced by one parentless commit authored by samolds@gmail.com.
#   The previous `public` stays reachable through `git reflog public`.
set -euo pipefail

SRC_REF="main"
DEST_BRANCH="public"
AUTHOR_EMAIL="samolds@gmail.com"
COMMIT_MSG="init commit"
AUTHOR_NAME="${PUBLISH_AUTHOR_NAME:-$(git config user.name)}"
PRIVATE_DIR="private"

cd "$(git rev-parse --show-toplevel)"
PII_FILE="${PUBLISH_PII_FILE:-$PWD/$PRIVATE_DIR/pii-patterns.txt}"
GIT_DIR_ABS="$(git rev-parse --absolute-git-dir)"

if [[ ! -s "$PII_FILE" ]]; then
  echo "error: PII pattern file missing or empty: $PII_FILE" >&2
  exit 1
fi
if [[ "$(git symbolic-ref --short -q HEAD || true)" == "$DEST_BRANCH" ]]; then
  echo "error: '$DEST_BRANCH' is checked out; switch to $SRC_REF first" >&2
  exit 1
fi
SRC_SHA="$(git rev-parse --verify "$SRC_REF^{commit}")"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "note: you have uncommitted changes; they are NOT published (only $SRC_REF @ ${SRC_SHA:0:7})" >&2
fi

WORK="$(mktemp -d /tmp/backyard_publish.XXXXXX)"
trap 'rm -rf -- "$WORK"' EXIT
TREE_DIR="$WORK/tree"
mkdir "$TREE_DIR"
git archive "$SRC_SHA" | tar -x -C "$TREE_DIR"
rm -rf -- "${TREE_DIR:?}/$PRIVATE_DIR"

# 1. Scrub text files in place (binary files are left alone and caught by step 2).
LOAD_PATTERNS='
  open my $f, "<", $ENV{PII_FILE} or die "cannot read $ENV{PII_FILE}: $!\n";
  local $/ = "\n";
  while (<$f>) {
    chomp; s/\r$//;
    next if /^\s*(#|$)/;
    my ($re, $rep) = split /\s+=>\s+/, $_, 2;
    push @P, [qr/$re/, defined $rep ? $rep : "[redacted]", $re];
  }
  die "no patterns in $ENV{PII_FILE}\n" unless @P;
'
(cd "$TREE_DIR" && grep -rIl --null '' . || true) | (cd "$TREE_DIR" && PII_FILE="$PII_FILE" xargs -0 perl -0777 -i -pe "
  BEGIN { $LOAD_PATTERNS }
  for my \$p (@P) { s/\$p->[0]/\$p->[1]/g }
")

# 2. Verify: no pattern may match any file's bytes or any path.
if ! (cd "$TREE_DIR" && find . -type f -print0 | PII_FILE="$PII_FILE" perl -0 -ne "
  BEGIN { $LOAD_PATTERNS \$bad = 0 }
  chomp; my \$path = \$_;
  open my \$fh, '<:raw', \$path or die \"\$path: \$!\n\";
  local \$/; my \$data = <\$fh>;
  for my \$p (@P) {
    if (\$path =~ \$p->[0] || \$data =~ \$p->[0]) { print STDERR \"PII still present: \$path (pattern: \$p->[2])\n\"; \$bad = 1 }
  }
  END { exit \$bad }
"); then
  echo "error: aborting; fix the files above (binary files must be fixed in $SRC_REF)" >&2
  exit 1
fi

# 3. Build a parentless commit from the scrubbed tree using a throwaway index.
TREE="$(
  cd "$TREE_DIR" &&
  GIT_INDEX_FILE="$WORK/index" git --git-dir="$GIT_DIR_ABS" --work-tree="$TREE_DIR" add -A -f . &&
  GIT_INDEX_FILE="$WORK/index" git --git-dir="$GIT_DIR_ABS" --work-tree="$TREE_DIR" write-tree
)"

OLD="$(git rev-parse -q --verify "refs/heads/$DEST_BRANCH" || true)"
if [[ -n "$OLD" && "$(git rev-parse "$OLD^{tree}")" == "$TREE" && -z "$(git rev-parse -q --verify "$OLD^" || true)" \
      && "$(git log -1 --format=%B "$OLD")" == "$COMMIT_MSG" ]]; then
  echo "$DEST_BRANCH is already up to date with $SRC_REF @ ${SRC_SHA:0:7} (${OLD:0:7}); nothing to do."
  exit 0
fi

COMMIT="$(
  GIT_AUTHOR_NAME="$AUTHOR_NAME" GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL" \
  GIT_COMMITTER_NAME="$AUTHOR_NAME" GIT_COMMITTER_EMAIL="$AUTHOR_EMAIL" \
  git commit-tree "$TREE" -m "$COMMIT_MSG"
)"
git update-ref -m "publish.sh: snapshot of $SRC_REF ${SRC_SHA:0:7}" "refs/heads/$DEST_BRANCH" "$COMMIT"

echo "$DEST_BRANCH: ${OLD:0:7} -> ${COMMIT:0:7} (scrubbed snapshot of $SRC_REF @ ${SRC_SHA:0:7}, author $AUTHOR_NAME <$AUTHOR_EMAIL>)"
echo "Review:  git show --stat $DEST_BRANCH"
echo "Publish: git push --force origin $DEST_BRANCH"
