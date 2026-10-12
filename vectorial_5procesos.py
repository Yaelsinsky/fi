# Integrantes:
#   - Camarena Arévalo Yael Eduardo - 318279864
#   - León Flores Pedro David - 316254283
#
# Fecha: 11/10/2026
#
# Sistemas Distribuidos - Proyecto 2, Actividad 3
# Relojes vectoriales con 5 procesos.
#
# Usa el mismo ambiente de la actividad 2. Cada proceso p tiene un vector
# Vp de 5 posiciones que empieza en ceros y sigue las reglas del algoritmo:
#   - Evento local:      Vp[p] = Vp[p] + 1
#   - Envío de mensaje:  Vp[p] = Vp[p] + 1  y el mensaje lleva Vm = Vp
#   - Recepción:         Vp[p] = Vp[p] + 1  y para cada i: Vp[i] = max(Vp[i], Vm[i])
#
# Al final se comparan algunos pares de eventos con la regla vista en clase:
#   V(a) < V(b) si cada componente de V(a) es menor o igual que la de V(b)
#   y al menos una es estrictamente menor. Si no se cumple ni V(a) < V(b)
#   ni V(b) < V(a), los eventos son concurrentes (a || b).
#
# Ambiente:
#   P1: a1 local | a2 envía a P2 | a3 local | a4 recibe de P3 | a5 envía a P5
#   P2: b1 recibe de P1 | b2 envía a P3 | b3 local | b4 recibe de P4
#   P3: c1 local | c2 recibe de P2 | c3 envía a P1 | c4 envía a P4 | c5 local
#   P4: d1 local | d2 recibe de P3 | d3 envía a P2 | d4 recibe de P5
#   P5: e1 local | e2 envía a P4 | e3 local | e4 recibe de P1
#
# Uso:  python3 vectorial_5procesos.py

import socket
import sys
import time
from datetime import datetime
from multiprocessing import Process, Pipe, Queue

N = 5         # número de procesos
PAUSA = 0.3   # pausa entre eventos para que la salida se pueda seguir


def mostrar(texto):
    """Escribe la línea completa de una sola vez para que las salidas de
    los distintos procesos no se mezclen en la terminal"""
    sys.stdout.write(texto + "\n")
    sys.stdout.flush()


def txt(v):
    return "[" + ",".join(str(x) for x in v) + "]"


def evento(pid, v, nombre, registro):
    v[pid - 1] += 1
    mostrar("P%d  %-3s %-36s V = %s" % (pid, nombre, "evento local", txt(v)))
    registro.put((pid, nombre, "local", list(v)))
    time.sleep(PAUSA)
    return v


def enviar(pipe, pid, v, nombre, destino, registro):
    v[pid - 1] += 1
    mostrar("P%d  %-3s %-36s V = %s  (Vm = %s)"
            % (pid, nombre, "envía a P%d" % destino, txt(v), txt(v)))
    pipe.send((nombre, list(v)))
    registro.put((pid, nombre, "envía a P%d" % destino, list(v)))
    time.sleep(PAUSA)
    return v


def recibir(pipe, pid, v, nombre, origen, registro):
    evento_origen, vm = pipe.recv()
    v[pid - 1] += 1
    for i in range(N):
        v[i] = max(v[i], vm[i])
    mostrar("P%d  %-3s %-36s V = %s"
            % (pid, nombre, "recibe de P%d (%s, Vm = %s)" % (origen, evento_origen, txt(vm)), txt(v)))
    registro.put((pid, nombre, "recibe de P%d" % origen, list(v)))
    time.sleep(PAUSA)
    return v


def proceso_1(p12, p13, p15, registro):
    v = [0] * N
    v = evento(1, v, "a1", registro)
    v = enviar(p12, 1, v, "a2", 2, registro)
    v = evento(1, v, "a3", registro)
    v = recibir(p13, 1, v, "a4", 3, registro)
    v = enviar(p15, 1, v, "a5", 5, registro)


