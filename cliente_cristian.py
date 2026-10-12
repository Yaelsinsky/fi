# Integrantes:
#   - Camarena Arévalo Yael Eduardo - 318279864
#   - León Flores Pedro David - 316254283
#
# Fecha: 11/10/2026
#
# Sistemas Distribuidos - Proyecto 2, Actividad 1
# Cliente del algoritmo de Cristian.
#
# El cliente tiene su propio reloj (Cc), que puede ir adelantado o atrasado
# respecto al servidor. Para sincronizarse:
#   1. Anota T0 con su reloj y le pide la hora al servidor.
#   2. El servidor responde con su hora Cs.
#   3. Anota T1 al recibir la respuesta.
#   4. Calcula la hora correcta:  C = Cs + (T1 - T0 - I) / 2
#      donde I es el tiempo de procesamiento que reporta el servidor.
#
# Después compara C con su reloj Cc:
#   - Si C > Cc el cliente va atrasado: se adelanta el reloj de inmediato.
#   - Si C < Cc el cliente va adelantado: NO se puede regresar el reloj,
#     porque el tiempo nunca debe ir hacia atrás. En su lugar el reloj se
#     hace más lento durante un periodo hasta que alcanza la hora correcta.
#
# Uso:  python3 cliente_cristian.py IP_SERVIDOR [--puerto 5000] [--desfase SEG]
#   --desfase simula que el reloj del cliente va adelantado (+) o atrasado (-).
#   Si las máquinas ya tienen relojes distintos se puede dejar en 0.

import argparse
import json
import socket
import time
from datetime import datetime


def formato(t):
    """Convierte segundos de época a HH:MM:SS.mmm"""
    return datetime.fromtimestamp(t).strftime("%H:%M:%S.%f")[:-3]


class RelojCliente:
    """Reloj por software del cliente.

    Avanza a partir de un valor base con un ritmo dado. Con ritmo 1.0 marcha
    igual que un reloj normal. Con ritmo menor a 1.0 marcha más lento, que es
    lo que se usa para corregir un reloj adelantado sin regresarlo.
    """

    def __init__(self, desfase):
        self.base_real = time.time()
        self.base_reloj = time.time() + desfase
        self.ritmo = 1.0

    def ahora(self):
        return self.base_reloj + (time.time() - self.base_real) * self.ritmo

    def fijar(self, valor, ritmo=1.0):
        self.base_real = time.time()
        self.base_reloj = valor
        self.ritmo = ritmo


def pedir_hora(servidor, puerto, reloj, host):
    """Una ronda del algoritmo de Cristian. Regresa T0, T1 y la respuesta."""
    t0 = reloj.ahora()
    with socket.create_connection((servidor, puerto), timeout=5) as s:
        s.sendall(("HORA " + host).encode())
        datos = s.recv(1024)
    t1 = reloj.ahora()
    return t0, t1, json.loads(datos.decode())


def main():
    parser = argparse.ArgumentParser(description="Cliente del algoritmo de Cristian")
    parser.add_argument("servidor", help="IP o nombre de la máquina del servidor")
    parser.add_argument("--puerto", type=int, default=5000)
    parser.add_argument("--desfase", type=float, default=0.0,
                        help="segundos de diferencia simulada del reloj del cliente")
    parser.add_argument("--periodo", type=float, default=10.0,
                        help="segundos mínimos para corregir un reloj adelantado")
    args = parser.parse_args()

    host = socket.gethostname()
    reloj = RelojCliente(args.desfase)

    print("=" * 66)
    print(" CLIENTE - ALGORITMO DE CRISTIAN")
    print("=" * 66)
    print(" Máquina del cliente  : %s" % host)
    print(" Fecha del sistema    : %s" % datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print(" Servidor de tiempo   : %s:%d" % (args.servidor, args.puerto))
    print(" Desfase del reloj    : %+.3f s" % args.desfase)
    print(" Reloj del cliente Cc : %s" % formato(reloj.ahora()))
    print("-" * 66, flush=True)

    # ---------- Ronda de sincronización ----------
    t0, t1, resp = pedir_hora(args.servidor, args.puerto, reloj, host)
    cs = resp["hora_servidor"]
    proc = resp["procesamiento"]
    rtt = t1 - t0
    c = cs + (rtt - proc) / 2.0      # hora calculada con Cristian
    cc = reloj.ahora()               # hora que marca el cliente en ese momento
    diferencia = c - cc

    print(" Servidor             : %s" % resp["host_servidor"])
    print(" T0 (envío)           : %s" % formato(t0))
    print(" Cs (hora servidor)   : %s" % formato(cs))
    print(" T1 (respuesta)       : %s" % formato(t1))
    print(" Ida y vuelta (T1-T0) : %.3f ms" % (rtt * 1000))
    print(" C = Cs + (T1-T0-I)/2 : %s" % formato(c))
    print(" Cc (reloj cliente)   : %s" % formato(cc))
    print(" Diferencia C - Cc    : %+.3f s" % diferencia)
    print("-" * 66, flush=True)

    # ---------- Ajuste del reloj ----------
    if abs(diferencia) < 0.001:
        print(" C = Cc  ->  El reloj ya está sincronizado, no se ajusta.")

    elif diferencia > 0:
        print(" C > Cc  ->  El reloj del cliente va ATRASADO %.3f s." % diferencia)
        print("            Se adelanta de inmediato a la hora calculada.")
        antes = reloj.ahora()
        reloj.fijar(antes + diferencia)
        print("            Cc antes : %s" % formato(antes))
        print("            Cc ahora : %s" % formato(reloj.ahora()))

    else:
        exceso = -diferencia
        periodo = max(args.periodo, 2 * exceso)   # así el ritmo nunca baja de 0.5
        ritmo = 1.0 - exceso / periodo
        print(" C < Cc  ->  El reloj del cliente va ADELANTADO %.3f s." % exceso)
        print("            No se puede regresar el reloj porque el tiempo no debe")
        print("            ir hacia atrás. Se hace más lento (ritmo %.2f) durante" % ritmo)
        print("            %.1f s hasta alcanzar la hora correcta." % periodo)
        print()
        print("    seg   Hora de referencia   Reloj del cliente   Diferencia")

        inicio_real = time.time()
        referencia_inicial = c + (time.time() - inicio_real)
        reloj.fijar(reloj.ahora(), ritmo)
        transcurrido = 0.0
        while transcurrido < periodo:
            transcurrido = time.time() - inicio_real
            referencia = referencia_inicial + transcurrido
            actual = reloj.ahora()
            print("   %5.1f   %s         %s        %+.3f s"
                  % (transcurrido, formato(referencia), formato(actual), actual - referencia),
                  flush=True)
            time.sleep(min(1.0, max(0.0, periodo - transcurrido)) or 0.01)
        reloj.fijar(reloj.ahora(), 1.0)
        print("            El reloj vuelve a su ritmo normal.")

    # ---------- Verificación con una segunda ronda ----------
    print("-" * 66)
    t0, t1, resp = pedir_hora(args.servidor, args.puerto, reloj, host)
    c2 = resp["hora_servidor"] + ((t1 - t0) - resp["procesamiento"]) / 2.0
    print(" Verificación: nueva diferencia C - Cc = %+.3f s" % (c2 - reloj.ahora()))
    print(" Reloj final del cliente : %s" % formato(reloj.ahora()))
    print("=" * 66, flush=True)


if __name__ == "__main__":
    main()
