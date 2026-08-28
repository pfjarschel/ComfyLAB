# ComfyLAB: Guía de Inicio Rápido y Resumen General
*Comfortable Lab Automation Blocks — Manual de Usuario, Resumen del Software y Referencia de Tutoriales Prácticos*

---

## 1. Introducción y Filosofía

### 1.1 ¿Qué es ComfyLAB?
**ComfyLAB** (**Comf**ortable **L**ab **A**utomation **B**locks) es una plataforma de programación visual de código abierto, diseñada específicamente para la automatización de experimentos científicos, prueba y medición, adquisición de datos (DAQ) y visualización en tiempo real.

En laboratorios de investigación modernos, los sistemas de medición automatizados a menudo requieren conectarse con hardware diverso (osciloscopios, fuentes de alimentación, multímetros, generadores de funciones, sensores personalizados) a través de varios protocolos (VISA, SCPI, Serial RS-232/RS-485, Ethernet, bibliotecas nativas DLL de C/C++). Escribir scripts de automatización tradicionales frecuentemente resulta en código repetitivo (boilerplate) para gestión de bucles, sincronización entre hilos, manejo de excepciones, análisis de datos y desarrollo de interfaces gráficas.

ComfyLAB resuelve este desafío proporcionando una interfaz gráfica limpia y modular, donde los usuarios arrastran **Bloques** funcionales a un lienzo digital, los conectan mediante **Cables** visuales y organizan los resultados en un **Dashboard** interactivo al instante.

---

### 1.2 Arquitectura Dual: Interfaz Web + Motor de Servidor en Python
ComfyLAB opera bajo un modelo cliente-servidor desacoplado:
<div style="page-break-before: always; break-before: page;"></div>

```
┌──────────────────────────────────────────────────────────┐
│                   INTERFAZ WEB (FRONT-END)               │
│ - Lienzo Web (React + XY Flow)                           │
│ - Colocación y Conexión de Bloques Drag-and-Drop         │
│ - Cockpit Dedicado de Dashboard del Operador (Atajo: D)  │
│ - Gráficos Interactivos 2D y 3D y Pantallas en Vivo      │
│ - Capa de Pizarra Digital (Whiteboard) y Anotaciones     │
└────────────────────────────┬─────────────────────────────┘
                             │ WebSocket / API HTTP
┌────────────────────────────▼─────────────────────────────┐
│             SERVIDOR DE EJECUCIÓN (BACK-END)             │
│ - Motor Central en Python + API (FastAPI)                │
│ - Ejecutor de Máquina de Estados Híbrida Push/Pull       │
│ - Drivers de Hardware VISA y Gestor de Bloqueo Serial    │
│ - Servidor de Instrumentos Virtuales Embebidos (SCPI)    │
│ - Procesamiento de Señales NumPy/SciPy y FFT             │
│ - Scripting Multilenguaje e Invocación DLL / SO          │
└──────────────────────────────────────────────────────────┘
```

* **Lienzo Front-End & Dashboard**: Se ejecuta en navegadores web modernos (o como aplicación de escritorio compilada). Proporciona manipulación gráfica fluida, herramientas de auto-organización, zoom/pan interactivo en gráficos, capa de pizarra digital y un **Dashboard del Operador** que organiza tarjetas fijadas, controles y monitores en una sala de control simplificada.
* **Servidor Back-End**: Impulsado por Python y FastAPI. Administra bloqueos de hardware en tiempo real, consultas VISA/SCPI, cálculos matriciales pesados, ejecución multihilo, persistencia de archivos, entornos virtuales de Python y un proceso en segundo plano para **Instrumentos Virtuales**.

---

### 1.3 Seguridad y Protección Integradas

* **Protección de Instrumentos y Rutinas de Apagado Seguro (Teardown)**: El hardware físico de laboratorio (láseres, fuentes de alto voltaje, generadores RF) requiere una gestión estricta de seguridad. Si una ejecución de medición encuentra un error, se detiene manualmente o se pierde la conexión, ComfyLAB ejecuta automáticamente rutinas de apagado seguro (shutdown hooks) para desactivar salidas activas y devolver los instrumentos a estados seguros.
* **Verificación de Seguridad de Blueprints**: Al abrir blueprints de fuentes externas, ComfyLAB ejecuta comprobaciones de seguridad para evitar la ejecución no autorizada de scripts, ofreciendo confirmación rápida y control total antes de ejecutar código.
* **Acceso Remoto Seguro**: ComfyLAB admite la operación remota segura a través de la red mediante autenticación por token, lo que permite a los investigadores supervisar y controlar experimentos que se ejecutan en computadoras de laboratorio desde estaciones de trabajo remotas.
* **Comprobador Integrado de Actualizaciones**: Administrador de versiones en el diálogo *Acerca de* (About) que comprueba automáticamente nuevas versiones en PyPI / GitHub, muestra notas de versión y permite la actualización con un clic.

<div style="page-break-before: always; break-before: page;"></div>