def proceso_2(p21, p23, p24, registro):
    v = [0] * N
    v = recibir(p21, 2, v, "b1", 1, registro)
    v = enviar(p23, 2, v, "b2", 3, registro)
    v = evento(2, v, "b3", registro)
    v = recibir(p24, 2, v, "b4", 4, registro)


def proceso_3(p32, p31, p34, registro):
    v = [0] * N
    v = evento(3, v, "c1", registro)
    v = recibir(p32, 3, v, "c2", 2, registro)
    v = enviar(p31, 3, v, "c3", 1, registro)
    v = enviar(p34, 3, v, "c4", 4, registro)
    v = evento(3, v, "c5", registro)


def proceso_4(p43, p42, p45, registro):
    v = [0] * N
    v = evento(4, v, "d1", registro)
    v = recibir(p43, 4, v, "d2", 3, registro)
    v = enviar(p42, 4, v, "d3", 2, registro)
    v = recibir(p45, 4, v, "d4", 5, registro)


def proceso_5(p54, p51, registro):
    v = [0] * N
    v = evento(5, v, "e1", registro)
    v = enviar(p54, 5, v, "e2", 4, registro)
    v = evento(5, v, "e3", registro)
    v = recibir(p51, 5, v, "e4", 1, registro)


def comparar(va, vb):
    """Regresa '->' si a ocurre antes que b, '<-' si b ocurre antes que a,
    o '||' si son concurrentes"""
    menor_igual = all(x <= y for x, y in zip(va, vb))
    mayor_igual = all(x >= y for x, y in zip(va, vb))
    if menor_igual and va != vb:
        return "->"
    if mayor_igual and va != vb:
        return "<-"
    return "||"


def main():
    print("=" * 78)
    print(" RELOJES VECTORIALES - 5 PROCESOS")
    print(" Máquina           : %s" % socket.gethostname())
    print(" Fecha del sistema : %s" % datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print(" Vector V = [P1, P2, P3, P4, P5]")
    print("=" * 78, flush=True)

    p12, p21 = Pipe()
    p13, p31 = Pipe()
    p15, p51 = Pipe()
    p23, p32 = Pipe()
    p24, p42 = Pipe()
    p34, p43 = Pipe()
    p45, p54 = Pipe()

    registro = Queue()
    procesos = [
        Process(target=proceso_1, args=(p12, p13, p15, registro)),
        Process(target=proceso_2, args=(p21, p23, p24, registro)),
        Process(target=proceso_3, args=(p32, p31, p34, registro)),
        Process(target=proceso_4, args=(p43, p42, p45, registro)),
        Process(target=proceso_5, args=(p54, p51, registro)),
    ]
    for p in procesos:
        p.start()

    total_eventos = 22
    eventos = [registro.get() for _ in range(total_eventos)]
    for p in procesos:
        p.join()

    # ---------- Resumen por proceso ----------
    print("\n" + "=" * 78)
    print(" RESUMEN: RELOJ VECTORIAL DE CADA EVENTO")
    print("=" * 78)
    vectores = {}
    for pid in range(1, N + 1):
        propios = [e for e in eventos if e[0] == pid]
        propios.sort(key=lambda e: e[3][pid - 1])
        for e in propios:
            vectores[e[1]] = e[3]
        print(" P%d:  %s" % (pid, "  ".join("%s=%s" % (e[1], txt(e[3])) for e in propios)))

    # ---------- Comparación de eventos ----------
    print("\n Comparación de algunos eventos:")
    pares = [("a2", "b1"), ("c1", "d4"), ("a1", "e4"),
             ("b3", "c5"), ("e3", "a5"), ("e3", "b3"), ("d4", "b4")]
    for x, y in pares:
        rel = comparar(vectores[x], vectores[y])
        if rel == "->":
            significado = "%s ocurre antes que %s" % (x, y)
        elif rel == "<-":
            significado = "%s ocurre antes que %s" % (y, x)
        else:
            significado = "son concurrentes"
        print("   %s %-13s %s  %s %-13s :  %s"
              % (x, txt(vectores[x]), rel, y, txt(vectores[y]), significado))
    print("=" * 78)


if __name__ == "__main__":
    main()
