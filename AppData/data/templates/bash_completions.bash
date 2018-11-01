#!/bin/bash

# It would have been impossible to create this without the following post on Stack Exchange!!!
# https://unix.stackexchange.com/a/55622

type "{executable_name}" &> /dev/null &&
_get_tasks_{current_date}(){
    echo $(cd {full_path_to_app_folder}; ./app.py print_tasks)
} &&
_get_globals_{current_date}(){
    echo $(cd {full_path_to_app_folder}; ./app.py print_settings)
} &&
_decide_nospace_{current_date}(){
    # Decide if after the completion of a term should a space character should be added or not.
    # It only works on Bash, not on Zsh. Not tested in any other shell.
    if [[ ${1} == "--"*"=" ]] ; then
        type "compopt" &> /dev/null && compopt -o nospace
    fi
} &&
_backup_utils_cli_{current_date}(){
    local cur prev cmd tasks_rel globals_rel
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    prev_to_prev="${COMP_WORDS[COMP_CWORD-2]}"

    # Auto-complete items from an array.
    case $prev in
        "--task")
            tasks_rel=( $(_get_tasks_{current_date}) )
            COMPREPLY=( $( compgen -W "${tasks_rel[*]}") )
            return 0
            ;;
        "--global")
            globals_rel=( $(_get_globals_{current_date}) )
            COMPREPLY=( $( compgen -W "${globals_rel[*]}") )
            return 0
            ;;
        "-t")
            tasks_rel=( $(_get_tasks_{current_date}) )
            COMPREPLY=( $( compgen -W "${tasks_rel[*]}" -- ${cur}) )
            return 0
            ;;
        "-g")
            globals_rel=( $(_get_globals_{current_date}) )
            COMPREPLY=( $( compgen -W "${globals_rel[*]}" -- ${cur}) )
            return 0
            ;;
    esac

    # Handle --xxxxx=value
    if [[ ${prev} == "=" ]] ; then
        case $prev_to_prev in
            "--task")
                tasks_rel=( $(_get_tasks_{current_date}) )
                COMPREPLY=( $( compgen -W "${tasks_rel[*]}" -- ${cur}) )
                return 0
                ;;
            "--global")
                globals_rel=( $(_get_globals_{current_date}) )
                COMPREPLY=( $( compgen -W "${globals_rel[*]}" -- ${cur}) )
                return 0
                ;;
        esac

        return 0
    fi

    # Completion of commands and "first level" options.
    if [[ $COMP_CWORD == 1 ]]; then
        COMPREPLY=( $(compgen -W "backup generate -h --help --manual --version" -- "${cur}") )
        return 0
    fi

    # Completion of options and sub-commands.
    cmd="${COMP_WORDS[1]}"

    case $cmd in
        "backup")
            COMPREPLY=( $(compgen -W "-t --task= -g --global= -d --dry-run" -- "${cur}") )
            _decide_nospace_{current_date} ${COMPREPLY[0]}
            ;;
        "generate")
            COMPREPLY=( $(compgen -W "task global system_executable" -- "${cur}") )
            ;;
    esac
} &&
complete -F _backup_utils_cli_{current_date} {executable_name}
