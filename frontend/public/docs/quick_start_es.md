# ComfyLAB: Guía de Inicio Rápido y Resumen General
*Comfortable Lab Automation Blocks — Manual de Usuario, Resumen del Software y Referencia de Tutoriales Prácticos*

---

## 1. Introducción y Filosofía

### 1.1 ¿Qué es ComfyLAB?
**ComfyLAB** (**Comf**ortable **L**ab **A**utomation **B**locks) es una plataforma de programación visual de código abierto diseñada específicamente para la automatización de experimentos científicos, pruebas y mediciones, adquisición de datos (DAQ) y visualización en tiempo real.

En los laboratorios de investigación modernos, las configuraciones de medición automatizadas a menudo requieren conectarse con hardware diverso (osciloscopios, fuentes de alimentación, multímetros, generadores de funciones, sensores personalizados) a través de varios protocolos (VISA, SCPI, Serial RS-232/RS-485, Ethernet, DLL nativas de C/C++). Escribir scripts de automatización en lenguajes tradicionales frecuentemente resulta en código repetitivo para el manejo de bucles, seguridad de hilos, manejo de excepciones, análisis de datos y renderizado de GUI.

ComfyLAB resuelve esto proporcionando una interfaz gráfica limpia y modular donde los usuarios arrastran **Bloques** funcionales a un lienzo digital y los conectan con **Cables** visuales.

---

### 1.2 Arquitectura Dual: Interfaz Web + Motor de Servidor en Python
ComfyLAB opera bajo un modelo cliente-servidor desacoplado:
<div style="page-break-before: always; break-before: page;"></div>

1. **Cliente Web en el Navegador (Frontend):** Construido con React, maneja la interfaz de arrastrar y soltar (diagramación visual). Es ligero, receptivo e independiente del sistema operativo. Muestra actualizaciones de datos en vivo y renderiza gráficos Plotly.
2. **Motor de Ejecución y Hardware en Python (Backend):** Una aplicación FastAPI que interactúa de manera nativa con hardware (a través de PyVISA, PySerial, ctypes). Compila el diagrama visual en un grafo de ejecución en Python. Mantiene el estado, la memoria de ejecución y las conexiones de hardware activas incluso cuando el navegador se cierra.

---

## 2. Empezando: Interfaz y Conceptos Básicos

### 2.1 El Lienzo (Blueprint)
El espacio de trabajo principal en ComfyLAB se llama **Blueprint** (Plano). Un Blueprint es la representación guardada de tu configuración.
* **Añadir Bloques:** Usa la **Biblioteca de Bloques** en la barra lateral izquierda (haciendo clic en "Mostrar Biblioteca" o presionando `B`).
* **Conectar Bloques:** Haz clic y arrastra desde el pin de salida de un bloque hasta el pin de entrada de otro bloque.
* **Ejecutar Blueprint:** Haz clic en el botón de reproducción `Ejecutar Blueprint` en la barra superior (o presiona `F5`).

<div style="page-break-before: always; break-before: page;"></div>

---

## 3. Tipos de Pines: Ejecución vs. Datos

ComfyLAB distingue estrictamente entre el orden en que se ejecutan los bloques (Flujo de Control) y el flujo de datos entre bloques (Flujo de Datos).

### 3.1 Pines de Ejecución (Pines Triangulares ►)
* Ubicados en la parte superior del bloque (arriba a la izquierda para entrada de ejecución, arriba a la derecha para salida de ejecución).
* Determinan la **secuencia** temporal en la que se ejecutan los bloques.
* Un bloque no se ejecutará hasta que su pin de ejecución de entrada reciba una señal (a menos que el bloque sea un *Nodo Raíz* sin entrada de ejecución o un componente de interfaz pasivo).
* **Ejemplo:** En un `Bucle For`, el pin "Loop Body" (Cuerpo del Bucle) dispara las acciones internas para cada iteración, mientras que "On Complete" (Al Completar) se dispara después de que termina el bucle.

