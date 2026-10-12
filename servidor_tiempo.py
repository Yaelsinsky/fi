# Integrantes:
#   - Camarena Arévalo Yael Eduardo - 318279864
#   - León Flores Pedro David - 316254283
#
# Fecha: 11/10/2026
#
# Sistemas Distribuidos - Proyecto 2, Actividad 1
# Servidor de tiempo para el algoritmo de Cristian.
#
# El servidor espera peticiones de los clientes por sockets TCP. Cada vez
# que un cliente le pide la hora, le responde con su reloj (Cs) y con el
# nombre de su máquina. Atiende a cada cliente en un hilo distinto para
# que los tres clientes puedan sincronizarse al mismo tiempo.
#
# Uso:  python3 servidor_tiempo.py [--puerto 5000]

import argparse
import json
import socket
import threading
import time
from datetime import datetime


def formato(t):
    """Convierte segundos de época a HH:MM:SS.mmm"""
    return datetime.fromtimestamp(t).strftime("%H:%M:%S.%f")[:-3]


def atender(conexion, direccion, contador):
    with conexion:
        peticion = conexion.recv(1024).decode()
        if not peticion:
            return

        # El cliente manda su nombre de máquina en la petición
        cliente = peticion.replace("HORA", "").strip() or direccion[0]

        llegada = time.time()
        hora_servidor = time.time()
        respuesta = {
            "hora_servidor": hora_servidor,
            "host_servidor": socket.gethostname(),
            # tiempo que tardó el servidor en preparar la respuesta (I)
            "procesamiento": time.time() - llegada,
        }
        conexion.sendall(json.dumps(respuesta).encode())

        contador[0] += 1
        print("[%d] Petición de %-12s (%s)  ->  Cs enviado = %s"
              % (contador[0], cliente, direccion[0], formato(hora_servidor)), flush=True)


def main():
    parser = argparse.ArgumentParser(description="Servidor de tiempo (Cristian)")
    parser.add_argument("--puerto", type=int, default=5000)
    args = parser.parse_args()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", args.puerto))
    servidor.listen(10)

    print("=" * 66)
    print(" SERVIDOR DE TIEMPO - ALGORITMO DE CRISTIAN")
    print("=" * 66)
    print(" Máquina del servidor : %s" % socket.gethostname())
    print(" Fecha del sistema    : %s" % datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print(" Escuchando en puerto : %d" % args.puerto)
    print("=" * 66, flush=True)

    contador = [0]
    try:
        while True:
            conexion, direccion = servidor.accept()
            hilo = threading.Thread(target=atender, args=(conexion, direccion, contador))
            hilo.daemon = True
            hilo.start()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