---

## 2. Capacidades y Flexibilidad: Lo que Puede (y No Puede) Hacerse

ComfyLAB fue diseñado desde cero para ofrecer máxima flexibilidad sin limitar a los usuarios avanzados a plantillas rígidas.

### 2.1 Qué se Puede Hacer con ComfyLAB

| Área de Recurso | Capacidades y Extensibilidad |
| :--- | :--- |
| **Control de Hardware Físico** | Compatibilidad completa con **VISA** (GPIB, USB TMC, Ethernet/LXI, Serial RS-232/RS-485) y comandos estándar **SCPI**. Bloques integrados para osciloscopios comerciales, multímetros, fuentes de alimentación, generadores de funciones y espectrómetros Horiba. |
| **Instrumentos Virtuales Embebidos** | ¡Instrumentos de prueba y medición simulados por software listos para usar! Incluye un **Osciloscopio Virtual** (`virt_osc`) y un **Generador de Funciones Virtual** (`virt_siggen`) acoplados a una simulación de **Circuito RC**, permitiendo desarrollo y enseñanza completa offline sin hardware físico. |
| **Dashboard del Operador** | Vista dedicada de **Dashboard** (atajo `D`). Fija cualquier bloque, parámetro de control o gráfico en un cockpit de operación limpio. Reordena y redimensiona tarjetas para crear paneles listos para presentaciones y ensayos. |
| **Temporización y Monitoreo de Progreso** | Seguimiento visual de ejecución con **Countdown Wait** (reloj digital regresivo, barra de progreso y botón para saltar la espera), widgets de **Barra de Progreso** (0–100%), reloj digital de **Tiempo Restante Estimado (ETR)** y bucles inteligentes. |
| **Suite Completa de Gráficos Científicos** | Gráficos interactivos 2D y 3D en tiempo real: **Gráfico XY / Línea** (trazo simple/múltiple, log/lineal), **Gráfico Dual-Y** (dos ejes Y independientes), **Gráfico de Barras**, **Box Plot** (distribución estadística y valores atípicos), **Histograma**, **Superficie 3D y Dispersión 3D**, **Gráfico Polar**, **Cascada Espectral (Waterfall)** y Heatmaps 2D. |
| **Invocación de Bibliotecas Nativas** | Llama directamente a bibliotecas compartidas compiladas en C/C++ (`.dll` en Windows, `.so` en Linux/macOS) usando un **Editor de Firmas** interactivo sin escribir código Ctypes en Python. |
| **Scripts Multilenguaje Personalizados** | Crea **Bloques de Script** en 9 lenguajes: Python, Rust, JavaScript, TypeScript, Julia, R, Lua, Octave y Wolfram. Acceso a la variable de entorno `COMFYLAB_WORKSPACE` para leer y escribir archivos en la carpeta del proyecto. |
| **Acceso al Ecosistema Python** | Conecta bloques de script a entornos virtuales locales (`.venv`), con acceso completo a `scipy`, `numpy`, `pandas`, `opencv`, `scikit-learn`, `matplotlib` y paquetes de PyPI. |
| **Publicación de Bloques y Paquetes (.cfy)** | Publica bloques de script directamente en la paleta lateral o empaqueta flujos completos (blueprints, scripts y archivos) en archivos comprimidos redistribuibles `.cfy`. |
| **Procesamiento de Señales y Matemáticas** | Operaciones matriciales en NumPy, análisis espectral FFT, ajuste de curvas (Gaussiana, Exponencial, Polinómica, Personalizada), filtrado (pasa-bajos, pasa-altos, pasa-banda), eliminación de tendencia (detrend) y detección de picos. |
| **Sub-Lienzos Modulares (Clústeres)** | Agrupa sub-grafos complejos en **Bloques de Clúster** con pines de entrada y salida dinámicos para mantener diagramas limpios y jerárquicos. |
| **Capa de Pizarra Digital (Whiteboard)** | Añade notas adhesivas, texto enriquecido, figuras geométricas, flechas y dibujos libres directamente sobre el lienzo para documentación y organización visual. |

---

### 2.2 Límites Realistas: Qué No Se Puede (o No Se Debe) Hacer

Aunque ComfyLAB maneja prácticamente cualquier tarea de medición científica, automatización y procesamiento de datos, es útil reconocer sus límites:

* **Determinismo de Tiempo Real Estricto en Microsegundos**: ComfyLAB se ejecuta sobre sistemas operativos estándar (Windows/Linux/macOS) mediante servidores Python/FastAPI. Está diseñado para bucles de automatización y muestreo en la escala de milisegundos a sub-segundos. **No** está destinado a lógica bare-metal en FPGA ni a bucles deterministas de sub-microsegundos (ej. control PWM de motores a 100 kHz). Para esas tareas, microcontroladores RTOS o placas FPGA deben gestionar la temporización de bajo nivel, comunicándose con ComfyLAB por serial/USB para supervisión, almacenamiento y gráficos.

