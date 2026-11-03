`timescale 1ns/1ps
module tb_m20v23_cpu;
 import m20_pkg::*;
 `include "v23_fixture.svh"
 string case_dir,case_id,trace_path;
 integer mf,scan,cf[0:3],kf,rf,i,k,key_value;
 integer words,entry,ia,iar,iz,ic,ig,initial_keys,limit,cycle_limit,mode,rom_ps,ram_ps;
 integer cases_done=0,events,cycles,cost,writes_in_instruction;
 logic captured_retire;logic [2:0] before_state;
 integer cap_pc,cap_word,cap_addr,cap_data,cap_kind,cap_cost;
 integer pcs[0:3],words_cap[0:3],addresses[0:3],data_cap[0:3],kinds[0:3];
 integer trace_file,trace_ticks=0;logic trace_enabled=0;
 task load_memories;
  begin
   $readmemh({case_dir,"/",case_id,".rom.memh"},mem.bram.rom);$readmemh({case_dir,"/",case_id,".rom.memh"},ref_mem.bram.rom);
   $readmemh({case_dir,"/",case_id,".rom.memh"},ideal_mem.bram.rom);$readmemh({case_dir,"/",case_id,".rom.memh"},switch_mem.bram.rom);
   $readmemh({case_dir,"/",case_id,".ram.memh"},mem.bram.memory);$readmemh({case_dir,"/",case_id,".ram.memh"},ref_mem.bram.memory);
   $readmemh({case_dir,"/",case_id,".ram.memh"},ideal_mem.bram.memory);$readmemh({case_dir,"/",case_id,".ram.memh"},switch_mem.bram.memory);
   mem.rom_delay_ns=rom_ps/1000.0;ref_mem.rom_delay_ns=rom_ps/1000.0;ideal_mem.rom_delay_ns=rom_ps/1000.0;switch_mem.rom_delay_ns=rom_ps/1000.0;
   mem.ram_delay_ns=ram_ps/1000.0;ref_mem.ram_delay_ns=ram_ps/1000.0;ideal_mem.ram_delay_ns=ram_ps/1000.0;switch_mem.ram_delay_ns=ram_ps/1000.0;
   mem.write_count=0;ref_mem.write_count=0;ideal_mem.write_count=0;switch_mem.write_count=0;
  end
 endtask
 task emit(input integer fd,input integer which,input integer event_kind);
  integer pcv,av,arv,zv,cv,gv,hv,tv;
  begin
   case(which)
    0:begin pcv=dbg_pc;av=dbg_a;arv=dbg_ar;zv=dbg_z;cv=dbg_c;gv=dbg_gpo;hv=halted;tv=trapped;end
    1:begin pcv=ref_dbg_pc;av=ref_dbg_a;arv=ref_dbg_ar;zv=ref_dbg_z;cv=ref_dbg_c;gv=ref_dbg_gpo;hv=ref_halted;tv=ref_trapped;end
    2:begin pcv=ideal_dbg_pc;av=ideal_dbg_a;arv=ideal_dbg_ar;zv=ideal_dbg_z;cv=ideal_dbg_c;gv=ideal_dbg_gpo;hv=ideal_halted;tv=ideal_trapped;end
    3:begin pcv=switch_dbg_pc;av=switch_dbg_a;arv=switch_dbg_ar;zv=switch_dbg_z;cv=switch_dbg_c;gv=switch_dbg_gpo;hv=switch_halted;tv=switch_trapped;end
   endcase
   $fwrite(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",events,pcs[which],words_cap[which],pcv,av,arv,zv,cv,gv,kinds[which],kinds[which]?addresses[which]:0,kinds[which]?data_cap[which]:0,cost,cycles,event_kind,hv,tv);
  end
 endtask
 always @(posedge sys_clk)if(trace_enabled && trace_ticks<1600)begin
  $fwrite(trace_file,"%0.3f,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0h,%0h,%0h,%0h,%0h,%0d\n",$realtime,phase,master_hold,slave_open,commit_ce,rom_read_ce,ram_sample_ce,observe_ce,dbg_pc,dut.state_qm[11:0],rom_data,ram_rdata,dbg_state,overlap_seen);
  trace_ticks=trace_ticks+1;
 end
 initial begin
  if(!$value$plusargs("CASE_DIR=%s",case_dir))$fatal(1,"CASE_DIR required");
  if(!$value$plusargs("TRACE_FILE=%s",trace_path))trace_path={case_dir,"/timing_trace.csv"};
  trace_file=$fopen(trace_path,"w");$fwrite(trace_file,"time_ns,phase,master_hold,slave_open,commit_ce,rom_read_ce,ram_sample_ce,observe_ce,pc_hex,qm_pc_hex,rom_hex,ram_hex,state_hex,overlap_events\n");
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);sched_reset=0;
  mf=$fopen({case_dir,"/cases.txt"},"r");if(!mf)$fatal(1,"manifest missing");
  while(!$feof(mf))begin
   scan=$fscanf(mf,"%s %d %d %d %d %d %d %d %d %d %d %d %d %d\n",case_id,words,entry,ia,iar,iz,ic,ig,initial_keys,limit,cycle_limit,mode,rom_ps,ram_ps);
   if(scan==14)begin
    compare_enabled=0;checks_enable=0;park();rst=1;load_memories();drive_keys(initial_keys);
    reset_all();
    // Four true cold-boot scenarios use the actual latch reset sequence, no register deposit.
    if(case_id!="pong_boot" && case_id!="snake_boot" && case_id!="pong_continuous_64" && case_id!="snake_continuous_64")load_fixture(entry,ia,iar,iz,ic,ig);
    else begin if(entry!=0 || ia!=0 || iar!=0 || iz!=1 || ic!=0 || ig!=8)$fatal(1,"cold boot fixture changed");prime();end
    cf[0]=$fopen({case_dir,"/",case_id,".rtl.csv"},"w");cf[1]=$fopen({case_dir,"/",case_id,".v1.csv"},"w");
    cf[2]=$fopen({case_dir,"/",case_id,".ideal.csv"},"w");cf[3]=$fopen({case_dir,"/",case_id,".switch.csv"},"w");
    for(k=0;k<4;k=k+1)$fwrite(cf[k],"sequence,pc,word,next_pc,a,ar,z,c,gpo,ram_kind,ram_addr,ram_data,cycles,cumulative_cycles,event,halted,trapped\n");
    kf=$fopen({case_dir,"/",case_id,".keys.txt"},"r");scan=$fscanf(kf,"%d\n",key_value);if(scan!=1)$fatal(1,"keys missing");drive_keys(key_value);
    events=0;cycles=0;cost=0;writes_in_instruction=0;compare_enabled=1;checks_enable=1;trace_enabled=(cases_done==0);start();
    while(events<limit)begin
     wait_commit();cycles=cycles+1;cost=cost+1;
     if(cycles>cycle_limit)$fatal(1,"V23 cycle bound %s",case_id);
     before_state=dbg_state;captured_retire=retire_valid;cap_pc=dbg_pc;cap_word=rom_data;
     cap_kind=(retire_valid && retire_ram_valid)?(retire_ram_write?2:1):0;
     cap_addr=ram_addr;cap_data=retire_ram_write?ram_wdata:ram_rdata;cap_cost=retire_instruction_cycles;
