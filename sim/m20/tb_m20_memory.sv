`timescale 1ns/1ps
module tb_m20_memory;
    import m20_pkg::*;
    `include "m20_tb_fixture.svh"
    integer i,guard,checks,writes_before;
    task reset_core;
        begin
            @(negedge clk);rst=1;
            #1ps;if (ram_we || ram_ce || retire_valid) $fatal(1,"reset did not suppress bus immediately");
            repeat(2) begin @(posedge clk);#1;end
            if (dbg_pc!=0 || dbg_ar!=0 || dbg_a!=0 || dbg_z!=1 || dbg_c!=0 || dbg_gpo!=8)
                $fatal(1,"reset register values");
            @(negedge clk);rst=0;
        end
    endtask
    task wait_state(input logic [2:0] target);
        begin
            guard=0;
            while(dbg_state!=target) begin
                @(negedge clk);guard=guard+1;
                if(guard>100) $fatal(1,"state timeout target=%0d actual=%0d",target,dbg_state);
            end
        end
    endtask
    task configure_program;
        begin
            for(i=0;i<4096;i=i+1) rom.memory[i]=16'hFFFF;
            rom.memory[0]=16'h0005; // LDI 5
            rom.memory[1]=16'h8122; // ST 22
            rom.memory[2]=16'h8022; // LD 22
            rom.memory[3]=16'hE200; // OUT
            rom.memory[4]=16'hF100; // HALT
            rom.valid_words=5;rom.read_delay_ps=1500;
            rom.configuration_changed=~rom.configuration_changed;
        end
    endtask
    initial begin
        checks=0;
        for(i=0;i<256;i=i+1) ram.memory[i]=4'hA;
        ram.mode=0;ram.read_delay_ps=2000;ram.write_count=0;
        ram.configuration_changed=~ram.configuration_changed;
        configure_program();
        reset_core();
        wait_state(S_MEM_ACCESS);
        // WE is already high, but its ACCESS->RELEASE write edge is pending.
        if (!ram_we || !ram_ce || ram_oe) $fatal(1,"pending ST did not assert WE");
        // Abort before that edge: reset must mask active WE immediately.
        rst=1;#1ps;
        if (ram_we || ram_ce || retire_valid) $fatal(1,"pending ST not immediately inhibited");
        @(posedge clk);#1;
        if (ram.memory[8'h22]!=4'hA || ram.write_count!=0) $fatal(1,"aborted ST wrote memory");
        for(i=0;i<256;i=i+1) if(ram.memory[i]!=4'hA) $fatal(1,"CPU reset cleared RAM");
        checks=checks+1;

        reset_core();
        wait_state(S_MEM_RELEASE);
        // An ST already written at ACCESS is not rolled back by later reset.
        if(ram.memory[8'h22]!=5 || ram.write_count!=1) $fatal(1,"ST did not produce one ACCESS write");
        rst=1;#1ps;if(ram_we || ram_ce) $fatal(1,"reset bus suppression after physical write");
        @(posedge clk);#1;
        if(ram.memory[8'h22]!=5 || ram.write_count!=1) $fatal(1,"reset changed earlier external write");
        checks=checks+1;

        reset_core();
        wait_state(S_HALT);
        if(dbg_a!=5 || dbg_gpo!=5 || ram.memory[8'h22]!=5 || ram.write_count!=2)
            $fatal(1,"delayed memory load/store/HALT mismatch");
        repeat(3) begin @(posedge clk);
            if(retire_valid || ram_ce || ram_we || ram_oe) $fatal(1,"HALT emitted transaction");
            #1;
        end
        checks=checks+1;

        // Recovery from HALT with synchronous-read adapter, same five cycles.
        ram.mode=1;ram.read_delay_ps=2000;
        reset_core();wait_state(S_HALT);
        if(dbg_a!=5 || dbg_gpo!=5 || ram.write_count!=3) $fatal(1,"synchronous adapter mismatch");
        checks=checks+1;

        @(negedge clk);rst=1;
        rom.memory[0]=16'hFFFF;rom.valid_words=1;
        rom.configuration_changed=~rom.configuration_changed;
        writes_before=ram.write_count;
        reset_core();wait_state(S_TRAP);
        if(dbg_pc!=0 || dbg_a!=0 || dbg_gpo!=8 || ram.write_count!=writes_before)
            $fatal(1,"TRAP state or memory side effect");
        repeat(3) begin @(posedge clk);
            if(retire_valid || ram_ce || ram_we || ram_oe) $fatal(1,"TRAP emitted transaction");#1;
        end
        checks=checks+1;

        // Mapping metadata is a test concern. FFFF remains an actual TRAP word.
        @(negedge clk);rst=1;dut.u_pc.value=12'd8;
        #3;
        if(rom_mapped || rom_data!==16'hFFFF) $fatal(1,"ROM mapping metadata/fill mismatch");
        if(ram_we || retire_valid) $fatal(1,"mapping probe changed functional interface");
        checks=checks+1;
        rom.memory[0]=16'hF100;rom.configuration_changed=~rom.configuration_changed;
        reset_core();wait_state(S_HALT);
        if(dbg_pc!=1 || dbg_gpo!=8 || ram.write_count!=writes_before)
            $fatal(1,"reset recovery from TRAP mismatch");
        checks=checks+1;
        $display("M20_MEMORY_PASS checks=%0d async_rom_ps=1500 async_ram_ps=2000 sync_ram_ps=2000 reset_abort=1 reset_after_write=1 mapping_metadata=1",checks);
        $finish;
    end
    initial begin #100000; $fatal(1,"memory unit watchdog");end
endmodule