> **Resumen**: Fuera del determinismo en microsegundos vía hardware FPGA, **prácticamente cualquier flujo de medición científica, automatización de laboratorio, adquisición de datos o graficado puede construirse en ComfyLAB**.

<div style="page-break-before: always; break-before: page;"></div>

---

## 3. Comparación con Paradigmas Alternativos

Comprender cómo se compara ComfyLAB con las herramientas de laboratorio tradicionales destaca sus ventajas tanto para la enseñanza como para la investigación:

| Característica / Aspecto | Scripts Python Puros (PyVISA, Matplotlib) | National Instruments LabVIEW | MATLAB / Simulink | **ComfyLAB** |
| :--- | :--- | :--- | :--- | :--- |
| **Licencia y Costo** | Gratuito y Código Abierto | Licenciamiento Comercial Costoso | Licenciamiento Comercial Costoso | **Gratuito y Código Abierto (GPLv3)** |
| **Paradigma de Programación** | Código Basado en Texto | Código Gráfico Propietario G | Diagramas Gráficos / Código | **Diagramas de Bloques Web + Código Políglota** |
| **Curva de Aprendizaje** | Alta (Requiere experiencia en programación)| Media (Convenciones estrictas de G) | Media (Sintaxis y toolboxes complejas) | **Baja (Lienzo intuitivo drag-and-drop)** |
| **Configuración de GUI y Gráficos** | Manual (PyQt, Tkinter, Matplotlib) | Panel Frontal Integrado | Ventanas de Figuras Integradas | **Gráficos 2D/3D, Polar, Cascada y Dashboard Instantáneos** |
| **Simulación Offline** | Requiere librerías mock manuales | Simulación de software básica | Modelado físico en Simulink | **Osciloscopio, Generador y Circuito SCPI Virtuales Integrados** |
| **Formato de Archivo y Git** | Texto plano `.py` (Amigable con Git) | Binario Propietario `.vi` (Difícil diff en Git) | `.m` / Binario `.slx` | **Blueprints JSON Limpios (Compatibles con Git)** |
| **Código Personalizado** | Nativo | Nodos de Llamada Complejos C/Python | Funciones S / Código MATLAB | **Bloques de Script Políglotas (Python, C/C++, Rust, etc.)** |
| **Arquitectura** | Script monohilo / hilos manuales | Aplicación de Escritorio Monolítica | Entorno de Escritorio Pesado | **Interfaz Web Desacoplada + Servidor FastAPI** |
| **Bloqueo de Hardware (Locking)** | Requiere implementación manual de locks | Drivers Integrados VISA / DAQmx | Instrument Control Toolbox | **Gestor Automático de Bloqueo Asíncrono VISA** |

### Conclusiones Principales:
1. **Vs. Python Puro**: Python es sumamente potente, pero construir interfaces gráficas, gráficos interactivos en tiempo real, bucles de hardware y diagramas visuales exige cientos de líneas de código repetitivo. ComfyLAB mantiene todo el poder analítico de Python ofreciendo una interfaz visual inmediata y cockpit de operación.
2. **Vs. LabVIEW**: LabVIEW es ampliamente utilizado, pero sufre de costos elevados de licencia, archivos binarios propietarios que dificultan el control de versiones y dependencia de proveedor. ComfyLAB ofrece una alternativa moderna y libre con blueprints en JSON, instrumentos virtuales embebidos e integración web nativa.
3. **Vs. MATLAB**: MATLAB sobresale en álgebra matricial pero tiene licencias costosas. ComfyLAB aprovecha motores gratuitos y abiertos de NumPy/SciPy bajo el capó.

<div style="page-break-before: always; break-before: page;"></div>

---

## 4. Diseño de la Interfaz y Conceptos Fundamentales

### 4.1 Resumen del Diseño de la Interfaz

La interfaz de ComfyLAB consta de tres áreas funcionales principales rodeadas por controles superiores:

```
┌──────────────────────────────────────────────────────────────┐
│ BARRA SUPERIOR: [🟰][⚙️] | [▶ Ejecutar/⏸ Pausa] [🛑 Parar] | [📊 Dash]│
├────────────────┬──────────────────────────────┬──────────────┤
│ BARRA LATERAL  │ ÁREA PRINCIPAL / DASHBOARD   │ INSPECTOR    │
│ (Paleta Bloques│                              │ (Valores)    │
│                │  ┌───────┐   Cable Ejecución │              │
│ Buscar...      │  │ Entry │▶───┐              │ Entradas     │
│ Control Flujo  │  └───────┘    │              │ Datos en Vivo│
│ Matemáticas    │            ┌──▼────────────┐ │ Consola Logs │
│ VISA / Virtual │ Cable Datos│ Bloque Math   │ │              │
│ Instrumentos   │ ──────────▶└───────────────┘ │              │
│ Visualización  │                              │              │
│                │ [Minimapa]       [Herram 1-4]│              │
└────────────────┴──────────────────────────────┴──────────────┘
```

