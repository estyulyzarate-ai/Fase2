"""Fase 2. Comparación reproducible de BFS, DFS y A* en Python 3.10+."""

from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from statistics import median
from time import perf_counter_ns

# (identificador, servicio reportado, usuarios afectados, hay alternativa)
REPORTES = (
    ("T3", "aplicación", 1, True),
    ("T1", "conectividad", 14, False),
    ("T2", "credenciales", 1, False),
)
CATEGORIAS = {"conectividad": "Redes", "credenciales": "Acceso",
              "aplicación": "Software"}
TECNICOS = ("B", "A", "C")  # Orden fijo de generación de candidatos.
COSTOS = {
    "Redes": {"A": 1, "B": 3},
    "Acceso": {"A": 4, "C": 1},
    "Software": {"B": 1, "C": 4},
}


def preparar_lote():
    """Clasifica los reportes y ordena por prioridad e identificador."""
    lote = []
    for ticket, servicio, afectados, alternativa in REPORTES:
        if afectados > 1 and not alternativa:
            prioridad = 1
        elif not alternativa:
            prioridad = 2
        else:
            prioridad = 3
        lote.append((prioridad, ticket, CATEGORIAS[servicio]))
    return sorted(lote)


@dataclass
class Nodo:
    nivel: int = 0
    ocupados: int = 0
    costo: int = 0
    padre: "Nodo | None" = None
    tecnico: str = ""


def sucesores(nodo, opciones):
    """Genera asignaciones compatibles con un cupo libre."""
    for tecnico, bit, costo in opciones[nodo.nivel]:
        if not nodo.ocupados & bit:
            yield Nodo(nodo.nivel + 1, nodo.ocupados | bit,
                       nodo.costo + costo, nodo, tecnico)


def buscar(opciones, algoritmo, minimos_pendientes, peso=2):
    """Devuelve la primera meta extraída y el total de expansiones."""
    raiz = Nodo()
    frontera = deque([raiz])
    monticulo = []
    orden = count()
    if algoritmo == "A*":
        heappush(monticulo, (peso * minimos_pendientes[0], next(orden), raiz))
    expandidos = 0
    while monticulo or (algoritmo != "A*" and frontera):
        if algoritmo == "BFS":
            nodo = frontera.popleft()
        elif algoritmo == "DFS":
            nodo = frontera.pop()
        else:
            _, _, nodo = heappop(monticulo)

        if nodo.nivel == len(opciones):
            return nodo, expandidos
        expandidos += 1
        hijos = list(sucesores(nodo, opciones))
        if algoritmo == "A*":
            for hijo in hijos:
                estimacion = hijo.costo + peso * minimos_pendientes[hijo.nivel]
                heappush(monticulo, (estimacion, next(orden), hijo))
        elif algoritmo == "DFS":
            frontera.extend(reversed(hijos))
        else:
            frontera.extend(hijos)
    return None, expandidos


def main():
    lote = preparar_lote()
    opciones = [
        [(tecnico, 1 << i, COSTOS[categoria][tecnico])
         for i, tecnico in enumerate(TECNICOS) if tecnico in COSTOS[categoria]]
        for _, _, categoria in lote
    ]
    # Suma de costos mínimos desde cada posición, calculada una sola vez.
    minimos = [0] * (len(lote) + 1)
    for i in range(len(lote) - 1, -1, -1):
        minimos[i] = minimos[i + 1] + min(costo for _, _, costo in opciones[i])

    for nombre, algoritmo, peso in (
        ("BFS", "BFS", 2), ("DFS", "DFS", 2),
        ("A* (peso 2)", "A*", 2), ("A* (peso 1)", "A*", 1),
    ):
        tiempos = []
        for _ in range(1000):
            inicio = perf_counter_ns()
            meta, expandidos = buscar(opciones, algoritmo, minimos, peso)
            tiempos.append(perf_counter_ns() - inicio)
        if meta is None:
            print(nombre, "sin asignación factible", expandidos)
            continue
        costo = meta.costo
        ruta = []
        while meta.padre is not None:
            ruta.append(f"{lote[meta.nivel - 1][1]} → {meta.tecnico}")
            meta = meta.padre
        print(f"{nombre} | {expandidos} | {median(tiempos) / 1e6:.6f} ms | "
              f"{costo} | {', '.join(reversed(ruta))}")


if __name__ == "__main__":
    main()
