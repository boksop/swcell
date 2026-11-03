"""Build the complete V1 4-bit ALU semantics using only MUX DAG nodes.

No arithmetic here is executed on runtime CPU data by Python: the arithmetic
operators only construct node topology or handle build-time indices/constants.
One 4-bit add/sub datapath is shared by ADD/ADC/SUB/SBC/CMP in both variants.
"""

OP = dict(LOAD=0, ADD=1, ADC=2, SUB=3, SBC=4, CMP=5, AND=6, XOR=7, OR=8,
          NOT=9, SHL=10, SHR=11, ST=12, ARL=13, ARH=14, MOVARL=15,
          MOVARH=16, MOVA_ARL=17, MOVA_ARH=18, INCAR=19, JMP=20,
          JZ=21, JC=22, IN0=23, IN1=24, OUT=25, NOP=26, HALT=27, INVALID=63)


def build_alu(circuit, op_bits, a, operand, c_in, *, group="alu", selects=None):
    """Return result/Z/C plus three independent write-enables.

    Inputs are LSB-first vectors, lengths 6/4/4. Optional selects maps the V1
    internal numeric op to a strict decoder's one-hot signal. It avoids a
    needless one-hot -> op6 -> one-hot roundtrip in the full CPU. The standalone
    ALU uses its own MUX-built equality network, including all 64 op values.
    """
    op_bits, a, operand = list(op_bits), list(a), list(operand)
    if len(op_bits) != 6 or len(a) != 4 or len(operand) != 4:
        raise ValueError("ALU requires op6, A4 and operand4 vectors")
    control = dict(group=group + ".decode", category="control")
    arithmetic = dict(group=group + ".arithmetic", category="alu")
    logic = dict(group=group + ".logic", category="alu")
    choice = dict(group=group + ".result", category="selection")
    flags = dict(group=group + ".flags", category="control")
    active_ops = list(range(12)) + [17, 18, 23, 24]
    if selects is None:
        hit = {op: circuit.eq_const(op_bits, op, **control) for op in active_ops}
    else:
        hit = {op: selects.get(op, 0) for op in active_ops}

    def any_op(values, **labels):
        return circuit.reduce_or((hit[op] for op in values), **labels)

    sub_mode = any_op((3, 4, 5), **control)
    use_old_carry = any_op((2, 4), **control)
    first_carry = circuit.mux(use_old_carry, sub_mode, c_in, **arithmetic)
    adjusted_operand = [circuit.mux(sub_mode, bit, circuit.inv(bit, **arithmetic),
                                    **arithmetic) for bit in operand]
    arithmetic_result, arithmetic_carry = circuit.add_bits(a, adjusted_operand,
                                                          cin=first_carry, **arithmetic)
    and_result = [circuit.and_(left, right, **logic) for left, right in zip(a, operand)]
    xor_result = [circuit.xor_(left, right, **logic) for left, right in zip(a, operand)]
    or_result = [circuit.or_(left, right, **logic) for left, right in zip(a, operand)]
    not_result = [circuit.inv(bit, **logic) for bit in a]
    shl_result, shr_result = [0] + a[:3], a[1:] + [0]
    functions = [(any_op((0, 17, 18, 23, 24), **control), operand),
                 (any_op((1, 2, 3, 4, 5), **control), arithmetic_result),
                 (hit[6], and_result), (hit[7], xor_result), (hit[8], or_result),
                 (hit[9], not_result), (hit[10], shl_result), (hit[11], shr_result)]
    result = list(a)
    for selected, data in functions:
        result = [circuit.mux(selected, previous, bit, **choice)
                  for previous, bit in zip(result, data)]
    c_out = circuit.mux(any_op((1, 2, 3, 4, 5), **flags), c_in, arithmetic_carry, **flags)
    c_out = circuit.mux(hit[10], c_out, a[3], **flags)
    c_out = circuit.mux(hit[11], c_out, a[0], **flags)
    z_out = circuit.inv(circuit.reduce_or(result, **flags), **flags)
    return dict(result=result, z=z_out, c=c_out,
                a_we=any_op((0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 17, 18, 23, 24), **flags),
                z_we=any_op(tuple(range(12)), **flags),
                c_we=any_op((1, 2, 3, 4, 5, 10, 11), **flags))
