#!/usr/bin/env bash
# @(#) Runs rtb for all command groups and commands and outputs overall help texts

set -euo pipefail; export FS=$'\n\t'

SOURCEDIR="redash_toolbelt/cli/commands"
FILES="$(find ${SOURCEDIR} -name '*.py' | grep -v __ | sort)"
RUN="rtb"
echo "# rtb - redash-toolbelt command line client reference"
echo ""
echo "This document lists the help texts of all commands as a reference, to search for and through it."
echo ""
for file in ${FILES}; do
    group=$(basename "$file" | cut -d "." -f 1)
    COMMANDS=$(grep "^def" "${SOURCEDIR}/${group}.py" | grep "_command" | cut -d " " -f 2 | cut -d "_" -f 1 | sort)

    echo "## Command group: ${group}"
    echo ""
    echo "\`\`\`"
    ${RUN} "${group}"
    echo "\`\`\`"
    echo ""

    for command in ${COMMANDS}; do
        echo "### Command: ${group} ${command}"
        echo ""
        echo "\`\`\`"
        ${RUN} "${group}" "${command}" --help
        echo "\`\`\`"
        echo ""
    done
done
