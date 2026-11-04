`timescale 1ns/1ps
module tb_m20_v3_selftest #(parameter PONG_FILE="",SNAKE_FILE="",parameter integer EXPECT_TRAP=0);
 reg clk=0;always #10 clk=~clk;reg power_reset=1;
 wire active,halted,trapped;wire[63:0] microcycles,retired,reads,writes,errors;
 wire[11:0] pc;wire[7:0] ar;wire[3:0] accumulator,gpo;wire z,c;wire[2:0] ustate;
 swc_m20_v3_system #(.PONG_FILE(PONG_FILE),.SNAKE_FILE(SNAKE_FILE)) dut(
  .clk(clk),.power_reset(power_reset),.reset_request(1'b0),.select_request(1'b0),.select_game(1'b0),
  .run_toggle(1'b0),.step_request(1'b0),.speed_request(1'b0),.speed_ticks(16'd50),.keys(6'b0),
  .active(active),.halted(halted),.trapped(trapped),.pc(pc),.ar(ar),.accumulator(accumulator),.gpo(gpo),.z(z),.c(c),.ustate(ustate),
  .microcycles(microcycles),.retired(retired),.reads(reads),.writes(writes),.errors(errors));
 string outdir=".";integer f;
 initial begin
  if($value$plusargs("OUT=%s",outdir))begin end
  repeat(5)@(negedge clk);power_reset=0;
  wait(halted||trapped);wait(!active);#1;
  if(errors!=0||trapped!==1'(EXPECT_TRAP)||halted!==!1'(EXPECT_TRAP))$fatal(1,"V3_SELFTEST_TERMINAL");
  $writememh({outdir,"/final_ram.memh"},dut.memory.memory);
  f=$fopen({outdir,"/final_state.json"},"w");
  $fdisplay(f,"{\"pc\":%0d,\"ar\":%0d,\"a\":%0d,\"z\":%0d,\"c\":%0d,\"gpo\":%0d,\"micro\":%0d,\"retired\":%0d,\"writes\":%0d,\"reads\":%0d,\"ustate\":%0d}",pc,ar,accumulator,z,c,gpo,microcycles,retired,writes,reads,ustate);
  $fclose(f);$display("M20_V3_DIAGNOSTIC_ROM_PASS trap=%0d retired=%0d micro=%0d",EXPECT_TRAP,retired,microcycles);$finish;
 end
 initial begin #100000000;$fatal(1,"V3_SELFTEST_TIMEOUT");end
endmodule