#### Descripción Detallada de la Interfaz:
* **Barra Superior**: Controles para ejecutar (▶️ / `Ctrl+R`), pausar (⏸️) y detener (🛑 / `Ctrl+Shift+R`) blueprints, abrir el **Dashboard del Operador** (📊 / `D`), guardar blueprints (`Ctrl+S`), cambiar temas de color y configurar opciones de VISA y diagnósticos.
* **Barra Lateral (Izquierda)**: Paleta con buscador que contiene todos los bloques nativos, bloques publicados, instrumentos virtuales y nodos de script agrupados por categoría.
* **Lienzo Principal (Centro)**: Espacio de trabajo infinito con zoom y desplazamiento para arrastrar y conectar bloques.
* **Inspector de Bloques (Derecha)**: Panel contextual que se abre al seleccionar un bloque. Muestra valores de pines en tiempo real, parámetros, notas de documentación y registros de consola.
* **Barra de Pestañas y Migas de Pan**: Permite navegar entre múltiples blueprints y profundizar en clústeres.

<div style="page-break-before: always; break-before: page;"></div>
---

### 4.2 Pines y Cables: Flujo de Ejecución vs. Valores de Datos

Las conexiones entre bloques en ComfyLAB se dividen estrictamente en dos categorías:

```
  Salida Ejec ▶══════════════════════════════▶ Entrada Ejec
              (Línea Violeta: Controla CUÁNDO se ejecutan los bloques)

  Salida Datos●──────────────────────────────● Entrada Datos
              (Línea Sólida: Transfiere VALORES bajo demanda)
```

1. **Pines de Ejecución (Flujo)**:
   * Representados por **conectores en forma de triángulo/flecha** y conectados mediante **líneas violetas (🟪)**.
   * Determinan el **orden temporal y flujo de control** (cuándo se ejecutan los pasos, repiten bucles o activan ramas).

2. **Pines de Datos (Valores)**:
   * Representados por **pines circulares de colores** y conectados mediante **líneas sólidas**.
   * Transportan **valores** (números, cadenas de texto, arreglos NumPy, diccionarios, identificadores de hardware).
   * Se evalúan bajo demanda cuando un bloque de ejecución solicita datos de entrada.

#### Referencia de Colores de Pines de Datos:
* 🟧 **Número (Naranja)**: Valores escalares enteros o decimales.
* 🟩 **Booleano (Verde)**: Banderas lógicas `True` o `False`.
* 🟪 **Cadena / String (Rosa)**: Textos, cadenas formateadas o comandos SCPI.
* 🟨 **Arreglo (Amarillo)**: Arreglos y matrices numéricas NumPy 1D/2D de alto rendimiento.
* 🟦 **Lista (Cian)**: Colecciones ordenadas de elementos.
* 🟫 **Diccionario (Marrón)**: Mapeos clave-valor.

---

### 4.3 Lógica de Ejecución y Cadenas Independientes
* **Disparo de Ejecución**: Al hacer clic en **Ejecutar Blueprint** (▶️ o `Ctrl+R`), la ejecución comienza en los bloques raíz (sin cables de ejecución entrantes) y avanza siguiendo los cables violetas.
* **Cadenas de Ejecución Independientes**: Si el lienzo contiene grupos de bloques aislados sin cables entre sí, ComfyLAB los trata automáticamente como cadenas paralelas que se ejecutan concurrentemente.
* **Bloques de Control de Flujo y Temporización**:
  * **Bucle For**: Ejecuta un sub-bucle una cantidad fija de iteraciones, emitiendo el índice actual, porcentaje de completitud (`%`) y tiempo restante estimado (`ETR`).
  * **Bucle Para Cada (For Each)**: Itera sobre cada elemento de una lista o arreglo, proporcionando elemento, índice, porcentaje y ETR.
  * **Bucle While**: Ejecuta continuamente un sub-bucle mientras una condición booleana permanezca en `True`.
  * **Bifurcación If / Else**: Enruta la ejecución hacia una salida `True` o `False` según una condición.
  * **Retraso / Sleep**: Pausa el flujo de ejecución durante un tiempo determinado (ms o segundos).
  * **Countdown Wait**: Pausa la ejecución con reloj digital regresivo en tiempo real, barra de descarga y botón para **Saltar Espera**.
  * **Barra de Progreso**: Widget visual dedicado para visualizar el avance de 0% a 100%.
  * **Reloj ETR**: Pantalla digital estilo sala de control con tiempo restante estimado (`HH:MM:SS` o `MM:SS`).
  * **Medidor de Tiempo (Measure Time)**: Mide con precisión el tiempo transcurrido entre eventos de ejecución.

---

### 4.4 Funciones Avanzadas

