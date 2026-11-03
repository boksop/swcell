"""M20 V2.1 deterministic explicit-MUX generator.
Formalized from reviewed candidate; illegal EXEC low state bit corrected.
No execution logic is implemented by FPGA operators: only emitted 157 cells.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]
class Network:
    def __init__(self):
        self.nodes = {}    # id => (select, zero, one, semantic_group)
        self.cache = {}
        self.origins = {}
        self.inputs = set()
        self.group = 'misc'
    def var(self, name):
        self.inputs.add(name); return name
    def M(self, s, a, b):
        if s in (0,1): return a if s==0 else b
        if a == b: return a
        if (a,b)==(0,1): return s
        # Cancellation / canonical equivalent select forms.
        if s==a: return self.A(s,b)
        if s==b: return self.O(s,a)
        key=(s,a,b)
        if key in self.cache: return self.cache[key]
        name='n%04d' % len(self.nodes)
        self.cache[key]=name
        self.nodes[name]=(s,a,b,self.group)
        return name
    def N(self,a):
        if a in (0,1): return 1-a
        return self.M(a,1,0)
    def A(self,a,b):
        if 0 in (a,b): return 0
        if a==1: return b
        if b==1: return a
        if a==b: return a
        if a==self.N(b): return 0
        x,y=sorted((a,b),key=str)
        return self.M(x,0,y)
    def O(self,a,b):
        if 1 in (a,b): return 1
        if a==0: return b
        if b==0: return a
        if a==b: return a
        if a==self.N(b): return 1
        x,y=sorted((a,b),key=str)
        return self.M(x,y,1)
    def X(self,a,b):
        if a==b: return 0
        if a==0: return b
        if b==0: return a
        if a==1: return self.N(b)
        if b==1: return self.N(a)
        return self.M(a,b,self.N(b))
    def AND(self,*arr):
        q=1
        for i in arr: q=self.A(q,i)
        return q
    def OR(self,*arr):
        q=0
        for i in arr: q=self.O(q,i)
        return q
    def eq(self,bits,value):
        if len(bits)>2:
            mid=len(bits)//2
            return self.A(self.eq(bits[:mid],value & ((1<<mid)-1)),self.eq(bits[mid:],value>>mid))
        return self.AND(*(bit if (value>>idx)&1 else self.N(bit) for idx,bit in enumerate(bits)))
    def z(self,bits): return self.N(self.OR(*bits))
    def mux_vec(self,sel,a,b): return [self.M(sel,x,y) for x,y in zip(a,b)]
    def select_or(self,terms):
        return self.OR(*(self.A(c,x) for c,x in terms))
    def inc(self,bits):
        carry=1; result=[]
        for bit in bits:
            result.append(self.X(bit,carry)); carry=self.A(bit,carry)
        return result
    def get_used(self,roots):
        active=set()
        def rec(x):
            if x not in self.nodes or x in active: return
            active.add(x)
            for i in self.nodes[x][:3]:rec(i)
        for x in roots:rec(x)
        return active
    def evaluate(self, values, outs):
        cache={0:0,1:1}
        def calc(x):
            if x in cache:return cache[x]
            if x in values:return values[x]
            s,a,b,_=self.nodes[x]
            r=calc(b) if calc(s) else calc(a)
            cache[x]=r
            return r
        return {k:calc(n) for k,n in outs.items()}


def construct():
    N=Network()
    P=[N.var(f'pc[{i}]') for i in range(12)]
    R=[N.var(f'ar[{i}]') for i in range(8)]
    A=[N.var(f'a[{i}]') for i in range(4)]
    Z=N.var('z'); C=N.var('c'); G=[N.var(f'gpo[{i}]') for i in range(4)]
    U=[N.var(f'u[{i}]') for i in range(3)]
    W=[N.var(f'rom_data[{i}]') for i in range(16)]
    D=[N.var(f'ram_rdata[{i}]') for i in range(4)]
    K=[N.var(f'keys[{i}]') for i in range(6)]
    rst=N.var('rst')
    lo=W[0:4]; aa=W[0:8]; sub=W[8:12]; maj=W[12:16]
    
    N.group='decode'
    m=[N.eq(maj,i) for i in range(16)]
    s=[N.eq(sub,i) for i in range(16)]
    hi0=N.z(W[4:12]); addr0=N.z(aa); subok=N.O(N.N(sub[3]),N.A(N.N(sub[2]),N.N(sub[1])));
    isram=N.OR(m[8],m[9]); direct=m[8]
    ramvalid=N.AND(isram,subok,N.OR(m[8],addr0))
    auxvalid=N.AND(m[7],addr0,N.OR(*s[:3]))
    arvalid=N.AND(m[10], N.OR(N.AND(N.OR(s[0],s[1]),N.z(W[4:8])),N.AND(N.OR(*s[2:7]),addr0)))
    iovalid=N.AND(m[14],addr0,N.OR(*s[:3]));sysvalid=N.AND(m[15],addr0,N.OR(*s[:2]))
    immvalid=N.AND(N.OR(*m[:7]),hi0)
    legal=N.OR(immvalid,auxvalid,ramvalid,arvalid,m[11],m[12],m[13],iovalid,sysvalid)
    # RAM class decode bits for opcode compact control; valid used as master gate.
    load=N.OR(m[0],N.AND(isram,s[0])); store=N.AND(isram,s[1]);
    add=N.OR(m[1],N.AND(isram,s[2])); adc=N.OR(m[2],N.AND(isram,s[3]));
    subtr=N.OR(m[3],N.AND(isram,s[4])); sbc=N.OR(m[4],N.AND(isram,s[5]));cmp=N.AND(isram,s[6]);
    and_op=N.OR(m[5],N.AND(isram,s[7])); xor_op=N.OR(m[6],N.AND(isram,s[8]));or_op=N.AND(isram,s[9]);
    shl=N.AND(m[7],s[0]);shr=N.AND(m[7],s[1]);notop=N.AND(m[7],s[2]);
    movalo=N.AND(m[10],s[4]);movahi=N.AND(m[10],s[5]);
    in0=N.AND(m[14],s[0]);in1=N.AND(m[14],s[1]);out=N.AND(m[14],s[2]);
    arl=N.AND(m[10],N.OR(s[0],s[2]));arh=N.AND(m[10],N.OR(s[1],s[3]));arinc=N.AND(m[10],s[6]);
    # no true 1-hot decoder is needed for all 45 instruction variants.
    
    N.group='control'
    S_reset=N.eq(U,0);S_fetch=N.eq(U,1);S_exec=N.eq(U,2);S_setup=N.eq(U,3);S_access=N.eq(U,4);S_release=N.eq(U,5);S_halt=N.eq(U,6);S_trap=N.eq(U,7)
    ram_exec=N.AND(S_exec,legal,isram)
    normal_exec=N.AND(S_exec,legal,N.N(isram))
    ram_release=N.AND(S_release,legal,isram)
    commit=N.AND(N.OR(normal_exec,ram_release),N.N(rst))
    trap=N.AND(S_exec,N.N(legal)); halt_instr=N.AND(S_exec,legal,m[15],s[1])
    # 3-bit next-state using compact state transition predicates (no wide state mux)
    # RESET->FETCH (1), FETCH->EXEC (2), EXEC->SETUP(3)/FETCH(1)/HALT(6)/TRAP(7), SETUP->ACCESS(4), ACCESS->RELEASE(5), RELEASE->FETCH(1), HALT->HALT, TRAP->TRAP
    state_nex=[
     N.OR(S_reset, N.AND(S_exec,N.N(ram_exec),N.N(halt_instr)), ram_exec,S_access,S_release,S_trap),
     N.OR(S_fetch,ram_exec,halt_instr,trap,S_halt,S_trap),
     N.OR(S_setup,S_access,halt_instr,trap,S_halt,S_trap)]
    # state_nex: EXEC normal=001, ram=011, illegal=111, halt=110, HALT=110, TRAP=111
    N.group='alu'
    isarith=N.OR(add,adc,subtr,sbc,cmp)
    issub=N.OR(subtr,sbc,cmp)
    operand=N.mux_vec(isram,lo,D)
    carry_in=N.M(issub,N.A(adc,C),N.OR(N.N(sbc),C))
    b_eff=[N.X(x,issub) for x in operand]
    carry=carry_in; sums=[]
    for a,b in zip(A,b_eff):
        p=N.X(a,b); sums.append(N.X(p,carry)); carry=N.M(p,a,carry)
    carry_result=carry
    xors=[N.X(a,b) for a,b in zip(A,operand)]
    ands=[N.A(a,b) for a,b in zip(A,operand)]
    ors=[N.O(a,b) for a,b in zip(A,operand)]
    # one-hot algebraic sum for 10 result classes avoids cascaded 10-input MUX select
    N.group='result'
    from_rom0=N.N(isram)
    # load result from operand; arithmetic result; shift; logic; NOT; AR read; key input
    out_bits=[]
    sel_logic=N.OR(and_op,xor_op,or_op)
    sel_arread=N.OR(movalo,movahi)
    sel_aux=N.OR(shl,shr,notop)
    sel_in=N.OR(in0,in1)
    sel_xor_or=N.M(isram,m[6],sub[3])
    for i in range(4):
        v_log=N.M(sub[0],xors[i],ors[i])
        v_log=N.M(sel_xor_or,ands[i],v_log)
        v_aux=N.M(sub[0], A[i-1] if i else 0, A[i+1] if i<3 else 0)
        v_aux=N.M(sub[1],v_aux,N.N(A[i]))
        v_ar=N.M(movahi,R[i],R[i+4])
        v_key=N.M(in1,K[i],K[i+4] if i<2 else 0)
        v=N.M(isarith,operand[i],sums[i]); v=N.M(sel_logic,v,v_log)
        v=N.M(sel_aux,v,v_aux);v=N.M(sel_arread,v,v_ar);v=N.M(sel_in,v,v_key)
        out_bits.append(v)
    
    N.group='flags'
    z_input=N.z(out_bits)  # CMP already selects subtraction result but A_we remains low
    c_input=N.M(N.OR(shl,shr),carry_result,N.M(shr,A[3],A[0]))
    a_kind=N.OR(N.OR(*m[:8]),N.A(isram,N.N(N.OR(s[1],s[6]))),N.A(m[10],N.OR(s[4],s[5])),N.A(m[14],N.OR(s[0],s[1])))
    z_kind=N.OR(N.OR(*m[:8]),N.A(isram,N.N(s[1])))
    c_kind=N.OR(isarith,shl,shr)
    a_we=N.A(commit,a_kind);z_we=N.A(commit,z_kind);c_we=N.A(commit,c_kind)
    
    N.group='pc'
    pinc=N.inc(P)
    branch_taken=N.OR(m[11],N.A(m[12],Z),N.A(m[13],C))
    branch_t=N.A(branch_taken,commit)
    # on commit choose branch address vs increment, otherwise hold
    pc_new=[]
    for i in range(12):
        change=N.M(branch_t,pinc[i],W[i]); change=N.M(commit,P[i],change)
        pc_new.append(N.M(rst,change,0))
    
    N.group='ar'
    rin=N.inc(R)
    ar_we_lo=N.A(commit,arl);ar_we_hi=N.A(commit,arh);ar_step=N.A(commit,arinc)
    source_ar=[N.M(sub[0] if False else W[9],lo[i],A[i]) for i in range(4)] # sub s0,1 low nibble or s2,3 from A: word bit9
    # source_ar = bit9 ? A : immediate
    ar_new=[]
    for i in range(8):
        source=source_ar[i%4]; step=N.M(ar_step,R[i],rin[i]);
        value=N.M(ar_we_lo if i<4 else ar_we_hi,step,source)
        ar_new.append(N.M(rst,value,0))
    
    N.group='storage'
    a_new=[N.M(rst,N.M(a_we,A[i],out_bits[i]),0) for i in range(4)]
    z_new=N.M(rst,N.M(z_we,Z,z_input),1)
    c_new=N.M(rst,N.M(c_we,C,c_input),0)
    gpo_new=[N.M(rst,N.M(N.A(commit,out),G[i],A[i]),((8>>i)&1)) for i in range(4)]
    state_new=[N.M(rst,state_nex[i],0) for i in range(3)]
    
    N.group='bus'
    ram_addr=N.mux_vec(m[9],W[:8],R)
    ram_ce=N.AND(isram,legal,N.OR(S_setup,S_access,S_release),N.N(rst))
    ram_oe=N.AND(ram_ce,N.N(store))
    ram_we=N.AND(ram_ce,store,S_access)
    
    outs={}
    for key,vect in [('pc_next',pc_new),('ar_next',ar_new),('a_next',a_new),('gpo_next',gpo_new),('u_next',state_new),('ram_addr',ram_addr)]:
        for idx,x in enumerate(vect):outs[f'{key}[{idx}]']=x
    outs.update(z_next=z_new,c_next=c_new,ram_ce=ram_ce,ram_oe=ram_oe,ram_we=ram_we,
                legal=legal,retire_valid=commit,trap_event=N.A(trap,N.N(rst)))
    # actual RAM address, no CE when invalid (even if address not defined)
    outs.update(halted=S_halt, trapped=S_trap, debug_legal=legal)
    return N, outs, dict(isram=isram, store=store, not_isram=N.N(isram))

REGS={'pc':('pc_reg',12,0),'ar':('ar_reg',8,0),'a':('a_reg',4,0),
      'z':('z_reg',1,1),'c':('c_reg',1,0),'gpo':('gpo_reg',4,8),'u':('state_reg',3,0)}
INPUTS=dict(clk=1,rst=1,keys=6,rom_data=16,ram_rdata=4)

def generate(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    n,old,meta=construct()
    rename={k:v[0] for k,v in REGS.items()}
    def signal(x):
        if type(x) is int:return str(x)
        return re.sub(r'^([a-z]+)(?=\[|$)',lambda m:rename.get(m[0],m[0]),x)
    def vec(key,w):return [signal(old[key+(f'[{i}]' if w>1 else '')]) for i in range(w)]
    regs=[dict(name=name,width=w,qbits=[name+(f'[{i}]' if w>1 else '') for i in range(w)],
               dbits=vec(k+'_next',w),reset_value=rv) for k,(name,w,rv) in REGS.items()]
    outs={name:vec(name,w) for name,w in [('ram_addr',8),('ram_ce',1),('ram_oe',1),('ram_we',1),
          ('retire_valid',1),('trap_event',1),('halted',1),('trapped',1),('debug_legal',1)]}
    regmap={r['name']:r for r in regs}
    for port,reg in [('rom_addr','pc_reg'),('ram_wdata','a_reg'),('dbg_pc','pc_reg'),('dbg_ar','ar_reg'),
                     ('dbg_a','a_reg'),('dbg_z','z_reg'),('dbg_c','c_reg'),('dbg_gpo','gpo_reg'),('dbg_state','state_reg')]:
        outs[port]=regmap[reg]['qbits']
    outs['retire_pc']=outs['dbg_pc'];outs['retire_instruction']=[f'rom_data[{i}]' for i in range(16)]
    for port,reg in [('retire_next_pc','pc_reg'),('retire_ar','ar_reg'),('retire_a','a_reg'),
                     ('retire_z','z_reg'),('retire_c','c_reg'),('retire_gpo','gpo_reg'),('debug_next_state','state_reg')]:
        outs[port]=regmap[reg]['dbits']
    # Retire payload is specified when retire_valid=1, as in V2 shared.
    outs.update(retire_is_memory=[signal(meta['isram'])],retire_ram_valid=[signal(meta['isram'])],
                retire_ram_write=[signal(meta['store'])],retire_ram_addr=outs['ram_addr'],
                retire_ram_wdata=outs['ram_wdata'],retire_ram_rdata=[f'ram_rdata[{i}]' for i in range(4)],
                retire_instruction_cycles=[signal(meta[k]) for k in ('isram','not_isram','isram')])
    used=n.get_used(old.values())
    nodes=[dict(id=k,y=k,s=signal(s),i0=signal(a),i1=signal(b),group=g,
                instance=f'g_{g}.u_{k}') for k,(s,a,b,g) in n.nodes.items() if k in used]
    assert len(nodes)==477
    def ref(x):return "1'b"+x if x in ('0','1') else x
    def expression(bits):return ref(bits[0]) if len(bits)==1 else '{'+','.join(ref(b) for b in reversed(bits))+'}'
    ports=[f'    input wire '+(f'[{w-1}:0] ' if w>1 else '')+k for k,w in INPUTS.items()]
    ports += [f'    output wire '+(f'[{len(v)-1}:0] ' if len(v)>1 else '')+k for k,v in outs.items()]
    lines=['`default_nettype none','// Generated by m20.v21_build. Retire payload valid only at retire_valid.',
           'module m20v21_cpu_core (',',\n'.join(ports),');']
    lines += ['    logic '+(f'[{r["width"]-1}:0] ' if r['width']>1 else '')+r['name']+';' for r in regs]
    lines += [f'    wire {x["id"]};' for x in nodes]
    lines += ['    generate']
    for g in dict.fromkeys(x['group'] for x in nodes):
        lines += [f'      if (1) begin : g_{g}']
        lines += [f'        swc_mux157 u_{x["id"]} (.s({ref(x["s"])}), .i0({ref(x["i0"])}), .i1({ref(x["i1"])}), .y({x["y"]}));' for x in nodes if x['group']==g]
        lines += ['      end']
    lines += ['    endgenerate']
    lines += [f'    assign {k} = {expression(v)};' for k,v in outs.items()]
    for r in regs:lines += ['    always_ff @(posedge clk) begin',f'        {r["name"]} <= {expression(r["dbits"])};','    end']
    lines += ['endmodule','`default_nettype wire','']
    text='\n'.join(lines);(output/'m20v21_cpu_core.sv').write_text(text)
    net=dict(schema_version=1,module='m20v21_cpu_core',inputs=INPUTS,outputs=outs,registers=regs,nodes=nodes,
             functional_outputs={k:outs[k] for k in ('rom_addr','ram_addr','ram_wdata','ram_ce','ram_oe','ram_we')},
             source_sha256=hashlib.sha256(text.encode()).hexdigest(),physical_mux_count=len(nodes),ff_bits=33,
             group_counts=dict(sorted(Counter(x['group'] for x in nodes).items())),
             isa='M20-300-ISA-0.1',timing_profile='M20-300-V1-TIMING-0.1',
             origin='Reviewed candidate, corrected EXEC illegal transition; no added functional state',
             generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'m20v21_cpu_core.netlist.json').write_text(json.dumps(net,indent=2)+'\n')
    print('M20V21_GENERATED mux=477 state=33 total=543')
    return net

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'rtl/m20/v21/generated')
    a=p.parse_args();dest=a.output.resolve()
    for old in (ROOT/'rtl/m20/v2',ROOT/'rtl/m20'):
        if dest==old.resolve():p.error('refusing baseline directory')
    if (ROOT/'rtl/m20/v2').resolve() in dest.parents:p.error('refusing V2 baseline')
    generate(dest)
if __name__=='__main__':main()
