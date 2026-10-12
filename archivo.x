/* definicion del programa */
/* Nombre del programa o servicio */
program PROGRAMAINCREMENTO {
    /* versiones del servicio una o mas */
    version INCREMENTOVERS {
        /* funciones RPC */
        int INCREMENTO(int) = 1;   /* id del procedimiento */
    } = 1;                         /* numero de la version */
} = 0x20000001;                    /* Numero unico de programa */