* **Dashboard del Operador y Tarjetas Fijadas (📊 / `D`)**: El Dashboard ofrece una vista despejada tipo sala de control para operar experimentos, presentar resultados o realizar prácticas de laboratorio sin la distracción de cables y bloques.
  * **Fijar Bloques en el Dashboard**: Cualquier bloque o pin puede fijarse al Dashboard. Haz clic derecho en el bloque y selecciona **Pin to Dashboard**, presiona el icono de alfiler en el Inspector de Bloques o usa el botón correspondiente en widgets compatibles.
  * **Organización Inteligente**: Las entradas y controles se agrupan en **Tarjetas de Control**, mientras que los gráficos, indicadores y cronómetros forman **Tarjetas de Monitoreo**.
  * **Personalización**: Reordena tarjetas arriba/abajo, arrastra las esquinas de los gráficos para redimensionarlos o haz clic en el icono de salto para regresar instantáneamente al bloque en el lienzo.
  * **Vista Maximizada**: Maximiza el panel del dashboard para convertirlo en una estación de control a pantalla completa.
* **Bloques Persistentes (📌)**: Por defecto, los estados de los bloques se reinician en cada corrida. Marcar un bloque como **Persistente** mantiene vivos sus recursos (ej. conexiones VISA, puertos seriales abiertos o promedios acumulados) entre ejecuciones consecutivas.
* **Deshabilitar Bloques (🚫)**: Hacer clic derecho y seleccionar deshabilitar atenúa el bloque en el lienzo. Los bloques deshabilitados se omiten en la ejecución, transfiriendo las señales limpiamente sin ejecutar código.
* **Clústeres (Sub-lienzos 📦)**: Agrupa conjuntos complejos de bloques en un único bloque personalizado. Hacer doble clic en un clúster abre un sub-lienzo aislado, con migas de pan para navegar.
* **Modo Pizarra (🎨)**: Presiona el atajo `4` para alternar al modo de dibujo, agregando notas, cuadros de texto y formas geométricas sobre el lienzo.

<div style="page-break-before: always; break-before: page;"></div>

---

## 5. Resumen de Categorías de Bloques Nativos

| Categoría | Descripción y Bloques Comunes |
| :--- | :--- |
| 🔄 **Control de Flujo y Tiempo** | Bucle For, Bucle Para Cada (For Each), Bucle While, Bifurcación If/Else, Retraso/Sleep, Countdown Wait, Medidor de Tiempo (Measure Time), Detener Ejecución. |
| 🔢 **Matemáticas y Lógica** | Suma, Resta, Multiplicación, División, Evaluador de Fórmulas, Seno/Coseno, Trigonometría, Exponencial, Logaritmo, Comparaciones (`>`, `<`, `==`), Lógica AND, OR, NOT. |
| 📝 **Datos y Cadenas** | Concatenar Cadenas, Formatear Texto, Búsqueda Regex, Divisor de Texto, Creador de Listas, Indexador de Listas, Creador de Diccionarios, Obtener Valor por Clave. |
| 📊 **Arreglos y Señales** | Crear Arreglo, Range/Linspace, Fatiado de Arreglos, Espectro de Potencia FFT, Filtros Paso Bajo/Paso Alto, Detrend, Estadísticas (Media, Desv. Estándar, Mín, Máx), Detector de Picos, Ajuste de Curvas (Gaussiana, Exponencial, Polinómica, Personalizada). |
| 💾 **E/S de Archivos** | Leer/Escribir archivos CSV, E/S de JSON, Almacenamiento Parquet, Leer/Escribir Archivos de Texto, Cargar/Guardar Imágenes. |
| 📡 **VISA y Hardware Físico** | Abrir Recurso VISA, Escritura SCPI, Lectura SCPI, Consulta SCPI (Query), Cerrar VISA, Abrir/Leer/Escribir Puerto Serie, Detección Automática de Instrumentos. |
| 🖥️ **Instrumentos Virtuales** | **VirtOsc** (Conexión, Base de Tiempo, Canales 1 y 2, Disparo/Trigger, Estado, Adquisición de Señal), **VirtSigGen** (Conexión, Onda Senoidal/Cuadrada/Triangular, Barrido Chirp, Nivel de Salida), Circuito RC Simulado. |
| 🔬 **Controladores de Instrumentos** | Osciloscopios (Tektronix, Keysight, Agilent), Multímetros Digitales (HP/Agilent 34401A, DMM Genérico), Fuentes DC (Keysight, Keithley), Generadores de Funciones, Espectrómetros Horiba Jobin Yvon, Digitalizadores CAEN, Motores Thorlabs. |
| 📈 **Pantalla, Gráficos y UI** | **Gráfico XY / Línea** (trazo simple/múltiple, log/lineal), **Gráfico Dual-Y**, **Gráfico de Barras**, **Box Plot**, **Histograma**, **Superficie 3D y Dispersión 3D**, **Gráfico Polar**, **Cascada Espectral (Waterfall)**, Matriz 2D Heatmap, Tabla, Medidor Digital, Indicador LED, **Barra de Progreso**, **Reloj ETR**, **Reloj Regresivo**. |
| ⚙️ **Nativo y Scripting** | Invocación de Biblioteca Nativa (DLL/SO) con Editor de Firmas, Nodos de Script Políglotas (Python, JS/TS, Julia, Rust, Lua, Octave, R, Wolfram) con soporte a la variable `COMFYLAB_WORKSPACE`. |

