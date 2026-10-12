# Integrantes:
#   - Camarena Arévalo Yael Eduardo - 318279864
#   - León Flores Pedro David - 316254283
#
# Fecha: 11/10/2026
#
# Sistemas Distribuidos - Proyecto 2, Actividad 2
# Relojes lógicos de Lamport con 5 procesos.
#
# Se extiende el ambiente visto en clase (3 procesos comunicados con pipes)
# a 5 procesos, cada uno con 4 o 5 eventos. Cada proceso tiene un contador
# Cp que empieza en 0 y sigue las reglas del algoritmo:
#   - Evento local:      Cp = Cp + 1
#   - Envío de mensaje:  Cp = Cp + 1  y el mensaje lleva Cm = Cp
#   - Recepción:         Cp = max(Cp, Cm) + 1
#
# Ambiente (ver diagrama en el documento):
#   P1: a1 local | a2 envía a P2 | a3 local | a4 recibe de P3 | a5 envía a P5
#   P2: b1 recibe de P1 | b2 envía a P3 | b3 local | b4 recibe de P4
#   P3: c1 local | c2 recibe de P2 | c3 envía a P1 | c4 envía a P4 | c5 local
#   P4: d1 local | d2 recibe de P3 | d3 envía a P2 | d4 recibe de P5
#   P5: e1 local | e2 envía a P4 | e3 local | e4 recibe de P1
#
# Uso:  python3 lamport_5procesos.py

import socket
import sys
import time
from datetime import datetime
from multiprocessing import Process, Pipe, Queue

PAUSA = 0.3   # pausa entre eventos para que la salida se pueda seguir


def mostrar(texto):
    """Escribe la línea completa de una sola vez para que las salidas de
    los distintos procesos no se mezclen en la terminal"""
    sys.stdout.write(texto + "\n")
    sys.stdout.flush()


def evento(pid, contador, nombre, registro):
    contador += 1
    mostrar("P%d  %-3s evento local             C = %d" % (pid, nombre, contador))
    registro.put((pid, nombre, "local", contador))
    time.sleep(PAUSA)
    return contador


def enviar(pipe, pid, contador, nombre, destino, registro):
    contador += 1
    # Se imprime antes de enviar para que en pantalla el envío
    # siempre aparezca antes que la recepción
    mostrar("P%d  %-3s envía a P%d   (Cm = %d)   C = %d"
            % (pid, nombre, destino, contador, contador))
    pipe.send((nombre, contador))
    registro.put((pid, nombre, "envía a P%d" % destino, contador))
    time.sleep(PAUSA)
    return contador


def recibir(pipe, pid, contador, nombre, origen, registro):
    evento_origen, cm = pipe.recv()
    anterior = contador
    contador = max(contador, cm) + 1
    mostrar("P%d  %-3s recibe de P%d (%s, Cm = %d)  C = max(%d, %d) + 1 = %d"
            % (pid, nombre, origen, evento_origen, cm, anterior, cm, contador))
    registro.put((pid, nombre, "recibe de P%d" % origen, contador))
    time.sleep(PAUSA)
    return contador


def proceso_1(p12, p13, p15, registro):
    c = 0
    c = evento(1, c, "a1", registro)
    c = enviar(p12, 1, c, "a2", 2, registro)
    c = evento(1, c, "a3", registro)
    c = recibir(p13, 1, c, "a4", 3, registro)
    c = enviar(p15, 1, c, "a5", 5, registro)


def proceso_2(p21, p23, p24, registro):
    c = 0
    c = recibir(p21, 2, c, "b1", 1, registro)
    c = enviar(p23, 2, c, "b2", 3, registro)
    c = evento(2, c, "b3", registro)
    c = recibir(p24, 2, c, "b4", 4, registro)


def proceso_3(p32, p31, p34, registro):
    c = 0
    c = evento(3, c, "c1", registro)
    c = recibir(p32, 3, c, "c2", 2, registro)
    c = enviar(p31, 3, c, "c3", 1, registro)
    c = enviar(p34, 3, c, "c4", 4, registro)
    c = evento(3, c, "c5", registro)


def proceso_4(p43, p42, p45, registro):
    c = 0
    c = evento(4, c, "d1", registro)
    c = recibir(p43, 4, c, "d2", 3, registro)
    c = enviar(p42, 4, c, "d3", 2, registro)
    c = recibir(p45, 4, c, "d4", 5, registro)


def proceso_5(p54, p51, registro):
    c = 0
    c = evento(5, c, "e1", registro)
    c = enviar(p54, 5, c, "e2", 4, registro)
    c = evento(5, c, "e3", registro)
    c = recibir(p51, 5, c, "e4", 1, registro)


def main():
    print("=" * 70)
    print(" RELOJES LÓGICOS DE LAMPORT - 5 PROCESOS")
    print(" Máquina           : %s" % socket.gethostname())
    print(" Fecha del sistema : %s" % datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("=" * 70, flush=True)

    # Un pipe por cada par de procesos que se comunican
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
    print("\n" + "=" * 70)
    print(" RESUMEN: VALOR DEL RELOJ DE LAMPORT EN CADA EVENTO")
    print("=" * 70)
    for pid in range(1, 6):
        propios = [e for e in eventos if e[0] == pid]
        propios.sort(key=lambda e: e[3])
        linea = "  ".join("%s=%d" % (e[1], e[3]) for e in propios)
        print(" P%d:  %s" % (pid, linea))

    # ---------- Orden total ----------
    # Se ordena por el valor del reloj y, si hay empate, por el número de
    # proceso. Así todos los eventos quedan ordenados entre sí.
    eventos.sort(key=lambda e: (e[3], e[0]))
    print("\n Orden total, formato evento(C.proceso):")
    marcas = ["%s(%d.%d)" % (e[1], e[3], e[0]) for e in eventos]
    for i in range(0, len(marcas), 6):
        print("   " + "  ->  ".join(marcas[i:i + 6]))
    print("=" * 70)


if __name__ == "__main__":
    main()
