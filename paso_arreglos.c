/*
 * Integrantes:
 *   - Camarena Arévalo Yael Eduardo - 318279864
 *   - León Flores Pedro David - 316254283
 *   - Rosas Hernández Nahim - 314126900
 *   - Salinas Suárez Julián Enrique - 422071938
 *
 * Fecha: 17/09/2026
 *
 * Sistemas Distribuidos - Proyecto 1, parte 2, inciso a)
 * Paso de dos arreglos entre procesos (anillo).
 *
 * El proceso 0 inicializa un arreglo A de enteros y uno B de flotantes,
 * los imprime y se los envía al proceso 1. Cada proceso que los recibe
 * les agrega un elemento a cada uno, los imprime junto con su id y se los
 * manda al siguiente. El último proceso se los regresa al proceso 0, que
 * imprime cómo quedaron al terminar la vuelta.
 *
 * Compilar:  mpicc paso_arreglos.c -o paso_arreglos
 * Ejecutar:  mpirun -np 4 ./paso_arreglos
 */

#include <stdio.h>
#include <mpi.h>

#define NELEMENTS 5   /* tamaño inicial de los arreglos */
#define MAXTAM 64     /* espacio reservado para el crecimiento */
#define TAG_A 1       /* etiqueta del mensaje del arreglo de enteros */
#define TAG_B 2       /* etiqueta del mensaje del arreglo de flotantes */

/* Imprime los dos arreglos en una sola línea para que no se mezclen
   con la salida de los demás procesos */
void imprime(int id, const char *texto, int A[], float B[], int n)
{
    char linea[1024];
    int i, pos;

    pos = sprintf(linea, "Proceso %d - %s (n = %d)\n", id, texto, n);

    pos += sprintf(linea + pos, "   A = [");
    for (i = 0; i < n; i++)
        pos += sprintf(linea + pos, "%d%s", A[i], (i < n - 1) ? ", " : "]\n");

    pos += sprintf(linea + pos, "   B = [");
    for (i = 0; i < n; i++)
        pos += sprintf(linea + pos, "%.2f%s", B[i], (i < n - 1) ? ", " : "]\n");

    printf("%s", linea);
    fflush(stdout);
}

int main(int argc, char *argv[])
{
    int id, np, i, n;
    int anterior, siguiente;
    int A[MAXTAM];
    float B[MAXTAM];
    MPI_Status estado;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &id);
    MPI_Comm_size(MPI_COMM_WORLD, &np);

    /* El anillo se cierra con el operador módulo, así el último proceso
       le envía de regreso al proceso 0 */
    siguiente = (id + 1) % np;
    anterior = (id - 1 + np) % np;

    if (np < 2) {
        if (id == 0)
            printf("Se necesitan al menos 2 procesos. Usa: mpirun -np 4 ./paso_arreglos\n");
        MPI_Finalize();
        return 0;
    }

    if (NELEMENTS + np > MAXTAM) {
        if (id == 0)
            printf("Demasiados procesos para el tamaño reservado. Aumenta MAXTAM.\n");
        MPI_Finalize();
        return 0;
    }

    if (id == 0) {
        /* Valores iniciales */
        n = NELEMENTS;
        for (i = 0; i < n; i++) {
            A[i] = i + 1;             /* 1, 2, 3, 4, 5 */
            B[i] = (i + 1) * 1.5f;    /* 1.5, 3.0, 4.5, 6.0, 7.5 */
        }

        imprime(id, "arreglos iniciales", A, B, n);

        /* Arranca el recorrido mandándoselos al proceso 1 */
        MPI_Send(A, n, MPI_INT, siguiente, TAG_A, MPI_COMM_WORLD);
        MPI_Send(B, n, MPI_FLOAT, siguiente, TAG_B, MPI_COMM_WORLD);

        /* Espera a que los arreglos regresen después de dar la vuelta.
           Cada uno de los np - 1 procesos restantes agregó un elemento */
        n = NELEMENTS + (np - 1);
        MPI_Recv(A, n, MPI_INT, anterior, TAG_A, MPI_COMM_WORLD, &estado);
        MPI_Recv(B, n, MPI_FLOAT, anterior, TAG_B, MPI_COMM_WORLD, &estado);

        imprime(id, "arreglos finales al regresar", A, B, n);
    }
    else {
        /* Tamaño con el que le llegan los arreglos a este proceso:
           el inicial más un elemento por cada proceso anterior */
        n = NELEMENTS + (id - 1);

        MPI_Recv(A, n, MPI_INT, anterior, TAG_A, MPI_COMM_WORLD, &estado);
        MPI_Recv(B, n, MPI_FLOAT, anterior, TAG_B, MPI_COMM_WORLD, &estado);

        /* Agrega un elemento a cada arreglo */
        A[n] = 100 + id;
        B[n] = 100.0f + id;
        n = n + 1;

        imprime(id, "arreglos recibidos con su elemento agregado", A, B, n);

        /* Se los pasa al siguiente proceso del anillo */
        MPI_Send(A, n, MPI_INT, siguiente, TAG_A, MPI_COMM_WORLD);
        MPI_Send(B, n, MPI_FLOAT, siguiente, TAG_B, MPI_COMM_WORLD);
    }

    MPI_Finalize();
    return 0;
}