### 3.2 Pines de Datos (Pines Circulares ●)
* Ubicados a lo largo de los lados inferiores del bloque (abajo a la izquierda para datos de entrada, abajo a la derecha para datos de salida).
* Pasan valores de memoria (Números, Cadenas, Arreglos Numpy, Identificadores VISA) entre bloques.
* **Evaluación Perezosa y Tipado Fuerte:** Los pines de datos validan el tipo. Si un tipo es incompatible (ej. conectar una Cadena a un puerto Booleano), la conexión puede fallar o mostrar una advertencia. Los valores se pasan durante el ciclo de ejecución definido por los pines de ejecución.

<div style="page-break-before: always; break-before: page;"></div>

---

## 4. Dominando el Flujo de Trabajo: Inspector de Bloques y Herramientas

### 4.1 Cómo entender mejor un Bloque (El Inspector de Bloques)
Seleccionar cualquier bloque en el lienzo abre el panel del **Inspector de Bloques** en la barra lateral derecha. El inspector es tu herramienta principal para monitorear estados de pines y depurar:

* **Pestaña de Parámetros (Parámetros Opcionales):** Muchos bloques (como Osciloscopios o Instrumentos VISA) tienen configuraciones opcionales que saturarían el lienzo. El inspector te permite alternar qué campos de entrada son visibles en el propio bloque.
* **Inspección de Datos en Vivo:** Mientras un Blueprint se ejecuta o está pausado, el inspector muestra los **valores en tiempo real** mantenidos en todos los pines de entrada y salida del bloque. Esto es invaluable para depurar resultados matemáticos o analizar cadenas SCPI en bruto.
* **Pestaña de Consola / Diagnósticos:** Si un bloque imprime texto o encuentra un error, se muestra aquí. Inspecciona declaraciones print, advertencias y mensajes de error generados durante la ejecución.

<div style="page-break-before: always; break-before: page;"></div>

### 4.2 Estados de los Bloques (Persistencia, Deshabilitación y Depuración)

* **Bloques Persistentes (PIN 📌):**
  **¿Por qué usar Bloques Persistentes?** Marcar un bloque como **Persistente** (a través del clic derecho o en el Inspector de Bloques) preserva su estado interno y recursos activos entre ejecuciones. Esto es esencial para:
  * **Conexiones de Hardware:** Un bloque "Abrir VISA" configurado como Persistente no cerrará y reabrirá la conexión del dispositivo cada vez que presiones Ejecutar. 
  * **Variables Globales:** Acumular datos o mantener contadores entre diferentes ejecuciones manuales del mismo Blueprint.

* **Deshabilitar Bloques (Bypass 🚫):**
  Si deseas saltar temporalmente un bloque sin desenredar sus cables:
  * Haz clic derecho en un bloque y selecciona **Deshabilitar Bloque** (o actívalo en el Inspector).
  * Los bloques deshabilitados pasarán las señales de ejecución a sus pines de salida predeterminados sin ejecutar su lógica interna.

### 4.3 Navegación y Herramientas del Lienzo
* **Modos de Selección (Marquesina):** Mantén presionada la tecla `Shift` y arrastra en el lienzo para seleccionar múltiples bloques y moverlos juntos.
* **Auto-Organizar (Varita Mágica):** Si tu Blueprint se vuelve desordenado, haz clic en el botón Auto-Organizar en el menú de herramientas flotante inferior para realinear lógicamente el flujo de trabajo (algoritmo Dagre).
* **Agrupación (Clústeres 📦):** Agrupa arreglos de bloques complejos en un solo bloque personalizado. Hacer doble clic en un bloque de clúster abre un sub-lienzo aislado, con migas de pan en la parte superior para la navegación.
* **Modo Pizarra (🎨):** Haz clic en el ícono de la herramienta o presiona la tecla `4` para alternar el modo de dibujo, permitiendo agregar notas a mano alzada, cuadros de texto y formas directamente sobre el lienzo.

<div style="page-break-before: always; break-before: page;"></div>

---

## 5. Resumen de las Categorías de Bloques Incorporadas

