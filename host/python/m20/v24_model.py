"""Independent one-reference-edge abstract control model, not a latch timing model."""
LEGAL={0,1,3,7,15,14,12,8}
NAMES=['j0','j1','j2','j3','run1','run2','step1','step2','token','ack','active','step_mode','fault_reg']
def transition(old,*,rst,run_request,step_request):
 if rst:return {k:int(k=='j3') for k in NAMES}
 q=sum(old['j'+str(i)]<<i for i in range(4));safe=q==8
 bad=q not in LEGAL or (not old['active'] and not safe)
 pending=old['step2']!=old['token'];complete=bool(old['active'] and safe and old['step_mode'])
 start=bool(safe and not old['fault_reg'] and not bad and (old['run2'] if complete else old['run2'] or pending))
 accept=start and not old['run2'] and pending and not complete
 nxt=dict(old);nxt.update(run1=run_request,run2=old['run1'],step1=step_request,step2=old['step1'])
 if old['fault_reg']:q2=8
 elif not bad and ((old['active'] and not safe) or start):q2=((q<<1)&15)|(1-(q>>3))
 else:q2=q
 for i in range(4):nxt['j'+str(i)]=(q2>>i)&1
 if accept:nxt['token']=old['step2']
 if complete:nxt['ack']=old['token']
 nxt['active']=0 if old['fault_reg'] or bad else int(start) if safe else old['active']
 nxt['step_mode']=0 if old['fault_reg'] or bad else int(start and not old['run2'] and pending and not complete) if safe else old['step_mode']
 nxt['fault_reg']=int(old['fault_reg'] or bad)
 return nxt
