/*
 * Nombre: Yael Eduardo Camarena Arévalo
 * Número de cuenta: XXXXXXXXX
 * Fecha: 16/09/2026
 *
 * Sistemas Distribuidos - Proyecto 1 (parte 1, ejemplo del video)
 * El proceso 0 envía un arreglo de 5 flotantes distintos a los procesos 1 a 5.
 * Cada receptor imprime el arreglo, el nombre del nodo y su identificador.
 *
 * Compilar:  mpicc arreglo_flotantes.c -o arreglo
 * Ejecutar:  mpirun -np 6 ./arreglo
 */

#include <stdio.h>
#include <mpi.h>

#define N 5          /* elementos del arreglo */
#define RECEPTORES 5 /* procesos que reciben el arreglo */
#define ETIQUETA 0

int main(int argc, char *argv[])
{
    int id, total, longitud, i, pos;
    char nodo[MPI_MAX_PROCESSOR_NAME];
    char linea[512];
    float arreglo[N];
    MPI_Status estado;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &id);
    MPI_Comm_size(MPI_COMM_WORLD, &total);
    MPI_Get_processor_name(nodo, &longitud);

    /* Se necesitan el proceso 0 y 5 receptores */
    if (total < RECEPTORES + 1) {
        if (id == 0)
            printf("Se necesitan al menos %d procesos. Usa: mpirun -np 6 ./arreglo\n",
                   RECEPTORES + 1);
        MPI_Finalize();
        return 0;
    }

    if (id == 0) {
        /* Arreglo con 5 valores diferentes */
        float datos[N] = {1.5f, 2.75f, 3.14f, 4.2f, 5.9f};

        pos = sprintf(linea, "Proceso %d en el nodo %s envia el arreglo: [", id, nodo);
        for (i = 0; i < N; i++)
            pos += sprintf(linea + pos, "%.2f%s", datos[i], (i < N - 1) ? ", " : "]\n");
        printf("%s", linea);
        fflush(stdout);

        /* Envío a los procesos 1 a 5 */
        for (i = 1; i <= RECEPTORES; i++)
            MPI_Send(datos, N, MPI_FLOAT, i, ETIQUETA, MPI_COMM_WORLD);
    }
    else if (id <= RECEPTORES) {
        /* Cada receptor espera el arreglo del proceso 0 */
        MPI_Recv(arreglo, N, MPI_FLOAT, 0, ETIQUETA, MPI_COMM_WORLD, &estado);

        /* Se arma toda la línea antes de imprimir para que no se mezcle con otras */
        pos = sprintf(linea, "Proceso %d en el nodo %s recibio: [", id, nodo);
        for (i = 0; i < N; i++)
            pos += sprintf(linea + pos, "%.2f%s", arreglo[i], (i < N - 1) ? ", " : "]\n");
        printf("%s", linea);
        fflush(stdout);
    }
    else {
        /* Si se lanzan más de 6 procesos, los extra solo se reportan */
        printf("Proceso %d en el nodo %s no participa en el envio\n", id, nodo);
        fflush(stdout);
    }

    MPI_Finalize();
    return 0;
}
