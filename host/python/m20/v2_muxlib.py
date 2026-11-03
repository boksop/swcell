"""Explicit single-bit 2:1-MUX DAG construction for M20 V2.

Every node is one physical swc_mux157. Wires/constants cost zero; an actual
inversion is mux(x, 1, 0) and costs one node unless that same node is shared.
The baseline and shared variants use the same constructors. Both simplify
constant selectors, identical branches and the direct-selector wire pattern;
only the shared variant hash-conses identical (S, I0, I1) triples.

This module constructs logic. Its evaluator is a convenience for unit tests,
not an independent implementation/resource-count oracle.
"""
from collections import Counter

Bit = str | int


def _bit(value):
    if type(value) is int and value in (0, 1):
        return value
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"expected a signal name or integer bit 0/1, got {value!r}")


def bits_const(value, width):
    """Return an LSB-first constant vector; never truncate out-of-range data."""
    if type(width) is not int or width < 0:
        raise ValueError("width must be a nonnegative integer")
    if type(value) is not int or not 0 <= value < (1 << width):
        raise ValueError("constant does not fit the vector width")
    return [(value >> i) & 1 for i in range(width)]


class Circuit:
    """Ordered acyclic gate list with deterministic IDs and ownership labels."""

    def __init__(self, optimize=False):
        self.optimize = bool(optimize)
        self.nodes = []
        self.shared_requests = []
        self.simplifications = []
        self._unique = {}
        self._node_ids = set()

    def mux(self, s, i0, i1, *, group="common", category="comb"):
        s, i0, i1 = _bit(s), _bit(i0), _bit(i1)
        if not isinstance(group, str) or not group or not isinstance(category, str) or not category:
            raise ValueError("group and category must be nonempty strings")
        reason = None
        result = None
        if type(s) is int:
            result, reason = (i1 if s else i0), "constant_selector"
        elif i0 == i1:
            result, reason = i0, "identical_branches"
        elif i0 == 0 and i1 == 1:
            result, reason = s, "direct_selector_wire"
        if reason:
            self.simplifications.append(dict(s=s, i0=i0, i1=i1, result=result,
                                             reason=reason, group=group, category=category))
            return result
        key = (s, i0, i1)
        if self.optimize and key in self._unique:
            result = self._unique[key]
            self.shared_requests.append(dict(id=result, s=s, i0=i0, i1=i1,
                                             group=group, category=category))
            return result
        name = f"m{len(self.nodes) + 1:06d}"
        if name in (s, i0, i1):
            raise ValueError("external signal name collides with generated MUX ID")
        self.nodes.append(dict(id=name, s=s, i0=i0, i1=i1, group=group, category=category))
        self._node_ids.add(name)
        if self.optimize:
            self._unique[key] = name
        return name

    def inv(self, value, **labels):
        return self.mux(value, 1, 0, **labels)

    def and_(self, a, b, **labels):
        return self.mux(a, 0, b, **labels)

    def or_(self, a, b, **labels):
        return self.mux(a, b, 1, **labels)

    def xor_(self, a, b, **labels):
        return self.mux(a, b, self.inv(b, **labels), **labels)

    def reduce_or(self, values, **labels):
        result = 0
        for value in values:
            result = self.or_(result, value, **labels)
        return result

    def reduce_and(self, values, **labels):
        result = 1
        for value in values:
            result = self.and_(result, value, **labels)
        return result

    def eq_const(self, values, constant, **labels):
        values = list(values)
        constant_bits = bits_const(constant, len(values))
        literals = [value if bit else self.inv(value, **labels)
                    for value, bit in zip(values, constant_bits)]
        return self.reduce_and(literals, **labels)

    def add_bits(self, a, b, cin=0, **labels):
        """Unsigned ripple adder, LSB first, with explicit carry MUXes."""
        a, b = list(a), list(b)
        if len(a) != len(b):
            raise ValueError("adder operand widths differ")
        carry = _bit(cin)
        result = []
        for left, right in zip(a, b):
            propagate = self.xor_(left, right, **labels)
            result.append(self.xor_(propagate, carry, **labels))
            # If operands differ carry follows cin; if equal it follows a.
            carry = self.mux(propagate, left, carry, **labels)
        return result, carry

    def inc_bits(self, values, **labels):
        values = list(values)
        result, _ = self.add_bits(values, bits_const(0, len(values)), cin=1, **labels)
        return result

    @staticmethod
    def _leaves(outputs):
        if isinstance(outputs, dict):
            for value in outputs.values():
                yield from Circuit._leaves(value)
        elif isinstance(outputs, (list, tuple)):
            for value in outputs:
                yield from Circuit._leaves(value)
        else:
            yield _bit(outputs)

    def eval(self, outputs, values):
        """Evaluate a scalar/vector/output mapping using externally bound bits."""
        wires = dict(values)

        def resolve(bit):
            bit = _bit(bit)
            if type(bit) is int:
                return bit
            value = wires[bit]
            if type(value) is not int or value not in (0, 1):
                raise ValueError(f"signal {bit!r} does not have a binary integer value")
            return value

        for node in self.nodes:
            selector = resolve(node["s"])
            wires[node["id"]] = resolve(node["i1"] if selector else node["i0"])

        def collect(value):
            if isinstance(value, dict):
                return {key: collect(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [collect(item) for item in value]
            return resolve(value)

        return collect(outputs)

    evaluate = eval

    def stats(self, outputs=None):
        """Descriptive graph metrics; independent audit must inspect nodes too."""
        depth = {}
        fanout = Counter()
        for node in self.nodes:
            inputs = [node[k] for k in ("s", "i0", "i1")]
            depth[node["id"]] = 1 + max((depth.get(x, 0) for x in inputs), default=0)
            fanout.update(x for x in inputs if isinstance(x, str))
        leaves = list(self._leaves(outputs)) if outputs is not None else []
        fanout.update(x for x in leaves if isinstance(x, str))
        by_id = {node["id"]: node for node in self.nodes}
        reachable = set()

        def visit(bit):
            if bit not in by_id or bit in reachable:
                return
            reachable.add(bit)
            for key in ("s", "i0", "i1"):
                visit(by_id[bit][key])

        for bit in leaves:
            visit(bit)
        return dict(mux_count=len(self.nodes),
                    by_group=dict(Counter(n["group"] for n in self.nodes)),
                    by_category=dict(Counter(n["category"] for n in self.nodes)),
                    shared_requests=len(self.shared_requests),
                    simplifications=len(self.simplifications),
                    maximum_node_depth=max(depth.values(), default=0),
                    maximum_output_depth=max((depth.get(x, 0) for x in leaves), default=0),
                    maximum_fanout=max(fanout.values(), default=0),
                    reachable_mux_count=len(reachable) if outputs is not None else len(self.nodes))
