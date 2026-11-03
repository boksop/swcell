"""Independent truth/math checks of the explicit V2 MUX constructors.

No V1 RTL or Python instruction-execution result is reused as the ALU oracle.
The 64 internal op numbers are a literal interface contract; runtime expected
arithmetic below is unbounded integer mathematics, not the MUX builder.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from m20.v2_muxlib import Circuit, bits_const
from m20.v2_alu import build_alu


def bind(prefix, width, value):
    return {f"{prefix}{bit}": (value >> bit) & 1 for bit in range(width)}


def number(bits):
    return sum(bit << i for i, bit in enumerate(bits))


def alu_oracle(op, a, operand, carry):
    result, c_out = a, carry
    a_we = z_we = c_we = 0
    if op == 0:
        result = operand; a_we = z_we = 1
    elif op in (1, 2):
        total = a + operand + (carry if op == 2 else 0)
        result, c_out = total % 16, int(total >= 16)
        a_we = z_we = c_we = 1
    elif op in (3, 4, 5):
        difference = a - operand - ((1 - carry) if op == 4 else 0)
        result, c_out = difference % 16, int(difference >= 0)
        a_we, z_we, c_we = int(op != 5), 1, 1
    elif op in (6, 7, 8, 9):
        result = (a & operand if op == 6 else a ^ operand if op == 7 else
                  a | operand if op == 8 else 15 - a)
        a_we = z_we = 1
    elif op == 10:
        result, c_out = (a * 2) % 16, int(a >= 8)
        a_we = z_we = c_we = 1
    elif op == 11:
        result, c_out = a // 2, a % 2
        a_we = z_we = c_we = 1
    elif op in (17, 18, 23, 24):
        result, a_we = operand, 1
    return dict(result=result, z=int(result == 0), c=c_out,
                a_we=a_we, z_we=z_we, c_we=c_we)


class M20V2MuxLibraryTests(unittest.TestCase):
    def test_single_mux_truth_table_and_derived_boolean_cells(self):
        for optimized in (False, True):
            c = Circuit(optimize=optimized)
            outputs = dict(mux=c.mux('s', 'a', 'b'), inv=c.inv('a'),
                           and_=c.and_('a', 'b'), or_=c.or_('a', 'b'),
                           xor_=c.xor_('a', 'b'))
            for s in (0, 1):
                for a in (0, 1):
                    for b in (0, 1):
                        actual = c.eval(outputs, dict(s=s, a=a, b=b))
                        self.assertEqual(actual, dict(mux=b if s else a, inv=1-a,
                                                     and_=a*b, or_=int(a+b > 0), xor_=(a+b)%2))
            self.assertEqual(c.reduce_or([]), 0)
            self.assertEqual(c.reduce_and([]), 1)

    def test_counted_inverters_constants_shared_ownership_and_wire_simplification(self):
        for optimized in (False, True):
            c = Circuit(optimize=optimized)
            self.assertEqual(c.mux(0, 'a', 'b'), 'a')
            self.assertEqual(c.mux(1, 'a', 'b'), 'b')
            self.assertEqual(c.mux('s', 'a', 'a'), 'a')
            self.assertEqual(c.mux('s', 0, 1), 's')
            self.assertEqual(len(c.nodes), 0)
            first = c.inv('x', group='first', category='inversion')
            second = c.inv('x', group='second', category='inversion')
            self.assertEqual(first == second, optimized)
            self.assertEqual(len(c.nodes), 1 if optimized else 2)
            self.assertEqual(c.nodes[0], dict(id='m000001', s='x', i0=1, i1=0,
                                            group='first', category='inversion'))
            self.assertEqual(len(c.shared_requests), int(optimized))
            if optimized:
                self.assertEqual(c.shared_requests[0]['group'], 'second')
                self.assertEqual(c.shared_requests[0]['id'], first)
            self.assertEqual(len(c.simplifications), 4)

    def test_adders_increments_reductions_and_constant_comparators(self):
        for optimized in (False, True):
            c = Circuit(optimize=optimized)
            a = [f'a{i}' for i in range(4)]; b = [f'b{i}' for i in range(4)]
            total, carry = c.add_bits(a, b, cin='cin')
            outputs = dict(sum=total, c=carry, eq9=c.eq_const(a, 9),
                           nonzero=c.reduce_or(a), allones=c.reduce_and(a))
            for left in range(16):
                for right in range(16):
                    for cin in (0, 1):
                        actual = c.eval(outputs, {**bind('a', 4, left), **bind('b', 4, right), 'cin':cin})
                        value = left + right + cin
                        self.assertEqual((number(actual['sum']), actual['c']), (value % 16, int(value >= 16)))
                        self.assertEqual((actual['eq9'], actual['nonzero'], actual['allones']),
                                         (int(left == 9), int(left != 0), int(left == 15)))
            for width in (4, 8, 12):
                inc = Circuit(optimize=optimized)
                result = inc.inc_bits([f'x{i}' for i in range(width)])
                for value in range(1 << width):
                    actual = number(inc.eval(result, bind('x', width, value)))
                    self.assertEqual(actual, (value + 1) % (1 << width))

    def test_both_alu_variants_all_32768_internal_op_vectors(self):
        for optimized in (False, True):
            c = Circuit(optimize=optimized)
            outputs = build_alu(c, [f'o{i}' for i in range(6)],
                                [f'a{i}' for i in range(4)], [f'b{i}' for i in range(4)], 'cin')
            checked = 0
            for op in range(64):
                for a in range(16):
                    for b in range(16):
                        for cin in (0, 1):
                            actual = c.eval(outputs, {**bind('o', 6, op), **bind('a', 4, a),
                                                      **bind('b', 4, b), 'cin':cin})
                            actual['result'] = number(actual['result'])
                            self.assertEqual(actual, alu_oracle(op, a, b, cin), (optimized, op, a, b, cin))
                            checked += 1
            self.assertEqual(checked, 32768)

    def test_predecoded_onehot_alu_preserves_same_semantics(self):
        for optimized in (False, True):
            c = Circuit(optimize=optimized)
            outputs = build_alu(c, [f'o{i}' for i in range(6)],
                                [f'a{i}' for i in range(4)], [f'b{i}' for i in range(4)], 'cin',
                                selects={op:f'hit{op}' for op in range(28)})
            for op in range(64):
                hits = {f'hit{i}':int(op == i) for i in range(28)}
                for a in (0, 1, 7, 15):
                    for b in (0, 1, 8, 15):
                        for cin in (0, 1):
                            actual = c.eval(outputs, {**hits, **bind('a', 4, a), **bind('b', 4, b), 'cin':cin})
                            actual['result'] = number(actual['result'])
                            self.assertEqual(actual, alu_oracle(op, a, b, cin))

    def test_dag_is_ordered_unique_and_labels_sum_to_real_cell_count(self):
        c = Circuit(optimize=True)
        first = c.mux('select', 'input0', 'input1', group='g1', category='data')
        inverse = c.inv('input0', group='g2', category='invert')
        result = c.mux(first, inverse, 'input1', group='g3', category='data')
        self.assertEqual(len(c.nodes), 3)
        seen = {'select', 'input0', 'input1'}
        for node in c.nodes:
            self.assertNotIn(node['id'], seen)
            for key in ('s', 'i0', 'i1'):
                if isinstance(node[key], str):
                    self.assertIn(node[key], seen)
            seen.add(node['id'])
        stats = c.stats(result)
        self.assertEqual(stats['mux_count'], 3)
        self.assertEqual(sum(stats['by_group'].values()), 3)
        self.assertEqual(sum(stats['by_category'].values()), 3)
        self.assertEqual(stats['maximum_output_depth'], 2)
        self.assertEqual(stats['reachable_mux_count'], 3)
        self.assertEqual(stats['maximum_fanout'], 2)

    def test_builder_rejects_invalid_widths_constants_and_bit_values(self):
        self.assertEqual(bits_const(0, 0), [])
        self.assertEqual(bits_const(0xA, 4), [0, 1, 0, 1])
        for value, width in ((16, 4), (-1, 4), (1, 0), (0, -1), (True, 1)):
            with self.assertRaises(ValueError):bits_const(value, width)
        c = Circuit()
        for value in (True, None, 2, -1, ''):
            with self.assertRaises(ValueError):c.mux(value, 0, 1)
        with self.assertRaises(ValueError):c.add_bits(['a'], ['b', 'c'])
        with self.assertRaises(ValueError):c.eq_const(['a'], 2)
        with self.assertRaises(ValueError):build_alu(c, ['op'], [0]*4, [0]*4, 0)
        gate = c.inv('unbound')
        with self.assertRaises(KeyError):c.eval(gate, {})


if __name__ == '__main__':
    unittest.main()
