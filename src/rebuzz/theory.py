"""Music-theory primitives for the composition DSL: note-name parsing, scales/
modes, and the Pedal-Chord type/arp-mode code tables. Everything ultimately
resolves to a `blob.note_value(octave, idx)` (octave*16 + idx + 1).

Pitch index is chromatic 0-11 with C=0. Octave matches ReBuzz note values.
"""
from .blob import note_value

# chromatic index by name (sharps + flats)
_BASE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def parse_note(token):
    """'A', 'Bb', 'F#', 'c#' -> chromatic index 0-11."""
    s = str(token).strip()
    if not s or s[0].upper() not in _BASE:
        raise ValueError('bad note name %r' % token)
    idx = _BASE[s[0].upper()]
    for c in s[1:]:
        if c in '#♯':
            idx += 1
        elif c in 'b♭':
            idx -= 1
        else:
            raise ValueError('bad accidental in %r' % token)
    return idx % 12


# scale / mode interval sets (semitones from the root)
SCALES = {
    'major':            [0, 2, 4, 5, 7, 9, 11],
    'ionian':           [0, 2, 4, 5, 7, 9, 11],
    'minor':            [0, 2, 3, 5, 7, 8, 10],
    'aeolian':          [0, 2, 3, 5, 7, 8, 10],
    'dorian':           [0, 2, 3, 5, 7, 9, 10],
    'phrygian':         [0, 1, 3, 5, 7, 8, 10],
    'lydian':           [0, 2, 4, 6, 7, 9, 11],
    'mixolydian':       [0, 2, 4, 5, 7, 9, 10],
    'locrian':          [0, 1, 3, 5, 6, 8, 10],
    'harmonic_minor':   [0, 2, 3, 5, 7, 8, 11],
    'hijaz':            [0, 1, 4, 5, 7, 8, 10],   # phrygian dominant
    'phrygian_dominant': [0, 1, 4, 5, 7, 8, 10],
    'blues':            [0, 3, 5, 6, 7, 10],
    'minor_pentatonic': [0, 3, 5, 7, 10],
    'major_pentatonic': [0, 2, 4, 7, 9],
    'chromatic':        list(range(12)),
}

# Pedal Chord ChordType codes (col 2), verified against ReBuzz
CHORD_CODES = {'maj': 0, 'major': 0, 'min': 1, 'minor': 1, 'dom7': 2, '7': 2,
               'dim': 5, 'diminished': 5, 'aug': 6, 'augmented': 6, 'oct': 50, 'octave': 50}

# Pedal Chord Mode codes (col 3)
ARP_MODES = {'block': 0, 'up': 1, 'down': 2, 'updown': 3, 'up+down': 3, 'random': 5}


def chord_code(name):
    try:
        return CHORD_CODES[str(name).lower()]
    except KeyError:
        raise ValueError('unknown chord type %r (have %s)'
                         % (name, ', '.join(sorted(set(CHORD_CODES)))))


def arp_mode(name):
    try:
        return ARP_MODES[str(name).lower()]
    except KeyError:
        raise ValueError('unknown arp mode %r (have %s)'
                         % (name, ', '.join(sorted(set(ARP_MODES)))))


class Scale:
    """A key + mode. Resolve degrees (1-based, wrapping octaves) or absolute
    note names to a chromatic index, then to a ReBuzz note value."""

    def __init__(self, root, mode='major'):
        self.root = parse_note(root) if isinstance(root, str) else int(root) % 12
        if mode not in SCALES:
            raise ValueError('unknown scale %r (have %s)' % (mode, ', '.join(sorted(SCALES))))
        self.mode = mode
        self.steps = SCALES[mode]

    def degree_index(self, n):
        """1-based scale degree -> chromatic index (octave offset folded in via +12*k)."""
        n = int(n)
        k = (n - 1) // len(self.steps)
        return self.root + self.steps[(n - 1) % len(self.steps)] + 12 * k

    def index_of(self, token):
        """Resolve a root token: note name ('A', 'Bb') or scale degree (int / '5')."""
        if isinstance(token, int) or (isinstance(token, str) and token.lstrip('-').isdigit()):
            return self.degree_index(int(token)) % 12
        return parse_note(token)

    def value(self, token, octave):
        """Root token -> ReBuzz note value at the given octave."""
        return note_value(octave, self.index_of(token))
