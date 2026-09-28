# Nombre: Yael Eduardo Camarena Arévalo
# Número de cuenta: 318279864
# Fecha: 28/09/2026
# Relojes lógicos de Lamport para el diagrama de 3 procesos
#
#   P1:  a(1) ---- b(2)
#                   \  m1
#   P2:              c(3) ---- d(4)
#                                \  m2
#   P3:  e(1) ------------------- f(5)

from multiprocessing import Process, Pipe
from os import getpid


def local_time(counter):
    return ' (LAMPORT_TIME={})'.format(counter)


# calcula la nueva marca de tiempo al recibir un mensaje
def calc_recv_timestamp(recv_time_stamp, counter):
    return max(recv_time_stamp, counter) + 1


# evento interno del proceso
def event(pid, counter, nombre):
    counter += 1
    print('Evento {} en {}'.format(nombre, pid) + local_time(counter) + '\n', flush=True)
    return counter


# envío de mensaje (también cuenta como evento)
def send_message(pipe, pid, counter, nombre, mensaje):
    counter += 1
    pipe.send((mensaje, counter))
    print('Evento {}: mensaje {} enviado desde {}'.format(nombre, mensaje, pid) + local_time(counter) + '\n', flush=True)
    return counter


# recepción de mensaje
def recv_message(pipe, pid, counter, nombre):
    mensaje, timestamp = pipe.recv()
    counter = calc_recv_timestamp(timestamp, counter)
    print('Evento {}: mensaje {} recibido en {}'.format(nombre, mensaje, pid) + local_time(counter) + '\n', flush=True)
    return counter


# P1: evento a, luego envía m1 a P2 (evento b)
def process_one(pipe_envio_p2):
    pid = 'P1 (pid {})'.format(getpid())
    counter = 0
    counter = event(pid, counter, 'a')                             # a = 1
    counter = send_message(pipe_envio_p2, pid, counter, 'b', 'm1')  # b = 2


# P2: recibe m1 de P1 (evento c), luego envía m2 a P3 (evento d)
def process_two(pipe_recibe_p1, pipe_envio_p3):
    pid = 'P2 (pid {})'.format(getpid())
    counter = 0
    counter = recv_message(pipe_recibe_p1, pid, counter, 'c')       # c = max(2, 0) + 1 = 3
    counter = send_message(pipe_envio_p3, pid, counter, 'd', 'm2')  # d = 4


# P3: evento e, luego recibe m2 de P2 (evento f)
def process_three(pipe_recibe_p2):
    pid = 'P3 (pid {})'.format(getpid())
    counter = 0
    counter = event(pid, counter, 'e')                         # e = 1
    counter = recv_message(pipe_recibe_p2, pid, counter, 'f')  # f = max(4, 1) + 1 = 5


if __name__ == '__main__':
    # Los mensajes solo viajan en un sentido, por eso los pipes son de una via
    # Pipe(duplex=False) regresa (extremo que recibe, extremo que envía)

    # canal de m1: P1 -> P2
    p2_recibe_m1, p1_envia_m1 = Pipe(duplex=False)
    # canal de m2: P2 -> P3
    p3_recibe_m2, p2_envia_m2 = Pipe(duplex=False)

    # creación de procesos
    process1 = Process(target=process_one, args=(p1_envia_m1,))
    process2 = Process(target=process_two, args=(p2_recibe_m1, p2_envia_m2))
    process3 = Process(target=process_three, args=(p3_recibe_m2,))

    process1.start()
    process2.start()
    process3.start()

    process1.join()
    process2.join()
    process3.join()
