"""3. INFRASTRUCTURE RÉTEG — CONTRACT IMPLEMENTATION (`RandomNumberProvider`).

Miért csomagoljuk külön osztályba a Python `random` modulját?
    Mert a Domain (`GameRulesEngine`) nem importálhatja közvetlenül a `random`-ot — különben
    a tesztekben kiszámíthatatlan lenne a gyümölcsök helye. Ez a vékony adapter
    teljesíti a `RandomNumberProvider` szerződést éles futáskor, opcionális `seed`
    támogatással a megismételhető demókhoz és visszajátszásokhoz.
"""

import random


class SystemRandomAdapter:
    """A `RandomNumberProvider` Protocol éles (nem-teszt) megvalósítása."""

    def __init__(self, seed: int | None = None) -> None:
        """Inicializálja a saját, elszigetelt `random.Random` példányt."""
        self._random_generator = random.Random(seed)

    def next_int(self, upper_exclusive: int) -> int:
        """Visszaad egy véletlen egészet a `[0, upper_exclusive)` tartományból."""
        return self._random_generator.randrange(upper_exclusive)
