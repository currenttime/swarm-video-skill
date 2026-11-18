"""Place workspace panels and schedule their clicks around timeline events."""
import math


def rectangle(x, y, width, height):
    return dict(x=x, y=y, width=width, height=height)


PANEL_NAMES = ('media', 'controls', 'inspector', 'transport')
PANEL_TARGETS = {
    'media': [(73 + 214 * column, 169 + 120 * row) for row in range(2) for column in range(3)],
    'controls': [(98, 470), (226, 506), (460, 456), (526, 519)],
    'inspector': [(1565, 171), (1694, 214), (1525, 362), (1752, 387), (1752, 501)],
    'transport': [(707, 549), (908, 549), (1109, 549)],
}


def workspace_layout(layout):
    """Keep older timeline/player layouts usable and fill safe panel rectangles."""
    layout = dict(layout)
    preview = layout.get('player') or layout.get('preview')
    timeline_top = layout['timeline']['y']
    if preview and all(name in layout for name in PANEL_NAMES):
        return layout
    header = min(.10, timeline_top * .24)
    left_width = preview['x'] if preview else .20
    panel_height = timeline_top - header
    if left_width >= .11 and panel_height >= .22:
        split = header + panel_height * (280 / 520)
        layout.setdefault('media', rectangle(0, header, left_width, split - header))
        layout.setdefault('controls', rectangle(0, split, left_width, timeline_top - split))
    if preview:
        right = preview['x'] + preview['width']
        bottom = preview['y'] + preview['height']
        if right <= .86 and panel_height >= .22:
            layout.setdefault('inspector', rectangle(right, header, 1 - right, panel_height))
        if timeline_top - bottom >= .035:
            layout.setdefault('transport', rectangle(preview['x'], bottom, preview['width'], timeline_top - bottom))
    return layout


def overlaps(first, second):
    return all(
        min(first[axis] + first[size], second[axis] + second[size])
        - max(first[axis], second[axis]) > 1e-8
        for axis, size in (('x', 'width'), ('y', 'height'))
    )


def linked_clicks(commits, frame_count, fps):
    """Pick spaced cues and order media, tool and timeline clicks around them."""
    gap = min(round(fps * .34), max(2, frame_count // 12))
    interval = max(3 * gap + 2, round(fps * 1.45))
    result = []
    for commit in sorted(commits, key=lambda item: item['at']):
        at = commit['at']
        if at <= 2 * gap or (result and at < result[-1]['timeline'] + interval):
            continue
        result.append(dict(commit=commit['id'], media=at-2*gap, controls=at-gap, timeline=at))
    return result


def panel_motion(role, worker_number, frame_count, fps, cue_frames=()):
    targets = PANEL_TARGETS[role]
    lead = bool(cue_frames)
    cadence = max(9, round(fps * (1.36 + (worker_number % 3)*.19)))
    clicks = list(cue_frames) if lead else list(
        range(max(2, round(fps * (.20 + (worker_number % 5)*.11))), frame_count, cadence)
    )
    if not clicks:
        clicks = [max(1, frame_count//3)]
    initial_slot = (worker_number + 1) % len(targets)
    position = targets[initial_slot]
    end = 0
    segments, actions = [], []

    def add(start, stop, origin, target, kind, bend=0):
        if stop > start:
            segments.append(dict(**{'from': start, 'to': stop}, p0=origin, p1=target, kind=kind, bend=bend))

    for index, at in enumerate(clicks):
        if at <= end:
            continue
        slot = (initial_slot + index + 1) % len(targets)
        target = targets[slot]
        distance = math.dist(position, target)
        travel = max(3, round(fps * min(.50, .18 + distance / 1100)))
        move_end = max(end + 1, at - max(1, round(fps * .055)))
        start_move = max(end, move_end - travel)
        add(end, start_move, position, position, 'hold')
        add(start_move, move_end, position, target, 'move', .025 * (-1 if index % 2 else 1))
        add(move_end, at, target, target, 'hold')
        click_end = min(at + max(2, round(fps * .20)), clicks[index + 1] if index + 1 < len(clicks) else frame_count + fps)
        add(at, click_end, target, target, 'click')
        actions.append(dict(at=at, slot=slot, worker=worker_number))
        end, position = click_end, target
    add(end, frame_count + fps, position, position, 'hold')
    return segments, actions
