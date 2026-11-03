`timescale 1ns/1ps
module tb_m20v21_cpu;
    import m20_pkg::*;
    `include "m20v21_tb_fixture.svh"
    string case_dir,case_id,manifest_path;
    integer manifest,scan,csv,v1_csv,key_file,ram_file,key_value;
    integer rom_words,entry_pc,init_a,init_ar,init_z,init_c,init_gpo,initial_keys;
    integer event_limit,cycle_limit,memory_mode,rom_delay_ps,ram_delay_ps;
    integer events,cycles,instruction_cycles,writes_in_instruction,cases_done,i;
    logic [11:0] held_pc;
    logic [15:0] held_word;
    logic [3:0] held_a;
    logic [7:0] held_ar,held_addr;
    logic held_z,held_c;
    logic captured_retire;
    logic [2:0] before_state;
    logic [11:0] captured_pc,captured_next_pc;
    logic [15:0] captured_word;
    logic [3:0] captured_a,captured_gpo,captured_data;
    logic [7:0] captured_ar,captured_addr;
    logic captured_z,captured_c,captured_memory,captured_write;
    integer captured_cost,kind;
    logic [29:0] terminal_state;
    logic [11:0] captured_ref_pc;
    logic [15:0] captured_ref_word;
    logic [7:0] captured_ref_addr;
    logic [3:0] captured_ref_data;
    integer captured_ref_kind;


    task check_known_state;
        begin
            if ($isunknown({dbg_pc,dbg_ar,dbg_a,dbg_z,dbg_c,dbg_gpo,dbg_state}))
                $fatal(1,"%s CPU state contains X/Z at cycle %0d",case_id,cycles);
            if ($isunknown({ram_ce,ram_oe,ram_we,retire_valid}))
                $fatal(1,"%s bus controls contain X/Z",case_id);
            if (ram_we && (!ram_ce || ram_oe || dbg_state!=S_MEM_ACCESS))
                $fatal(1,"%s illegal write control",case_id);
            if (ram_oe && (!ram_ce || ram_we))
                $fatal(1,"%s illegal read control",case_id);
        end
    endtask

    initial begin
        if (!$value$plusargs("CASE_DIR=%s",case_dir)) $fatal(1,"+CASE_DIR is required");
        manifest_path={case_dir,"/cases.txt"};
        manifest=$fopen(manifest_path,"r");
        if (!manifest) $fatal(1,"cannot read %s",manifest_path);
        cases_done=0;
        while (!$feof(manifest)) begin
            scan=$fscanf(manifest,"%s %d %d %d %d %d %d %d %d %d %d %d %d %d\n",
                case_id,rom_words,entry_pc,init_a,init_ar,init_z,init_c,init_gpo,
                initial_keys,event_limit,cycle_limit,memory_mode,rom_delay_ps,ram_delay_ps);
            if (scan!=14) begin
                if (scan!=-1 && scan!=0) $fatal(1,"bad manifest record, fields=%0d",scan);
            end else begin
                if (event_limit<=0 || cycle_limit<=0) $fatal(1,"invalid manifest bounds");
                // Configuration and all memory initialization occur only at reset.
                lockstep_enabled=0;
                @(negedge clk);rst=1;keys=initial_keys[5:0];
                rom.load({case_dir,"/",case_id,".rom.memh"},rom_words,rom_delay_ps);
                ref_rom.load({case_dir,"/",case_id,".rom.memh"},rom_words,rom_delay_ps);
                ram.load({case_dir,"/",case_id,".ram.memh"},memory_mode,ram_delay_ps);
                ref_ram.load({case_dir,"/",case_id,".ram.memh"},memory_mode,ram_delay_ps);
                repeat(2) begin @(posedge clk);#1;
                    if (ram_ce || ram_oe || ram_we || retire_valid) $fatal(1,"reset allowed a transaction");
                end
                @(negedge clk);rst=0;
                @(posedge clk);#1;
                if (dbg_state!=S_FETCH_WAIT || dbg_pc!=0 || dbg_ar!=0 || dbg_a!=0 ||
                    dbg_z!=1 || dbg_c!=0 || dbg_gpo!=8) $fatal(1,"reset values mismatch");
                @(negedge clk);
                // Test fixture backdoor only. No functional core fixture ports/FF.
                dut.pc_reg=entry_pc[11:0];dut.ar_reg=init_ar[7:0];
                dut.a_reg=init_a[3:0];dut.z_reg=init_z[0];dut.c_reg=init_c[0];
                dut.gpo_reg=init_gpo[3:0];
                ref_dut.u_pc.value=entry_pc[11:0];ref_dut.u_ar.value=init_ar[7:0];
                ref_dut.a_reg=init_a[3:0];ref_dut.z_reg=init_z[0];ref_dut.c_reg=init_c[0];
                ref_dut.gpo_reg=init_gpo[3:0];lockstep_enabled=1;
                key_file=$fopen({case_dir,"/",case_id,".keys.txt"},"r");
                if (!key_file) $fatal(1,"missing key schedule %s",case_id);
                scan=$fscanf(key_file,"%d\n",key_value);
                if (scan!=1 || key_value<0 || key_value>63) $fatal(1,"invalid first key");
                keys=key_value[5:0];
                csv=$fopen({case_dir,"/",case_id,".rtl.csv"},"w");
                if (!csv) $fatal(1,"cannot write CSV %s",case_id);
                $fwrite(csv,"sequence,pc,word,next_pc,a,ar,z,c,gpo,ram_kind,ram_addr,ram_data,cycles,cumulative_cycles,event,halted,trapped\n");
                v1_csv=$fopen({case_dir,"/",case_id,".v1.csv"},"w");
                $fwrite(v1_csv,"sequence,pc,word,next_pc,a,ar,z,c,gpo,ram_kind,ram_addr,ram_data,cycles,cumulative_cycles,event,halted,trapped\n");
                events=0;cycles=0;instruction_cycles=0;writes_in_instruction=0;
                while (events<event_limit) begin
                    @(posedge clk);
                    cycles=cycles+1;instruction_cycles=instruction_cycles+1;
                    if (cycles>cycle_limit) $fatal(1,"%s cycle bound %0d",case_id,cycle_limit);
                    check_known_state();
                    before_state=dbg_state;
                    if (dbg_state==S_FETCH_WAIT) begin
                        if ($isunknown(rom_data)) $fatal(1,"%s unknown ROM at FETCH",case_id);
                        held_pc=dbg_pc;held_word=rom_data;held_a=dbg_a;held_ar=dbg_ar;
                        held_z=dbg_z;held_c=dbg_c;
                    end else if (dbg_state==S_EXEC || dbg_state==S_MEM_SETUP ||
                                 dbg_state==S_MEM_ACCESS || dbg_state==S_MEM_RELEASE) begin
                        if (dbg_pc!==held_pc || rom_data!==held_word)
                            $fatal(1,"%s PC/ROM changed during instruction pc=%h held=%h word=%h heldword=%h",case_id,dbg_pc,held_pc,rom_data,held_word);
                    end
                    if (dbg_state==S_MEM_SETUP) held_addr=ram_addr;
                    if (dbg_state==S_MEM_SETUP || dbg_state==S_MEM_ACCESS || dbg_state==S_MEM_RELEASE) begin
                        if (!ram_ce || ram_addr!==held_addr || dbg_a!==held_a || dbg_ar!==held_ar ||
                            dbg_z!==held_z || dbg_c!==held_c)
                            $fatal(1,"%s RAM address or source state changed before retire",case_id);
                    end
                    if (ram_we) writes_in_instruction=writes_in_instruction+1;
                    captured_retire=retire_valid;
                    captured_pc=retire_pc;captured_word=retire_instruction;
                    captured_next_pc=retire_next_pc;captured_a=retire_a;captured_ar=retire_ar;
                    captured_z=retire_z;captured_c=retire_c;captured_gpo=retire_gpo;
                    captured_memory=retire_ram_valid;captured_write=retire_ram_write;
                    captured_addr=retire_ram_addr;
                    captured_data=captured_write ? retire_ram_wdata : retire_ram_rdata;
                    captured_cost=retire_instruction_cycles;
                    captured_ref_pc=ref_retire_pc;captured_ref_word=ref_retire_instruction;
                    captured_ref_addr=ref_retire_ram_addr;
                    captured_ref_kind=ref_retire_ram_valid ? (ref_retire_ram_write?2:1):0;
                    captured_ref_data=ref_retire_ram_write ? ref_retire_ram_wdata:ref_retire_ram_rdata;
                    if (captured_retire && captured_memory && !captured_write && $isunknown(captured_data))
                        $fatal(1,"%s RAM read sample X/Z",case_id);
                    #1;
                    if (captured_retire) begin
                        if ({dbg_pc,dbg_a,dbg_ar,dbg_z,dbg_c,dbg_gpo} !==
                            {captured_next_pc,captured_a,captured_ar,captured_z,captured_c,captured_gpo})
                            $fatal(1,"%s preedge retire projection differs from committed state",case_id);
                        if (instruction_cycles!=captured_cost || captured_cost!=(captured_memory?5:2))
                            $fatal(1,"%s actual instruction cycles %0d expected %0d",case_id,instruction_cycles,captured_cost);
                        if (writes_in_instruction!=(captured_memory && captured_write ? 1:0))
                            $fatal(1,"%s ST write count %0d",case_id,writes_in_instruction);
                        kind=captured_memory ? (captured_write?2:1):0;
                        $fwrite(csv,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,0,%0d,%0d\n",
                            events,captured_pc,captured_word,dbg_pc,dbg_a,dbg_ar,dbg_z,dbg_c,dbg_gpo,
                            kind,kind?captured_addr:0,kind?captured_data:0,instruction_cycles,cycles,halted,trapped);
                        $fwrite(v1_csv,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,0,%0d,%0d\n",
                            events,captured_ref_pc,captured_ref_word,ref_dbg_pc,ref_dbg_a,ref_dbg_ar,ref_dbg_z,ref_dbg_c,ref_dbg_gpo,
                            captured_ref_kind,captured_ref_kind?captured_ref_addr:0,captured_ref_kind?captured_ref_data:0,
                            instruction_cycles,cycles,ref_halted,ref_trapped);
                        events=events+1;instruction_cycles=0;writes_in_instruction=0;
                    end else if (trapped && before_state==S_EXEC) begin
                        if (instruction_cycles!=2 || writes_in_instruction!=0 ||
                            {dbg_pc,dbg_a,dbg_ar,dbg_z,dbg_c} !== {held_pc,held_a,held_ar,held_z,held_c})
                            $fatal(1,"%s illegal instruction changed state/transaction",case_id);
                        $fwrite(csv,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,0,0,0,%0d,%0d,1,0,1\n",
                            events,held_pc,held_word,dbg_pc,dbg_a,dbg_ar,dbg_z,dbg_c,dbg_gpo,instruction_cycles,cycles);
                        $fwrite(v1_csv,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,0,0,0,%0d,%0d,1,0,1\n",
                            events,captured_ref_pc,captured_ref_word,ref_dbg_pc,ref_dbg_a,ref_dbg_ar,ref_dbg_z,ref_dbg_c,ref_dbg_gpo,instruction_cycles,cycles);
                        events=events+1;instruction_cycles=0;
                    end
                    if ((halted || trapped) && events<event_limit)
                        $fatal(1,"%s terminated early after %0d expected %0d events",case_id,events,event_limit);
                    if (captured_retire && events<event_limit) begin
                        scan=$fscanf(key_file,"%d\n",key_value);
                        if (scan!=1 || key_value<0 || key_value>63) $fatal(1,"bad key event %0d",events);
                        keys=key_value[5:0];
                    end
                end
                if (halted || trapped) begin
                    terminal_state={dbg_pc,dbg_a,dbg_ar,dbg_z,dbg_c,dbg_gpo};
                    repeat(3) begin
                        @(posedge clk);
                        if (retire_valid || ram_ce || ram_oe || ram_we) $fatal(1,"terminal state emitted transaction");
                        #1;if ({dbg_pc,dbg_a,dbg_ar,dbg_z,dbg_c,dbg_gpo}!==terminal_state)
                            $fatal(1,"terminal state changed");
                    end
                end
                ram_file=$fopen({case_dir,"/",case_id,".ram.final.memh"},"w");
                for(i=0;i<256;i=i+1) begin
                    if(ram.memory[i]!==ref_ram.memory[i]) $fatal(1,"V1/V2 final RAM mismatch index=%0d",i);
                    $fwrite(ram_file,"%01h\n",ram.memory[i]);
                end
                $fclose(ram_file);
                ram_file=$fopen({case_dir,"/",case_id,".v1.ram.final.memh"},"w");
                for(i=0;i<256;i=i+1) $fwrite(ram_file,"%01h\n",ref_ram.memory[i]);
                $fclose(ram_file);$fclose(key_file);$fclose(csv);$fclose(v1_csv);
                $display("M20V21_CASE_PASS name=%s events=%0d cycles=%0d writes=%0d mode=%0d",case_id,events,cycles,ram.write_count,memory_mode);
                cases_done=cases_done+1;
            end
        end
        $fclose(manifest);
        if (cases_done==0) $fatal(1,"empty suite");
        $display("M20V21_CPU_PASS cases=%0d lockstep_cycles=%0d",cases_done,lockstep_cycles);
        $finish;
    end
endmodule
