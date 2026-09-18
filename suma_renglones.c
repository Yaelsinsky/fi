/*
 * Integrantes:
 *   - Camarena Arévalo Yael Eduardo - 318279864
 *   - León Flores Pedro David - 316254283
 *   - Rosas Hernández Nahim - 314126900
 *   - Salinas Suárez Julián Enrique - 422071938
 *
 * Fecha: 17/09/2026
 *
 * Sistemas Distribuidos - Proyecto 1, parte 2, inciso b)
 * Suma de los renglones de una matriz usando comunicaciones colectivas.
 *
 * El proceso 0 inicializa una matriz A de N x M con números enteros y la
 * reparte entre todos los procesos con MPI_Scatter. Cada proceso calcula
 * la suma de los renglones que le tocaron y determina cuál de sus renglones
 * locales tiene la menor suma. Después, con MPI_Gather, todas las sumas
 * regresan al proceso 0, que imprime la matriz inicial, el renglón con la
 * menor suma y el renglón con la mayor suma.
 *
 * Compilar:  mpicc suma_renglones.c -o suma_renglones
 * Ejecutar:  mpirun -np 4 ./suma_renglones
 */

#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

#define N 8      /* renglones de la matriz, debe ser divisible entre np */
#define M 6      /* columnas de la matriz */
#define SEMILLA 12345

int main(int argc, char *argv[])
{
    int id, np, i, j;
    int renglones;              /* renglones que le tocan a cada proceso */
    int matriz[N][M];           /* matriz completa, la llena el proceso 0 */
    int bloque[N * M];          /* pedazo de la matriz que recibe cada proceso */
    int sumas_locales[N];       /* sumas de los renglones de este proceso */
    int sumas[N];               /* todas las sumas, las junta el proceso 0 */
    int suma, menor, mayor, renglon_menor, renglon_mayor;
    char linea[512];
    int pos;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &id);
    MPI_Comm_size(MPI_COMM_WORLD, &np);

    /* El enunciado pide mínimo 4 procesos y que N sea divisible entre np */
    if (np < 4 || N % np != 0) {
        if (id == 0)
            printf("Se necesitan al menos 4 procesos y que %d sea divisible entre ellos.\n", N);
        MPI_Finalize();
        return 0;
    }

    renglones = N / np;

    /* El proceso 0 inicializa la matriz */
    if (id == 0) {
        srand(SEMILLA);
        for (i = 0; i < N; i++)
            for (j = 0; j < M; j++)
                matriz[i][j] = rand() % 20 + 1;

        printf("Matriz inicial de %d x %d\n", N, M);
        for (i = 0; i < N; i++) {
            pos = sprintf(linea, "   Renglon %d:", i);
            for (j = 0; j < M; j++)
                pos += sprintf(linea + pos, " %3d", matriz[i][j]);
            printf("%s\n", linea);
        }
        printf("\n");
        fflush(stdout);
    }

    /* Se reparte la matriz. Cada proceso recibe renglones * M enteros.
       Solo el proceso 0 necesita tener llena la matriz de origen */
    MPI_Scatter(matriz, renglones * M, MPI_INT,
                bloque, renglones * M, MPI_INT,
                0, MPI_COMM_WORLD);

    /* Cada proceso suma los renglones que le tocaron */
    menor = 0;
    for (i = 0; i < renglones; i++) {
        suma = 0;
        for (j = 0; j < M; j++)
            suma = suma + bloque[i * M + j];
        sumas_locales[i] = suma;

        if (i == 0 || suma < sumas_locales[menor])
            menor = i;
    }

    /* Cada proceso reporta lo que encontró en su bloque local.
       El renglon global se obtiene con el desplazamiento del proceso */
    pos = sprintf(linea, "Proceso %d - renglones %d a %d, sumas:",
                  id, id * renglones, id * renglones + renglones - 1);
    for (i = 0; i < renglones; i++)
        pos += sprintf(linea + pos, " %d", sumas_locales[i]);
    pos += sprintf(linea + pos, " | menor local: renglon %d con %d\n",
                   id * renglones + menor, sumas_locales[menor]);
    printf("%s", linea);
    fflush(stdout);

    /* Todas las sumas se juntan en el proceso 0, en orden */
    MPI_Gather(sumas_locales, renglones, MPI_INT,
               sumas, renglones, MPI_INT,
               0, MPI_COMM_WORLD);

    /* El proceso 0 decide cuál renglón tiene la menor y la mayor suma */
    if (id == 0) {
        renglon_menor = 0;
        renglon_mayor = 0;
        for (i = 1; i < N; i++) {
            if (sumas[i] < sumas[renglon_menor])
                renglon_menor = i;
            if (sumas[i] > sumas[renglon_mayor])
                renglon_mayor = i;
        }
        menor = sumas[renglon_menor];
        mayor = sumas[renglon_mayor];

        printf("\nSumas de todos los renglones:\n");
        for (i = 0; i < N; i++)
            printf("   Renglon %d: %d\n", i, sumas[i]);

        printf("\nEl renglon con la MENOR suma es el %d, con una suma de %d\n",
               renglon_menor, menor);
        printf("El renglon con la MAYOR suma es el %d, con una suma de %d\n",
               renglon_mayor, mayor);
        fflush(stdout);
    }

    MPI_Finalize();
    return 0;
}