pcs[0]=dbg_pc;words_cap[0]=rom_data;addresses[0]=ram_addr;kinds[0]=(retire_valid && retire_ram_valid)?(retire_ram_write?2:1):0;data_cap[0]=retire_ram_write?ram_wdata:ram_rdata;
pcs[1]=ref_dbg_pc;words_cap[1]=ref_rom_data;addresses[1]=ref_ram_addr;kinds[1]=(ref_retire_valid && ref_retire_ram_valid)?(ref_retire_ram_write?2:1):0;data_cap[1]=ref_retire_ram_write?ref_ram_wdata:ref_ram_rdata;
pcs[2]=ideal_dbg_pc;words_cap[2]=ideal_rom_data;addresses[2]=ideal_ram_addr;kinds[2]=(ideal_retire_valid && ideal_retire_ram_valid)?(ideal_retire_ram_write?2:1):0;data_cap[2]=ideal_retire_ram_write?ideal_ram_wdata:ideal_ram_rdata;
pcs[3]=switch_dbg_pc;words_cap[3]=switch_rom_data;addresses[3]=switch_ram_addr;kinds[3]=(switch_retire_valid && switch_retire_ram_valid)?(switch_retire_ram_write?2:1):0;data_cap[3]=switch_retire_ram_write?switch_ram_wdata:switch_ram_rdata;
     if(ram_we)writes_in_instruction=writes_in_instruction+1;
     wait_observe();check_states();
     if(captured_retire)begin
      if(cost!=cap_cost || cost!=(cap_kind?5:2))$fatal(1,"V23 cycle profile");
      if(writes_in_instruction!=(cap_kind==2?1:0))$fatal(1,"V23 RAM single write contract");
      for(k=0;k<4;k=k+1)emit(cf[k],k,0);
      events=events+1;cost=0;writes_in_instruction=0;
     end else if(trapped && before_state==S_EXEC)begin
      if(cost!=2 || writes_in_instruction!=0)$fatal(1,"V23 illegal side effect");
      cap_kind=0;for(k=0;k<4;k=k+1)kinds[k]=0;for(k=0;k<4;k=k+1)emit(cf[k],k,1);events=events+1;cost=0;
     end
     if((halted || trapped) && events<limit)$fatal(1,"V23 early stop");
     if(captured_retire && events<limit)begin scan=$fscanf(kf,"%d\n",key_value);if(scan!=1)$fatal(1,"keys schedule short");drive_keys(key_value);end
    end
    if(halted || trapped)repeat(3)begin advance();if(retire_valid || ram_ce || ram_we || ram_oe)$fatal(1,"terminal transaction");end
    park();trace_enabled=0;checks_enable=0;compare_enabled=0;
    for(k=0;k<4;k=k+1)begin
     case(k)
      0:rf=$fopen({case_dir,"/",case_id,".ram.final.memh"},"w");
      1:rf=$fopen({case_dir,"/",case_id,".v1.ram.final.memh"},"w");
      2:rf=$fopen({case_dir,"/",case_id,".ideal.ram.final.memh"},"w");
      3:rf=$fopen({case_dir,"/",case_id,".switch.ram.final.memh"},"w");
     endcase
     for(i=0;i<256;i=i+1)begin
      if(mem.bram.memory[i]!==ref_mem.bram.memory[i] || mem.bram.memory[i]!==ideal_mem.bram.memory[i] || mem.bram.memory[i]!==switch_mem.bram.memory[i])$fatal(1,"V23 final RAM index=%0d",i);
      case(k)
       0:$fwrite(rf,"%h\n",mem.bram.memory[i]);1:$fwrite(rf,"%h\n",ref_mem.bram.memory[i]);
       2:$fwrite(rf,"%h\n",ideal_mem.bram.memory[i]);3:$fwrite(rf,"%h\n",switch_mem.bram.memory[i]);
      endcase
     end
     $fclose(rf);$fclose(cf[k]);
    end
    if(mem.write_count!=ref_mem.write_count || mem.write_count!=ideal_mem.write_count || mem.write_count!=switch_mem.write_count)$fatal(1,"V23 physical write counts");
    $fclose(kf);$display("M20V23_CASE_PASS name=%s events=%0d cycles=%0d writes=%0d old_memory_mode=%0d all_bram_sync=1",case_id,events,cycles,mem.write_count,mode);cases_done=cases_done+1;
   end
  end
  $fclose(mf);$fclose(trace_file);$display("M20V23_CPU_PASS cases=%0d microcycles=%0d",cases_done,microcycles);$finish;
 end
 initial begin #2000000000;$fatal(1,"V23 CPU watchdog");end
endmodule
