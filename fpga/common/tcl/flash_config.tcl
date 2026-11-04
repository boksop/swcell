# Shared by build.tcl, program_flash.tcl and pure-Tcl timing tests.
proc swc_flash_settings {array_name} {
    upvar 1 $array_name cfg
    if {![info exists cfg(flash_enable)] || !$cfg(flash_enable)} {return [dict create enabled 0]}
    foreach key {flash_model flash_cfgmem_part flash_cfgmem_alias flash_size_mib flash_buswidth flash_transfer flash_fall_edge flash_32bit_addr flash_compress boot_mode_bits configrate_mhz flash_tco_ns fpga_spi_setup_ns cclk_tolerance flash_sdr_max_mhz fpga_cclk_max_mhz flash_board_delay_budget_ns} {
        if {![info exists cfg($key)]} {error "Missing Flash config field: $key"}
    }
    if {$cfg(boot_mode_bits) ne "001"} {error "7-series Master SPI requires physical M\[2:0\]=001"}
    if {$cfg(flash_transfer) ne "SDR"} {error "7-series hard SPI configuration supports SDR read opcodes; SPI_FALL_EDGE is not DDR/DTR"}
    if {$cfg(flash_buswidth) ni {1 2 4}} {error "Unsupported SPI bus width"}
    foreach key {flash_fall_edge flash_32bit_addr flash_compress} {
        if {![string is boolean -strict $cfg($key)]} {error "Invalid boolean: $key"}
    }
    foreach key {flash_tco_ns fpga_spi_setup_ns flash_sdr_max_mhz fpga_cclk_max_mhz} {
        if {![string is double -strict $cfg($key)] || !($cfg($key)>0.0 && $cfg($key)<1.0e6)} {error "Invalid positive timing input: $key"}
    }
    foreach key {cclk_tolerance flash_board_delay_budget_ns} {
        if {![string is double -strict $cfg($key)] || !($cfg($key)>=0.0 && $cfg($key)<1.0e6)} {error "Invalid timing budget: $key"}
    }
    if {![string is integer -strict $cfg(flash_size_mib)] || $cfg(flash_size_mib)<1 ||
        ($cfg(flash_size_mib)&($cfg(flash_size_mib)-1))!=0} {error "Flash size must be a positive power of two in MiB"}
    if {$cfg(flash_size_mib)>16 && !$cfg(flash_32bit_addr)} {error "Flash >128 Mbit requires SPI_32BIT_ADDR"}
    set timing_ns [expr {$cfg(flash_tco_ns)+$cfg(fpga_spi_setup_ns)+$cfg(flash_board_delay_budget_ns)}]
    set fraction [expr {$cfg(flash_fall_edge)?1.0:0.5}]
    set actual_limit [expr {min($cfg(flash_sdr_max_mhz),$cfg(fpga_cclk_max_mhz),1000.0*$fraction/$timing_ns)}]
    set nominal_limit [expr {$actual_limit/(1.0+$cfg(cclk_tolerance))}]
    # Vivado 2022.1 / 7-series supported CONFIGRATE values (queried from tool).
    set rates {3 6 9 12 16 22 26 33 40 50 66}
    set rate 0
    foreach candidate $rates {if {$candidate<=$nominal_limit} {set rate $candidate}}
    if {$rate==0} {error "No CONFIGRATE satisfies Flash/FPGA/board timing budget"}
    if {$cfg(configrate_mhz) ne "auto"} {
        if {$cfg(configrate_mhz) ni $rates || $cfg(configrate_mhz)>$rate} {error "Requested CONFIGRATE exceeds supported timing budget (maximum $rate MHz)"}
        set rate $cfg(configrate_mhz)
    }
    set actual_max [expr {$rate*(1.0+$cfg(cclk_tolerance))}]
    set margin [expr {1000.0*$fraction/$actual_max-$timing_ns}]
    return [dict create enabled 1 rate_mhz $rate worst_cclk_mhz $actual_max timing_ns $timing_ns margin_ns $margin         size_mib $cfg(flash_size_mib) buswidth $cfg(flash_buswidth) fall_edge $cfg(flash_fall_edge)         address32 $cfg(flash_32bit_addr) compress $cfg(flash_compress)         cfgmem_part $cfg(flash_cfgmem_part) cfgmem_alias $cfg(flash_cfgmem_alias) model $cfg(flash_model)]
}

proc swc_flash_write_xdc {settings filename} {
    set handle [open $filename w]
    set code [catch {
        puts $handle "# Generated from validated Flash configuration; do not edit build output."
        puts $handle "set_property CONFIG_MODE SPIx[dict get $settings buswidth] \[current_design\]"
        foreach {property value} [list             BITSTREAM.CONFIG.SPI_BUSWIDTH [dict get $settings buswidth]             BITSTREAM.CONFIG.SPI_FALL_EDGE [expr {[dict get $settings fall_edge]?"YES":"NO"}]             BITSTREAM.CONFIG.SPI_32BIT_ADDR [expr {[dict get $settings address32]?"YES":"NO"}]             BITSTREAM.CONFIG.CONFIGRATE [dict get $settings rate_mhz]             BITSTREAM.CONFIG.EXTMASTERCCLK_EN DISABLE             BITSTREAM.STARTUP.STARTUPCLK CCLK             BITSTREAM.GENERAL.COMPRESS [expr {[dict get $settings compress]?"TRUE":"FALSE"}]] {
            puts $handle "set_property $property $value \[current_design\]"
        }
    } result options]
    close $handle
    if {$code} {return -options $options $result}
}

proc swc_flash_write_images {settings bitfile output_dir} {
    file mkdir $output_dir
    set bitfile [file normalize $bitfile]
    set image [file join $output_dir swcell_m11]
    set interface SPIx[dict get $settings buswidth]
    foreach format {mcs bin} {
        write_cfgmem -force -format $format -interface $interface -size [dict get $settings size_mib]             -loadbit [list up 0x00000000 $bitfile] -file $image.$format
    }
    set handle [open [file join $output_dir flash_settings.rpt] w]
    set code [catch {
        foreach key [lsort [dict keys $settings]] {puts $handle "$key=[dict get $settings $key]"}
        puts $handle "start_address=0x00000000"
        puts $handle "bitfile=$bitfile"
        puts $handle "timing_budget_is_board_measurement=false"
    } result options]
    close $handle
    if {$code} {return -options $options $result}
    puts "SWCELL_FLASH_IMAGE_PASS: $image.mcs (CONFIGRATE=[dict get $settings rate_mhz] MHz, x[dict get $settings buswidth], SDR)"
}
