"""Independent mathematical game oracles, used only for validation.

Never called by Machine.step(); these functions cannot advance the CPU.
RAM scratch and return-ID cells are deliberately outside architectural checks.
"""

PONG_FIELDS = tuple(range(0x0D))
SNAKE_FIELDS = tuple(range(0x11)) + tuple(range(0x40, 0xE0))


def get8(ram, addr):
    return ram[addr] | (ram[addr + 1] << 4)


def put8(ram, addr, value):
    ram[addr], ram[addr + 1] = value & 15, (value >> 4) & 15


def pong_initial():
    ram = [0] * 256
    ram[:6] = [8, 4, 0, 0, 2, 2]
    return ram


def pong_tick(before, keys):
    ram = list(before)
    x, y, vx, vy, left, right = ram[:6]
    for address, shift in ((4, 0), (5, 2)):
        up, down = (keys >> shift) & 1, (keys >> (shift + 1)) & 1
        if up != down:
            ram[address] = max(0, min(5, ram[address] + down - up))
    event = 0
    candidate_y = y + (1 if vy == 0 else -1)
    if candidate_y < 0:
        y, vy, event = 1, 0, 1
    elif candidate_y > 7:
        y, vy, event = 6, 1, 1
    else:
        y = candidate_y
    candidate_x = x + (1 if vx == 0 else -1)
    if candidate_x in (0, 15):
        paddle = ram[4 if candidate_x == 0 else 5]
        if paddle <= y < paddle + 3:
            vx ^= 1
            event |= 2
        else:
            score_addr = 8 if candidate_x == 0 else 6
            put8(ram, score_addr, (get8(ram, score_addr) + 1) % 256)
            x, y, vx, vy = 8, 4, int(candidate_x == 0), 0
            event = 8 if candidate_x == 0 else 4
    else:
        x = candidate_x
    ram[:4] = x, y, vx, vy
    ram[10:13] = event, keys & 15, (keys >> 4) & 3
    return ram


def set_occupied(ram, point, occupied):
    x, y = point
    linear = y * 16 + x
    address, mask = 0xC0 + linear // 4, 1 << (linear % 4)
    if occupied:
        ram[address] |= mask
    else:
        ram[address] &= 15 ^ mask


def is_occupied(ram, point):
    x, y = point
    linear = y * 16 + x
    return bool(ram[0xC0 + linear // 4] & (1 << (linear % 4)))


def slot_point(ram, slot):
    return ram[0x40 + 2 * slot], ram[0x41 + 2 * slot]


def snake_fixture(points, direction=0, food=(10, 3), tail_index=0,
                  score=0, status=0):
    if not 0 <= tail_index < 64 or direction not in range(4):
        raise ValueError('ring index/direction')
    if not 1 <= len(points) <= 64 or len(set(points)) != len(points):
        raise ValueError('body length/uniqueness')
    if any(not (0 <= x < 16 and 0 <= y < 8) for x, y in points):
        raise ValueError('body coordinates')
    if not (0 <= food[0] < 16 and 0 <= food[1] < 8):
        raise ValueError('food coordinates')
    ram = [0] * 256
    head_index = (tail_index + len(points) - 1) % 64
    put8(ram, 0, head_index)
    put8(ram, 2, tail_index)
    put8(ram, 4, len(points))
    ram[6:9] = direction, food[0], food[1]
    put8(ram, 9, score)
    ram[11] = status
    for i, point in enumerate(points):
        slot = (tail_index + i) % 64
        ram[0x40 + 2 * slot:0x42 + 2 * slot] = point
        set_occupied(ram, point, True)
    return ram


def snake_initial():
    ram = snake_fixture([(2, 3), (3, 3), (4, 3)])
    ram[14] = 4  # CPU boot/restart indication
    return ram


def snake_tick(before, keys):
    if keys & 32:
        return snake_initial()
    ram = list(before)
    ram[12:17] = [keys & 15, (keys >> 4) & 3, 0, 0, 0]
    if ram[11]:
        return ram
    direction = ram[6]
    for bit, candidate in ((0, 3), (1, 1), (2, 2), (3, 0)):
        if keys & (1 << bit):
            if candidate != (direction ^ 2):
                direction = candidate
            break
    ram[6] = direction
    head_index, tail_index, length = get8(ram, 0), get8(ram, 2), get8(ram, 4)
    x, y = slot_point(ram, head_index)
    dx, dy = ((1, 0), (0, 1), (-1, 0), (0, -1))[direction]
    new = (x + dx, y + dy)
    if not (0 <= new[0] < 16 and 0 <= new[1] < 8):
        ram[11], ram[14] = 1, 2
        return ram
    grow = new == (ram[7], ram[8])
    tail = slot_point(ram, tail_index)
    if is_occupied(ram, new) and not (not grow and new == tail):
        ram[11], ram[14] = 1, 2
        return ram
    if grow and length >= 64:
        ram[11], ram[14] = 2, 3
        return ram
    if not grow:
        set_occupied(ram, tail, False)
        put8(ram, 2, (tail_index + 1) % 64)
    head_index = (head_index + 1) % 64
    put8(ram, 0, head_index)
    ram[0x40 + 2 * head_index:0x42 + 2 * head_index] = new
    set_occupied(ram, new, True)
    if grow:
        length += 1
        put8(ram, 4, length)
        put8(ram, 9, (get8(ram, 9) + 1) % 256)
        ram[14] = 1
        if length == 64:
            ram[11], ram[14] = 2, 3
            return ram
        start = ram[8] * 16 + ram[7]
        for probes in range(1, 66):
            candidate = (start + probes) % 128
            if not is_occupied(ram, (candidate % 16, candidate // 16)):
                ram[7], ram[8] = candidate % 16, candidate // 16
                put8(ram, 15, probes)
                break
        else:
            put8(ram, 15, 65)
            ram[11], ram[14] = 3, 5
    return ram


def snake_invariants(ram):
    """Representation checks independent of assembly's addressing sequence."""
    length, tail, head = get8(ram, 4), get8(ram, 2), get8(ram, 0)
    assert 1 <= length <= 64 and 0 <= head < 64 and 0 <= tail < 64
    assert head == (tail + length - 1) % 64
    points = [slot_point(ram, (tail + i) % 64) for i in range(length)]
    assert len(set(points)) == length
    assert all(0 <= x < 16 and 0 <= y < 8 for x, y in points)
    occupied = {(x, y) for y in range(8) for x in range(16) if is_occupied(ram, (x, y))}
    assert occupied == set(points)
    assert all(abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1 for a,b in zip(points, points[1:]))
    return points