<div style="page-break-before: always; break-before: page;"></div>

---

## 6. Tutoriales Prácticos de Iniciación

Utiliza estos breves ejercicios paso a paso para familiarizarte con ComfyLAB antes o durante tu sesión de laboratorio.

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 1: Pipeline Matemático e Inspección en Vivo
**Objetivo**: Crear dos números, multiplicarlos, aplicar una fórmula matemática e inspeccionar el resultado en el Inspector de Bloques.

```
┌──────────────┐
│ Número (5.0) ├──┐   ┌───────────┐   ┌─────────────┐
│ Salida Datos │  ├──▶│Multiplicar├──▶│ Fórmula     ├──► Salida
└──────────────┘  │   └───────────┘   │ "x^2 + 10"  │
┌──────────────┐  │                   └─────────────┘
│ Número (3.0) ├──┘
│ Salida Datos │
└──────────────┘
```

#### Instrucciones Paso a Paso:
1. Abre ComfyLAB y crea un nuevo workspace/blueprint.
2. En la **Barra Lateral** izquierda, busca `Number` y arrastra **dos** bloques de Número al lienzo.
3. Establece el valor del primer bloque en `5.0` y el del segundo en `3.0`.
4. Arrastra un bloque **Multiply** (de la categoría *Matemáticas y Lógica*) al lienzo.
5. Conecta el pin de datos del Número 1 a la Entrada A del bloque Multiply, y el Número 2 a la Entrada B.
6. Arrastra un bloque **Formula** al lienzo. Define su ecuación como `x^2 + 10`.
7. Conecta el pin de salida de Multiply (`15.0`) a la entrada `x` del bloque Formula.
8. Haz clic en **Ejecutar Blueprint** (▶️ o `Ctrl+R`) en la barra superior.
9. Haz clic en el bloque **Formula** para abrir el **Inspector de Bloques** en la derecha.
10. **Verificación**: En el Inspector, revisa el valor de salida en vivo. Debería evaluarse como `(15)^2 + 10 = 235.0`.

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 2: Generación de Señal Sintética y Graficado en Vivo
**Objetivo**: Generar un arreglo de onda senoidal ruidosa, calcular su espectro FFT y mostrarlo en un gráfico interactivo.

```
┌────────────────────┐     ┌────────────────────┐
│ Linspace (0 a 10s) ├────▶│ Generador Onda Seno├─┐
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
1. Busca `Linspace` en la Barra Lateral. Establece `Start = 0`, `Stop = 10`, `Points = 1000` para generar un vector de tiempo.
2. Busca `Sine` (en *Matemáticas y Lógica* o *Arreglos*). Conecta la salida de Linspace a la entrada de tiempo del bloque Sine. Establece la frecuencia en `5.0 Hz`.
3. Agrega un bloque **Random Noise** y un bloque **Add** para sumar ruido blanco a la onda senoidal (`Señal + Ruido`).
4. Arrastra un bloque **Interactive Plotter** (XY Plot) al lienzo.
5. Conecta el arreglo de tiempo al **Pin X** del gráfico y la señal con ruido al **Pin Y**.
6. (Opcional) Conecta la señal con ruido a un bloque **FFT Spectrum** y envía la salida FFT a un segundo trazo en el graficador.
7. Haz clic en **Ejecutar Blueprint** (▶️).
8. **Verificación**: El widget del gráfico mostrará inmediatamente la onda senoidal con ruido en tiempo real. ¡Usa la rueda del ratón para hacer zoom y arrastra para desplazarte por los ejes!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 3: Barrido Automatizado de Parámetros y Registro en CSV
**Objetivo**: Usar un `Bucle For` para simular el barrido de voltaje de una fuente, calcular la corriente, mostrar la curva en vivo y guardar los datos en un archivo CSV.

```
┌─────────────────────┐    ┌────────────────────┐
│ Bucle For (0 a 50)  │▶──▶│ Escritor CSV       │
└──────────┬──────────┘    └────────────────────┘
           │ (Índice)
           ▼