| Categoría | Descripción y Bloques Comunes |
| :--- | :--- |
| 🔄 **Flujo de Control** | Bucle For, Bucle While, Bifurcación If/Else, Retraso/Pausa, Detener Ejecución. |
| 🔢 **Matemáticas y Lógica** | Suma, Resta, Multiplicación, División, Evaluador de Fórmulas, Seno/Coseno, Trigonometría, Exponencial, Logaritmo, Comparaciones (`>`, `<`, `==`), Lógica AND, OR, NOT. |
| 📝 **Datos y Cadenas** | Concatenar Cadenas, Formatear Texto, Búsqueda Regex, Divisor de Cadenas, Creador de Listas, Indexador de Listas, Creador de Diccionarios, Obtener Valor por Clave. |
| 📊 **Arreglos y Señales** | Crear Arreglo, Range/Linspace, Corte de Arreglos, Espectro de Potencia FFT, Filtros Paso Bajo/Paso Alto, Detrend, Estadísticas (Media, Desv. Estándar, Mín, Máx), Detector de Picos, Ajuste de Curvas (Gaussiana, Exponencial, Polinómica, Personalizada). |
| 💾 **E/S de Archivos** | Leer/Escribir archivos CSV, E/S de JSON, Almacenamiento Parquet, Leer/Escribir Archivos de Texto, Cargar/Guardar Imágenes. |
| 📡 **VISA y Hardware** | Abrir Recurso VISA, Escritura SCPI, Lectura SCPI, Consulta SCPI, Cerrar VISA, Abrir/Leer/Escribir Puerto Serie. |
| 🔬 **Controladores de Instrumentos** | Configuración de Osciloscopio y Lectura de Ondas, Lectura de Multímetro Digital (DMM), Ajuste/Lectura de Fuente de Alimentación de CC, Configuración de Generador de Funciones y muchos más. |
| 📈 **Pantalla e Interfaz** | Graficador de Líneas Interactivo (Trazo Único y Múltiple, Ejes Log/Lineal), Visor de Matrices de Imágenes, Visor de Tabla de Datos, Medidor Digital, Indicador de Estado. |
| ⚙️ **Nativo y Scripts** | Invocación de Biblioteca Nativa (DLL/SO), Nodo Script Políglota (Python, JS, Julia, Rust, etc.). |

<div style="page-break-before: always; break-before: page;"></div>

---

## 6. Tutoriales Prácticos Iniciales

### Tutorial 1: Flujo Matemático e Inspección en Vivo
**Objetivo**: Crear dos números, multiplicarlos, aplicar una fórmula matemática e inspeccionar el resultado en el Inspector de Bloques.

```
┌──────────────┐
│ Número (5.0) ├──┐   ┌─────────────┐   ┌─────────────┐
└──────────────┘  ├──▶│ Multiplicar ├──▶│ Fórmula     ├──► Salida
┌──────────────┐  │   └─────────────┘   │ "x^2 + 10"  │
│ Número (3.0) ├──┘                     └─────────────┘
└──────────────┘
```

#### Instrucciones Paso a Paso:
1. Abre ComfyLAB y crea un nuevo workspace/blueprint.
2. En la **Barra Lateral** izquierda, busca por `Number` (Número) y arrastra **dos** bloques Número al lienzo (canvas).
3. Establece el valor del primer bloque a `5.0` y del segundo a `3.0`.
4. Arrastra un bloque **Multiply** (Multiplicar - en *Matemáticas y Lógica*) al lienzo.
5. Conecta el pin de salida de datos del Número 1 a la Entrada A del bloque Multiplicar, y el Número 2 a la Entrada B.
6. Arrastra un bloque **Formula** (Fórmula) al lienzo. Establece su parámetro de ecuación a `x^2 + 10`.
7. Conecta el pin de salida del bloque Multiplicar (`15.0`) a la entrada `x` del bloque Fórmula.
8. Haz clic en **Ejecutar Blueprint** (▶️) en la barra de herramientas superior.
9. Haz clic en el bloque **Fórmula** para abrir el **Inspector de Bloques** en la barra lateral derecha.
10. **Verificación**: En el Inspector de Bloques, verifica el valor en vivo en el pin de salida. Debe calcular `(15)^2 + 10 = 235.0`.

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 2: Generación de Señal Sintética y Gráfico en Vivo
**Objetivo**: Generar un vector de onda senoidal con ruido, calcular su espectro de potencia FFT y renderizarlo en un graficador interactivo.

