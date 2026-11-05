`timescale 1ns/1ps
module tb_m20_v31_gpio;
 logic clk=0;always #10 clk=~clk;
 logic power_reset=1,KEY0=1,KEY1=1,KEY2=1,KEY3=1,KEY5=1,KEY6=1;
 logic[3:0] gpo=8;wire[5:0] keys;wire oled_cs_n,oled_dc,oled_sck,oled_mosi;
 swc_m20_v31_gpio dut(.*);
 initial begin
  repeat(3)@(negedge clk);power_reset=0;
  for(integer k=0;k<6;k=k+1)begin
   @(negedge clk);{KEY6,KEY5,KEY1,KEY3,KEY0,KEY2}=~(6'b1<<k);
   @(posedge clk);#1;if(keys!==0)$fatal(1,"GPIO_STAGE1 %d",k);
   @(negedge clk);{KEY6,KEY5,KEY1,KEY3,KEY0,KEY2}=6'b111111;
   @(posedge clk);#1;if(keys!==(6'b1<<k))$fatal(1,"GPIO_MAPPING_OR_FILTER %d",k);
   @(posedge clk);#1;if(keys!==0)$fatal(1,"GPIO_PULSE_LENGTH %d",k);
  end
  for(integer value=0;value<16;value=value+1)begin
   gpo=value;#1;if({oled_cs_n,oled_dc,oled_sck,oled_mosi}!==gpo)$fatal(1,"GPIO_DIRECT %d",value);
  end
  $display("M20_V31_GPIO_PASS six_single_cycle_pulses=6 gpo_patterns=16");$finish;
 end
endmodule

module tb_m20_v31_memory #(parameter ROM_FILE="");
 logic clk=0;always #10 clk=~clk;
 logic cancel=0,rom_req=0,ram_req=0,write_ce=0;
 logic[11:0] rom_addr=0;wire[15:0] rom_data;
 logic[7:0] ram_addr=0;logic[3:0] ram_wdata=0;logic ram_ce=0,ram_oe=0,ram_we=0;
 wire[3:0] ram_data;wire write_commit,read_commit;
 swc_m20_v31_memory #(.ROM_FILE(ROM_FILE)) dut(.*);
 integer writes=0,reads=0;
 always @(posedge clk)begin if(write_commit)writes=writes+1;if(read_commit)reads=reads+1;end
 initial begin
  dut.memory[43]=4;
  @(negedge clk);rom_req=1;rom_addr=1;
  @(negedge clk);rom_req=0;rom_addr=2;
  @(negedge clk);if(rom_data!==dut.rom[1])$fatal(1,"ROM_ADDRESS_HOLD");
  ram_req=1;ram_addr=42;ram_wdata=9;ram_ce=1;ram_we=1;
  @(negedge clk);ram_req=0;ram_addr=43;ram_wdata=2;
  repeat(3)@(negedge clk);write_ce=1;
  repeat(3)@(negedge clk);write_ce=0;
  if(writes!=1||dut.memory[42]!==9||dut.memory[43]!==4)$fatal(1,"RAM_WRITE_ONCE");
  ram_req=1;ram_addr=42;ram_we=0;ram_oe=1;
  @(negedge clk);ram_req=0;ram_addr=43;
  @(negedge clk);if(ram_data!==9||reads!=1)$fatal(1,"RAM_READ_HOLD");
  ram_req=1;ram_we=1;ram_oe=0;
  @(negedge clk);ram_req=0;cancel=1;write_ce=1;
  repeat(3)@(negedge clk);cancel=0;write_ce=0;
  if(writes!=1||dut.memory[42]!==9||dut.memory[43]!==4)$fatal(1,"RAM_CANCEL_OR_RESET_CLEAR");
  $display("M20_V31_MEMORY_PASS sampled_address read_hold write_once cancel no_hardware_clear");$finish;
 end
endmodule

module tb_m20_v31_control #(parameter ROM_FILE="");
 logic clk=0;always #10 clk=~clk;
 logic power_reset=1,reset_request=0,run_toggle=0,step_request=0;
 logic[5:0] keys=0;wire active,run_requested,cpu_reset;
 wire[11:0] pc;wire[2:0] ustate;wire[3:0] gpo;
 wire[63:0] writes,microcycles,errors;
 swc_m20_v31_service #(.ROM_FILE(ROM_FILE)) dut(
  .clk(clk),.power_reset(power_reset),.start_enable(1'b1),.reset_request(reset_request),.run_toggle(run_toggle),.step_request(step_request),.keys(keys),
  .active(active),.run_requested(run_requested),.cpu_reset(cpu_reset),.pc(pc),.ustate(ustate),.gpo(gpo),
  .writes(writes),.microcycles(microcycles),.errors(errors));
 logic[63:0] saved_writes,saved_micro;
 task pulse_reset;
  @(negedge clk);reset_request=1;@(negedge clk);reset_request=0;
 endtask
 task step;
  saved_micro=microcycles;@(negedge clk);step_request=1;@(negedge clk);step_request=0;
  wait(active);wait(!active);@(negedge clk);
  if(microcycles!=saved_micro+1)$fatal(1,"CONTROL_STEP");
 endtask
 initial begin
  repeat(4)@(negedge clk);power_reset=0;
  // Program: LDI9 ST42 HALT. Stop on the pending ST before physical commit.
  wait(dut.ram_we&&dut.phase==10);@(negedge clk);run_toggle=1;
  @(negedge clk);run_toggle=0;wait(!active&&!run_requested);@(negedge clk);
  saved_writes=writes;
  repeat(100)@(negedge clk);if(writes!=saved_writes)$fatal(1,"CONTROL_STOP_WRITE");
  if(writes!=1||dut.memory.memory[42]!==9)$fatal(1,"CONTROL_ST_LOST");
  step();step(); // Finish the memory instruction and next FETCH.
  @(negedge clk);run_toggle=1;@(negedge clk);run_toggle=0;
  wait(dut.halted&&!active);if(writes!=1||errors!=0)$fatal(1,"CONTROL_HALT");
  pulse_reset();wait(cpu_reset);wait(!cpu_reset&&dut.warm_cycles==0&&!active);
  if(pc!==0||ustate!==1||gpo!==8||writes!=1)$fatal(1,"CONTROL_STOPPED_RESET");
  step();step();if(pc!==1)$fatal(1,"CONTROL_RESET_RESUME");
  // Environmental ROM fault injection; never alters CPU code or ISA.
  dut.memory.rom[0]=16'hffff;pulse_reset();wait(cpu_reset);wait(!cpu_reset&&dut.warm_cycles==0&&!active);
  @(negedge clk);run_toggle=1;@(negedge clk);run_toggle=0;
  wait(dut.trapped&&!active);if(pc!==0||writes!=1)$fatal(1,"CONTROL_TRAP");
  pulse_reset();wait(cpu_reset);wait(!cpu_reset&&dut.warm_cycles==0&&!active);
  if(ustate!==1||pc!==0||gpo!==8)$fatal(1,"CONTROL_TRAP_RESET");
  $display("M20_V31_CONTROL_PASS stop_pending_write step halt trap reset");$finish;
 end
 initial begin #10000000;$fatal(1,"CONTROL_TIMEOUT pc=%h state=%d",pc,ustate);end
endmodule