┌─────────────────────┐
│ Voltaje = Ind*0.1   │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Corriente = V / R   ├─► Graficador en Vivo
└─────────────────────┘
```

#### Instrucciones Paso a Paso:
1. Arrastra un bloque **For Loop** al lienzo.
2. Establece la cantidad de iteraciones en `50`. Observa que el bloque proporciona pines de porcentaje (`%`) y tiempo restante estimado (`ETR`).
3. Dentro de la ruta de ejecución del bucle, multiplica el pin `Iteration Index` por `0.1` usando un bloque **Multiply** para crear un barrido de `0.0 V` a `5.0 V`.
4. Divide el voltaje entre una resistencia fija (`R = 100 Ohms`) usando un bloque **Divide** para obtener la corriente `I`.
5. Conecta los valores de Voltaje y Corriente a un bloque **CSV Writer**. Nombra el archivo como `sweep_results.csv`.
6. Conecta el cable de ejecución de salida del bloque CSV de regreso al pin de paso del bucle para completar la iteración.
7. Haz clic en **Ejecutar Blueprint** (▶️).
8. **Verificación**: Observa el avance paso a paso con las líneas violetas animadas. Al finalizar, abre la carpeta de tu espacio de trabajo: ¡encontrarás `sweep_results.csv` con las 50 filas registradas!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 4: Creación y Publicación de un Bloque de Script en Python
**Objetivo**: Crear un bloque de script personalizado que filtre valores por debajo de un umbral, probarlo y publicarlo en la paleta lateral izquierda.

```
┌──────────────────────────────────────────────────┐
│ Bloque de Script Personalizado (Python)          │
│ Entradas: data_in (Arreglo), threshold (Número)  │
│ Salidas:  filtered_data (Arreglo), count (Número)│
├──────────────────────────────────────────────────┤
│ arr = np.array(inputs['data_in'])                │
│ result = arr[arr > inputs['threshold']]          │
│ outputs['filtered_data'] = result.tolist()       │
│ outputs['count'] = len(result)                   │
└──────────────────────────────────────────────────┘
```

#### Instrucciones Paso a Paso:
1. Arrastra un bloque **Script Block** (de *Scripting & Native*) al lienzo. Selecciona **Python** como lenguaje.
2. En el **Inspector de Bloques**, haz clic en **Edit Pins**:
   * Entrada: `data_in` (Tipo: Array)
   * Entrada: `threshold` (Tipo: Number)
   * Salida: `filtered_data` (Tipo: Array)
   * Salida: `count_passed` (Tipo: Number)
3. Haz doble clic en el Bloque de Script para abrir el editor integrado.
4. Escribe el código mostrado arriba. (Ten en cuenta que `os.environ["COMFYLAB_WORKSPACE"]` está disponible para interactuar con archivos de tu proyecto).
5. Conecta un arreglo de prueba en `data_in` y establece `threshold = 2.5`.
6. Haz clic en **Ejecutar Blueprint** (▶️) y revisa `filtered_data` y `count_passed` en el Inspector.
7. Una vez comprobado, haz clic en **Publish Block** en el Inspector. Nómbralo como `Filtro Umbral`, asigna un icono y guárdalo en la categoría `Arrays`.
8. **Verificación**: Abre la paleta de la **Barra Lateral**. ¡Tu nuevo bloque estará permanentemente disponible para usarlo en cualquier blueprint!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 5: Interfaz de Hardware VISA (Consulta SCPI de Identificación)
**Objetivo**: Conectar a un instrumento físico o simulado mediante VISA, enviar una consulta SCPI `*IDN?` y mostrar la identificación del fabricante.

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│ Abrir VISA│▶───▶│Query SCPI │▶───▶│Cerrar VISA│
│ Recurso   ├────▶│ "*IDN?"   ├────▶│ Handle    │
└───────────┘     └─────┬─────┘     └───────────┘
                        │ Cadena de Respuesta
                        ▼
                  [Inspector de Bloques]
```

#### Instrucciones Paso a Paso:
1. Arrastra un bloque **VISA Open** al lienzo. Establece la cadena de recurso con la dirección de tu instrumento (ej. `TCPIP0::192.168.1.100::INSTR`, `GPIB0::14::INSTR` o `COM3`).
2. Arrastra un bloque **SCPI Query**. Conecta el `ExecOut` de VISA Open al `ExecIn` de SCPI Query.
3. Conecta el pin de salida `VISA Handle` (cian) de VISA Open a la entrada `VISA Handle` de SCPI Query.
4. Establece la orden en SCPI Query como `*IDN?
`.
5. Arrastra un bloque **VISA Close** y conecta el cable de ejecución y el handle VISA para garantizar la liberación limpia del recurso.
6. Haz clic en **Ejecutar Blueprint** (▶️).
7. **Verificación**: Haz clic en el bloque **SCPI Query** y revisa el Inspector de Bloques. El pin de salida mostrará la identificación (ej. `HEWLETT-PACKARD,34401A,0,11-5-2` o `KEYSIGHT TECHNOLOGIES,DSOX2002A,...`).
8. **Consejo**: ¡También puedes usar el Administrador de Recursos VISA para descubrir instrumentos automáticamente!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 6: Automatización Offline con Instrumentos Virtuales Embebidos
**Objetivo**: Conectar a los instrumentos virtuales integrados en ComfyLAB, configurar un generador de señales simulado, capturar la forma de onda en el osciloscopio virtual y monitorear los resultados en el Dashboard sin requerir hardware físico.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ VirtSigGen Conn │▶───▶│ Config Wave     │▶───▶│ VirtOsc Connect │
│ (TCP Virtual)   ├────▶│ Freq: 1 kHz     │     │ (TCP Virtual)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Fijar en        │◀────┤ Widget Gráfico  │◀────┤ Adquirir Señal  │
│ Dashboard (D)   │     │ Tiempo vs Volts │     │ Canal 1         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### Instrucciones Paso a Paso:
1. En la Barra Lateral, abre la categoría **Dispositivos > Virtual**.
2. Arrastra un bloque **VirtSigGen Connect** y un bloque **VirtSigGen Config Wave**. Conéctalos para emitir una onda senoidal de 1,0 kHz a 2,0 Vpp.
3. Arrastra un bloque **VirtOsc Connect** y un bloque **VirtOsc Acquire**. Conecta los cables de ejecución y los identificadores de dispositivo.
4. Arrastra un bloque **XY Plot**. Conecta el arreglo de tiempo a **X** y la señal de voltaje a **Y**.
5. Haz clic derecho en el bloque **XY Plot** y elige **Pin to Dashboard**.
6. Presiona `D` en el teclado (o haz clic en el botón **Dashboard** en la barra superior) para abrir el panel de operación.
7. Haz clic en **Ejecutar Blueprint** (▶️ o `Ctrl+R`).
8. **Verificación**: ComfyLAB iniciará automáticamente el servidor de simulación en segundo plano. El Dashboard mostrará de inmediato la señal capturada en tiempo real. También puedes abrir el ejemplo **Bode Diagram Virtual** en **Menú Archivo > Cargar Ejemplo > Bode_Diagram_Virtual.json** para ver un barrido automatizado con gráficos de Bode completos.