```
┌────────────────────┐     ┌────────────────────┐
│ Linspace (0 a 10s) ├────▶│ Generador de Seno  ├─┐
└────────────────────┘     └────────────────────┘ │
                                                  ▼
┌────────────────────┐     ┌────────────────────┐ │
│ Gráfico Interactivo│◀────┤ Señal + Ruido      │◀┘
└────────────────────┘     └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ Espectro FFT       │
                           └────────────────────┘
```

#### Instrucciones Paso a Paso:
1. Busca `Linspace` en la Barra Lateral. Establece `Start = 0`, `Stop = 10`, `Points = 1000` para crear un vector de tiempo.
2. Busca `Sine` (Seno - en *Matemáticas* o *Vectores*). Conecta la salida de Linspace a la entrada de tiempo del bloque Sine. Establece la frecuencia a `5.0 Hz`.
3. Añade un bloque de **Ruido Aleatorio** y un bloque de **Suma** (Add) para corromper la onda senoidal con ruido blanco (`Señal + Ruido`).
4. Arrastra un bloque **Graficador Interactivo** al lienzo.
5. Conecta el vector de tiempo al **Pin X** del graficador y la señal con ruido al **Pin Y**.
6. (Opcional) Conecta la señal con ruido a un bloque **Espectro FFT**, y conecta la salida del FFT a un segundo trazo en el graficador.
7. Haz clic en **Ejecutar Blueprint** (▶️).
8. **Verificación**: El widget del graficador en tu lienzo mostrará inmediatamente la onda senoidal con ruido en vivo. ¡Usa la rueda del ratón sobre el gráfico para acercar/alejar y arrastra para navegar por los ejes!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 3: Barrido Automático de Parámetros y Registro CSV
**Objetivo**: Usar un bucle `For Loop` para simular el barrido de voltaje de una fuente de alimentación, calcular el consumo de energía, mostrar la curva en vivo y registrar datos en un archivo CSV.

```
┌─────────────────────┐    ┌────────────────────┐
│ For Loop (0 a 50)   │▶──▶│ Escritor CSV       │
└──────────┬──────────┘    └────────────────────┘
           │ (Índice)
           ▼
┌─────────────────────┐
│ Voltaje = Índice*0.1│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Corriente = V / R   ├─► Graficador en Vivo
└─────────────────────┘
```

#### Instrucciones Paso a Paso:
1. Arrastra un bloque **For Loop** (Bucle For) al lienzo. 
2. Establece el contador de iteraciones del `For Loop` a `50`.
3. Dentro de la ruta de ejecución del bucle, multiplica el pin `Índice de Iteración` por `0.1` usando un bloque **Multiply** (Multiplicar) para generar un barrido de voltaje de `0.0 V` a `5.0 V`.
4. Divide el voltaje por una resistencia constante (`R = 100 Ohms`) usando un bloque **Divide** (Dividir) para calcular la corriente `I`.
5. Conecta ambos valores de Voltaje y Corriente a un bloque **CSV Writer** (Escritor CSV). Establece el nombre del archivo como `sweep_results.csv`.
6. Conecta el pin de ejecución de salida del bloque CSV de vuelta a la entrada de iteración del bucle para completar el ciclo.
7. Haz clic en **Ejecutar Blueprint** (▶️).
8. **Verificación**: Observa el bucle ejecutarse paso a paso con líneas de ejecución violetas animadas. Una vez completada la ejecución, abre la carpeta de tu workspace activo — ¡encontrarás el archivo `sweep_results.csv` poblado con las 50 filas de datos!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 4: Escribiendo y Publicando un Bloque de Script Python Personalizado
**Objetivo**: Crear un bloque de script Python personalizado que filtre los valores por debajo de un umbral, probarlo y publicarlo en la paleta de la barra lateral izquierda.

