# Shared repository discovery; independent of CWD and the project's nesting depth.
proc swc_repo_root {script_path} {
    set dir [file dirname [file normalize $script_path]]
    while {1} {
        if {[file isfile [file join $dir AGENTS.md]] && [file isdirectory [file join $dir rtl]] && [file isdirectory [file join $dir fpga]]} {return $dir}
        set parent [file dirname $dir]
        if {$parent eq $dir} {error "Cannot locate SwCell repository from $script_path"}
        set dir $parent
    }
}