<div style="page-break-before: always; break-before: page;"></div>

---

## 7. Guía Rápida de Atajos y Referencia de Teclado

### Atajos de Teclado

| Acción | Atajo | Descripción |
| :--- | :--- | :--- |
| **Alternar Dashboard** | `D` | Abrir o cerrar el panel dedicado del Dashboard del Operador. |
| **Ejecutar / Pausar / Reanudar** | `Ctrl + R` | Iniciar la ejecución del blueprint, pausarla o reanudarla. |
| **Detener Ejecución** | `Ctrl + Shift + R` | Interrumpir la ejecución de inmediato y ejecutar rutinas de seguridad. |
| **Duplicar Bloque(s)** | `Ctrl + D` | Duplicar los bloques seleccionados manteniendo su configuración. |
| **Herramienta Selección** | `1` | Modo estándar para seleccionar, mover bloques y conectar pines. |
| **Herramienta Desplazamiento (Pan)** | `2` | Mover la vista del lienzo sin arrastrar bloques. |
| **Herramienta Cortar Cable** | `3` | Pasar la cuchilla para borrar cables rápidamente. |
| **Herramienta Pizarra** | `4` | Alternar la capa de dibujo para notas, figuras y anotaciones. |
| **Desplazar Lienzo** | `Espacio` + Arrastrar | Mantener presionada la barra espaciadora y arrastrar el fondo. |
| **Zoom en Lienzo** | `Rueda del Ratón` | Girar la rueda para acercar o alejar la vista. |
| **Guardar Blueprint** | `Ctrl + S` | Guardar el plano actual en el JSON del workspace (`Ctrl + Shift + S` para Guardar Como). |
| **Abrir Blueprint** | `Ctrl + O` | Abrir la ventana de diálogo para cargar un blueprint. |
| **Deshacer / Rehacer** | `Ctrl + Z` / `Ctrl + Y` | Deshacer o rehacer acciones recientes en el lienzo. |
| **Copiar / Pegar** | `Ctrl + C` / `Ctrl + V` | Copiar y pegar bloques seleccionados. |
| **Eliminar Bloque / Cable** | `Delete` o `Backspace` | Eliminar los bloques o cables seleccionados del lienzo. |
| **Navegar en Clúster** | `Doble Clic en Clúster` | Entrar al sub-lienzo interno del bloque Clúster. |

<div style="page-break-before: always; break-before: page;"></div>

---

## 8. Lista de Verificación para la Sesión de Laboratorio

Antes de comenzar tu sesión de práctica en el laboratorio, comprueba que:
* [ ] ComfyLAB esté instalado y se abra correctamente (`http://localhost:8000`).
* [ ] La carpeta del espacio de trabajo activo esté configurada.
* [ ] Los backends NI-VISA / PyVISA sean detectados si se realizarán pruebas con hardware real.
* [ ] Los Instrumentos Virtuales funcionen offline sin necesidad de hardware físico (`Bode_Diagram_Virtual.json`).
* [ ] El panel de Dashboard (`D`) haya sido probado para desplegar gráficos y controles en vivo.
* [ ] Los blueprints de ejemplo en `src/comfylab/examples` estén accesibles para demostración.

---
*ComfyLAB se distribuye bajo la Licencia Pública General GNU v3.0 (GPLv3). Desarrollado por Paulo Felipe Jarschel, GATE/EIT, IFGW, Unicamp.*