```
┌──────────────────────────────────────────────────┐
│ Bloque Script Personalizado (Python)             │
│ Entradas: data_in (Vector), threshold (Número)   │
│ Salidas:  filtered_data (Vector), count (Número) │
├──────────────────────────────────────────────────┤
│ arr = np.array(inputs['data_in'])                │
│ result = arr[arr > inputs['threshold']]          │
│ outputs['filtered_data'] = result.tolist()       │
│ outputs['count'] = len(result)                   │
└──────────────────────────────────────────────────┘
```

#### Instrucciones Paso a Paso:
1. Arrastra un **Script Block** (de *Scripts y Nativo*) al lienzo. Selecciona **Python** como lenguaje.
2. En el **Inspector de Bloques**, haz clic en **Editar Pines**:
   * Añadir Pin de Entrada: `data_in` (Tipo: Vector)
   * Añadir Pin de Entrada: `threshold` (Tipo: Número)
   * Añadir Pin de Salida: `filtered_data` (Tipo: Vector)
   * Añadir Pin de Salida: `count_passed` (Tipo: Número)
3. Haz doble clic en el Script Block para abrir el editor de código integrado.
4. Escribe el fragmento de código Python mostrado arriba.
5. Conecta un vector de prueba en `data_in` y establece `threshold = 2.5`.
6. Haz clic en **Ejecutar Blueprint** (▶️) e inspecciona `filtered_data` y `count_passed` en el Inspector de Bloques.
7. Una vez verificado, haz clic en **Publicar Bloque** en el Inspector de Bloques. Nómbralo como `Filtro de Umbral`, elige un icono y asígnalo a la categoría `Vectores`.
8. **Verificación**: Mira en la paleta de la **Barra Lateral** izquierda. ¡Tu nuevo bloque `Filtro de Umbral` ahora está permanentemente disponible para arrastrarlo a cualquier lienzo de tu workspace!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 5: Interfaz de Hardware VISA (Consulta de Identificación SCPI)
**Objetivo**: Conectar a un instrumento físico o simulado a través de VISA, enviar una consulta SCPI `*IDN?` y mostrar el modelo del instrumento como respuesta.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ VISA Abrir  │▶─▶│ Consulta SCPI▶─▶│ VISA Cerrar │
│ Recurso     ├─▶ │ "*IDN?"     ├─▶ │ Identificador│
└─────────────┘   └──────┬──────┘   └─────────────┘
                         │ String de Respuesta
                         ▼
                  [Inspector de Bloques]
```

#### Instrucciones Paso a Paso:
1. Arrastra un bloque **VISA Open** al lienzo. Establece el parámetro de String de Recurso a la dirección de tu instrumento (ej. `TCPIP0::192.168.1.100::INSTR`, `GPIB0::14::INSTR`, o `COM3`).
2. Arrastra un bloque **SCPI Query**. Conecta la salida de ejecución (`ExecOut`) del VISA Open a la entrada (`ExecIn`) de Consulta SCPI.
3. Conecta el pin de salida `Handle VISA` (pin cian) de VISA Open a la entrada `Handle VISA` de Consulta SCPI.
4. Establece el parámetro de string de comando en la Consulta SCPI a `*IDN?\n`.
5. Arrastra un bloque **VISA Close** y conecta la línea de ejecución y el handle VISA a él para asegurar la liberación limpia del recurso.
6. Haz clic en **Ejecutar Blueprint** (▶️).
7. **Verificación**: Haz clic en el bloque **SCPI Query** y mira el Inspector de Bloques. El pin de salida de string mostrará la identificación del fabricante (ej., `HEWLETT-PACKARD,34401A,0,11-5-2` o `KEYSIGHT TECHNOLOGIES,DSOX2002A,...`).
8. **Consejo**: ¡También puedes aprovechar el bloque Administrador de Recursos VISA para descubrir instrumentos conectados automáticamente!


<div style="page-break-before: always; break-before: page;"></div>

---
