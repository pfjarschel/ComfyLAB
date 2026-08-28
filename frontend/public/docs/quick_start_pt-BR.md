# ComfyLAB: Guia de Início Rápido e Visão Geral Completa
*Comfortable Lab Automation Blocks — Manual do Usuário, Visão Geral do Software e Referência de Tutoriais Práticos*

---

## 1. Introdução e Filosofia

### 1.1 O que é o ComfyLAB?
O **ComfyLAB** (**Comf**ortable **L**ab **A**utomation **B**locks) é uma plataforma de programação visual de código aberto, projetada especificamente para automação de experimentos científicos, teste e medição, aquisição de dados (DAQ) e visualização em tempo real.

Em laboratórios de pesquisa modernos, sistemas de medição automatizados frequentemente exigem comunicação com diversos equipamentos (osciloscópios, fontes de alimentação, multímetros, geradores de funções, sensores customizados) por meio de múltiplos protocolos (VISA, SCPI, Serial RS-232/RS-485, Ethernet, bibliotecas nativas C/C++ DLLs). Escrever código de automação tradicional baseado em scripts geralmente resulta em códigos repetitivos (boilerplate) para gerenciamento de loops, segurança entre threads, tratamento de exceções, parsing de dados e renderização de interfaces gráficas.

O ComfyLAB resolve esse desafio fornecendo uma interface gráfica limpa e modular, onde os usuários arrastam **Blocos** funcionais para uma tela digital e os conectam através de **Fios** visuais.

---

### 1.2 Arquitetura Dupla: Interface Web UI + Motor de Execução Python
O ComfyLAB opera em um modelo cliente-servidor desacoplado:
<div style="page-break-before: always; break-before: page;"></div>

```
┌───────────────────────────────────────────────────┐
│                   INTERFACE WEB (FRONT-END)       │
│ - Canvas Web (React + XY Flow)                    │
│ - Posicionamento de Blocos e Conexão Drag-and-Drop│
│ - Gráficos Interativos e Exibição em Tempo Real   │
│ - Camada de Lousa Interativa (Whiteboard)         │
└────────────────────────┬──────────────────────────┘
                         │ WebSocket / API HTTP
┌────────────────────────▼──────────────────────────┐
│            SERVIDOR DE EXECUÇÃO (BACK-END)        │
│ - Motor Core Python + API (FastAPI)               │
│ - Executor de Máquina de Estados Híbrida Push/Pull│
│ - Drivers Hardware VISA e Gerenciador Serial Lock │
│ - Processamento de Sinais NumPy/SciPy e FFT       │
│ - Scripting Multilinguagem e Invocação DLL / SO   │
└───────────────────────────────────────────────────┘
```

* **Canvas Front-End**: Executa em navegadores web modernos (ou em builds de aplicativo desktop de arquivo único). Proporciona manipulação gráfica fluida, ferramentas de auto-layout, zoom/pan interativo em gráficos e anotações virtuais em lousa (camada de interação com o usuário).
* **Servidor Back-End**: Alimentado por Python e FastAPI. Gerencia bloqueios de hardware em tempo real, consultas VISA/SCPI, cálculos matriciais pesados, execução multi-thread, persistência de arquivos e ambientes virtuais Python (camada de processamento, orquestração de instrumentos e cálculos).

---

### 1.3 Segurança e Proteção Integradas

* **Proteção de Instrumentos e Rotinas de Segurança**: Equipamentos físicos de laboratório (lasers, fontes de alta tensão, fontes de sinal RF) exigem gerenciamento de segurança rigoroso. Se uma execução de medição encontrar um erro, for interrompida manualmente ou sofrer perda de conexão, o ComfyLAB executa automaticamente rotinas de desligamento seguro (shutdown hooks) para desativar saídas ativas e retornar os instrumentos a estados seguros.
* **Verificação de Segurança de Blueprints**: Ao abrir blueprints de fontes externas, o ComfyLAB realiza verificações de segurança para evitar a execução não autorizada de scripts, garantindo controle total e confirmação rápida ao usuário antes de rodar códigos customizados.
* **Acesso Remoto Seguro**: O ComfyLAB suporta operação remota segura via rede com autenticação por token, permitindo que pesquisadores monitorem e controlem com segurança experimentos rodando em computadores do laboratório a partir de estações de trabalho remotas. *(Nota: a criptografia na camada de transporte HTTPS está planejada para versões futuras).*

<div style="page-break-before: always; break-before: page;"></div>

---

## 2. Capacidades e Flexibilidade: O que Pode (ou Não) Ser Feito

O ComfyLAB foi desenvolvido do zero para oferecer extrema flexibilidade, sem restringir usuários avançados a modelos de interface rígidos.

### 2.1 O que Pode Ser Feito com o ComfyLAB

| Área de Recurso                                   | Capacidades e Extensibilidade                                                                                                                                                                                                                  |
| :------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Controle de Hardware Físico**                   | Suporte completo para **VISA** (GPIB, USB TMC, Ethernet/LXI, Serial RS-232/RS-485) e comandos padrão **SCPI**. Blocos de driver integrados para osciloscópios comerciais populares, multímetros, fontes de alimentação e geradores de funções. |
| **Invocação de Bibliotecas Nativas**              | Chamada direta de bibliotecas em C/C++ (`.dll` no Windows, `.so` no Linux/macOS) através de um **Editor de Assinaturas** interativo, sem escrever Ctypes em Python.                                                                            |
| **Scripts Customizados Multilinguagem**           | Criação de **Blocos de Script** em 9 linguagens: Python, Rust, JavaScript, TypeScript, Julia, R, Lua, Octave e Wolfram.                                                                                                                        |
| **Acesso ao Ecossistema Python**                  | Conexão de blocos de script a ambientes virtuais Python (`.venv`), para acesso a bibliotecas como `scipy`, `numpy`, `pandas`, `opencv`, `scikit-learn`, `matplotlib` e pacotes PyPI.                                                           |
| **Publicação de Blocos e Pacotes (.cfy)**         | Publicação de blocos de script diretamente na paleta da barra lateral ou empacotamento de fluxos completos (blueprints, scripts e arquivos) em pacotes redistribuíveis `.cfy`.                                                                 |
| **Processamento Avançado de Sinais e Matemática** | Operações matriciais NumPy, análise espectral FFT, ajuste de curvas (Gaussiana, Exponencial, Polinomial, Não-linear customizada), filtragem (passa-baixas, passa-altas, passa-faixa), remoção de tendência (detrend) e detecção de picos.      |
| **Visualização Rica e Exportação de Dados**       | Gráficos interativos (traço único/múltiplo, eixos log/linear), visualizadores de imagem matricial 2D, exibições em tabela e exportação automática de dados para formatos CSV, JSON e Apache Parquet.                                           |
| **Sub-Canvases Modulares (Clusters)**             | Agrupamento de sub-grafos complexos em **Blocos de Cluster** com pinos de entrada e saída dinâmicos para manter diagramas de blueprint limpos e hierárquicos.                                                                                  |
| **Camada de Lousa Interativa (Whiteboard)**       | Adição de notas, texto formatado, formas geométricas, setas e desenhos livres diretamente sobre o canvas para apresentação e documentação. Uso de formas para agrupar blocos visualmente dentro de retângulos.                                 |

---

### 2.2 Limitações Realistas: O que Não Pode (ou Não Deve) Ser Feito

Embora o ComfyLAB suporte quase qualquer tarefa de medição científica, automação e processamento de dados, é importante compreender seus limites de aplicação:

* **Determinismo de Tempo Real Estrito em Microsegundos**: O ComfyLAB executa sobre sistemas operacionais convencionais (Windows/Linux/macOS) através de back-ends em Python/FastAPI. Ele é projetado para loops de automação na escala de milissegundos a sub-segundos, amostragem de sensores e controle de instrumentos. Ele **não** se destina a lógicas de hardware bare-metal em FPGA ou loops de controle determinísticos de microsegundos em tempo real (ex.: comutação PWM de drivers de motor a 100 kHz). Para essas tarefas, placas FPGA ou microcontroladores dedicados com RTOS devem gerenciar a temporização de baixo nível, enquanto o ComfyLAB se comunica com eles via serial/USB para controle de alto nível, armazenamento em buffer e plotagem.

> **Resumo**: Fora o determinismo de hardware em microsegundos via FPGA, **praticamente qualquer fluxo de medição científica, automação de laboratório, registro de dados, análise de sinais ou plotagem pode ser construído no ComfyLAB**.

<div style="page-break-before: always; break-before: page;"></div>

---

## 3. Comparação com Paradigmas Alternativos

Compreender como o ComfyLAB se compara às ferramentas tradicionais de laboratório destaca por que ele é uma escolha vantajosa tanto para o ensino quanto para a pesquisa.

| Recurso / Aspecto                      | Scripts Python Puros (PyVISA, Matplotlib) | National Instruments LabVIEW                     | MATLAB / Simulink                  | **ComfyLAB**                                   |
| :------------------------------------- | :---------------------------------------- | :----------------------------------------------- | :--------------------------------- | :--------------------------------------------- |
| **Licenciamento e Custo**              | Gratuito e Código Aberto                  | Licenciamento Comercial Elevado                  | Licenciamento Comercial Elevado    | **Gratuito e Código Aberto (GPLv3)**           |
| **Paradigma de Programação**           | Código Baseado em Texto                   | Código Gráfico Proprietário G                    | Diagrama de Blocos Gráfico / Texto | **Diagramas de Blocos Web + Código**           |
| **Curva de Aprendizado**               | Alta (Exige fluência em programação)      | Média (Convenções complexas da linguagem G)      | Média (Exige sintaxe e toolboxes)  | **Baixa (Canvas intuitivo drag-and-drop)**     |
| **Configuração de GUI e Gráficos**     | Manual (PyQt, Tkinter, Matplotlib)        | Painel Frontal Integrado                         | Janelas de Figura Integradas       | **Widgets Prontos de Plotagem e Visualização** |
| **Formato de Arquivo e Versionamento** | Texto puro `.py` (Amigável ao Git)        | Binário Proprietário `.vi` (Difícil diff no Git) | `.m` / Binário Proprietário `.slx` | **Blueprints JSON Limpos (OK com Git)**        |
| **Extensão com Código Customizado**    | Nativa                                    | Nós de Chamada Complexos C/Python                | Funções S / Código MATLAB          | **Blocos de Script**                           |
| **Arquitetura**                        | Script single-thread / threads manuais    | Aplicação Desktop Monolítica                     | Ambiente Desktop Pesado            | **Interface Web Desacoplada + Servidor**       |
| **Bloqueio de Hardware (Locking)**     | Exige implementação manual de lock        | Drivers Integrados VISA / DAQmx                  | VISA / Instrument Control Toolbox  | **Gerenciador de Lock VISA Automático**        |

### Principais Conclusões:
1. **Vs. Python Puro**: O Python é extremamente poderoso, mas criar interfaces de usuário, gráficos interativos em tempo real, loops de estado de hardware e fluxos visuais exige centenas de linhas de código repetitivo. O ComfyLAB mantém todo o poder analítico do Python, fornecendo uma interface visual imediata.
2. **Vs. LabVIEW**: O LabVIEW é amplamente utilizado, mas sofre com custos elevados de licença comercial, arquivos binários proprietários que dificultam o controle de versão e bloqueio do fornecedor (lock-in). O ComfyLAB oferece uma alternativa moderna e open-source com blueprints em JSON e integração nativa com navegadores web.
3. **Vs. MATLAB**: O MATLAB se destaca em cálculos matriciais, mas possui custos de licença elevados. O ComfyLAB utiliza back-ends gratuitos e de código aberto baseados em NumPy/SciPy.

<div style="page-break-before: always; break-before: page;"></div>

---

## 4. Layout da Interface e Conceitos Fundamentais

### 4.1 Visão Geral do Layout da Interface

A interface do usuário do ComfyLAB é composta por três zonas funcionais principais cercadas por controles superiores:

```
┌──────────────────────────────────────────────────────────────────┐
│ BARRA SUPERIOR: [🟰][⚙️] | [▶ Rodar/⏸ Pausar] [🛑 Parar] | [Tema]│
├────────────────┬──────────────────────────────────┬──────────────┤
│ BARRA LATERAL  │ ÁREA PRINCIPAL DO CANVAS         │ INSPETOR     │
│ (Paleta Blocos)│                                  │ (Valores)    │
│                │  ┌───────┐   Fio Execução        │              │
│ Buscar...      │  │ Entry │▶───┐                  │ Entradas     │
│ Controle Fluxo │  └───────┘    │                  │ Dados ao Vivo│
│ Matemática     │            ┌──▼────────────┐     │ Logs Console │
│ Hardware VISA  │ Fio Dados  │ Bloco Math    │     │              │
│ Instrumentos   │ ──────────▶└───────────────┘     │              │
│ Visualização   │                                  │              │
│                │ [Minimap]        [Tools 1-4]     │              │
└────────────────┴──────────────────────────────────┴──────────────┘
```

#### Descrição Detalhada da Interface:
* **Barra de Ferramentas Superior**: Controles para executar (▶️), pausar (⏸️) e parar (🛑) blueprints, criar/salvar arquivos de workspace (`Ctrl+S`), alternar temas de cores e configurar opções globais do VISA.
* **Barra Lateral (Esquerda)**: Paleta pesquisável contendo todos os blocos nativos disponíveis, blocos customizados publicados e nós de script categorizados por domínio.
* **Canvas Principal (Centro)**: Área de trabalho visual infinita com zoom e pan onde você arrasta, posiciona e conecta os blocos funcionais.
* **Inspetor de Blocos (Direita)**: Painel de detalhes contextual que se abre ao selecionar um bloco. Exibe valores de pinos ao vivo, parâmetros do bloco, documentação resumida e logs de console de execução.
* **Barra de Abas e Breadcrumbs**: Navegação entre múltiplos arquivos de blueprint abertos e detalhamento (drill down) em clusters de sub-canvas.

<div style="page-break-before: always; break-before: page;"></div>
---

### 4.2 Pinos e Conexões: Fluxo de Execução vs. Valores de Dados

As conexões entre blocos no ComfyLAB são estritamente divididas em duas categorias distintas:

```
  Saída Exec  ▶══════════════════════════════▶ Entrada Exec
              (Linha Violeta: Controla QUANDO os blocos rodam)

  Saída Dados ●──────────────────────────────● Entrada Dados
              (Linha Sólida: Transfere VALORES sob demanda)
```

1. **Pinos de Execução (Fluxo)**:
   * Representados por **conectores em forma de seta** e interligados por **linhas violetas (🟪)**.
   * Ditam o **sequenciamento temporal e fluxo de controle** (quando as etapas executam, loops repetem ou ramificações são acionadas).

2. **Pinos de Dados (Valores)**:
   * Representados por **pinos circulares coloridos** e interligados por **linhas coloridas sólidas**.
   * Transportam **valores** (números, strings de texto, vetores NumPy, dicionários, handles de hardware).
   * São avaliados de forma preguiçosa (lazy evaluation) sob demanda quando um bloco de execução solicita dados de entrada.

#### Referência de Cores dos Pinos de Dados:
* 🟧 **Número (Laranja)**: Valores numéricos escalares inteiros ou de ponto flutuante.
* 🟩 **Booleano (Verde)**: Flags lógicas `True` (Verdadeiro) ou `False` (Falso).
* 🟪 **String (Rosa)**: Textos, caracteres formatados ou comandos SCPI.
* 🟨 **Array (Amarelo)**: Vetores ou matrizes numéricas NumPy 1D/2D de alto desempenho.
* 🟦 **Lista (Ciano)**: Coleções ordenadas de elementos.
* 🟫 **Dicionário (Marrom)**: Mapeamentos de parâmetros chave-valor.

---

### 4.3 Lógica de Execução e Cadeias Independentes
* **Gatilho de Execução**: Clicar em **Run Blueprint** (▶️) inicia a execução nos blocos de entrada (blocos sem conexões de execução de entrada) e segue os fios de execução fluxo abaixo.
* **Cadeias de Execução Independentes**: Se o canvas contiver grupos de blocos separados e não conectados entre si, o ComfyLAB os trata automaticamente como cadeias de execução paralelas, permitindo que loops de aquisição independentes rodem concorrentemente.
* **Blocos de Controle de Fluxo**:
  * **For Loop**: Executa um sub-loop por uma quantidade fixa de iterações, emitindo o índice atual, a porcentagem de conclusão e a estimativa de tempo restante (ETR).
  * **For Each Loop**: Itera sobre cada item em uma lista ou array, fornecendo saídas de item, índice, porcentagem e tempo restante (ETR).
  * **While Loop**: Executa continuamente um sub-loop enquanto a condição Booleana do pino permanecer `True`.
  * **If / Else Branch**: Direciona o fluxo de execução para uma saída `True` ou `False` com base em uma condição.
  * **Delay / Sleep**: Pausa o fluxo de execução por uma duração especificada (ms ou segundos).
  * **Countdown Wait**: Pausa a execução com relógio regressivo digital em tempo real, barra de progresso e botão para pular a espera.
  * **Barra de Progresso & Relógio ETR**: Displays visuais para acompanhamento de porcentagem ao vivo, tempo restante e relógio estilo sala de controle.

---

### 4.4 Recursos Avançados

* **Blocos Persistentes (📌)**: Por padrão, os estados dos blocos são reiniciados a cada execução. Marcar um bloco como **Persistente** preserva seu estado interno e handles de hardware (ex.: conexões VISA ativas, portas seriais abertas ou médias móveis) entre múltiplas execuções do blueprint.
* **Desativação de Blocos (🚫)**: Clicar com o botão direito em um bloco para desativá-lo o deixa opaco no canvas. Blocos desativados são ignorados durante a execução, repassando dados de forma limpa sem executar código—ideal para testar fluxos sem hardware físico.
* **Clusters (Sub-canvases 📦)**: Agrupamento de arranjos complexos de blocos em um único bloco customizado. Dar um duplo clique em um bloco de cluster abre um sub-canvas isolado, com breadcrumbs na barra superior para navegação.
* **Modo Lousa / Whiteboard (🎨)**: Clique no ícone de ferramenta ou pressione o atalho `4` para alternar o modo de desenho, permitindo adicionar notas adesivas, caixas de texto e formas geométricas diretamente sobre o canvas.

<div style="page-break-before: always; break-before: page;"></div>

---

## 5. Resumo das Categorias de Blocos Nativos

| Categoria | Descrição e Blocos Comuns |
| :--- | :--- |
| 🔄 **Controle de Fluxo** | For Loop, While Loop, Ramificação If/Else, Delay/Sleep, Parar Execução. |
| 🔢 **Matemática e Lógica** | Adição, Subtração, Multiplicação, Divisão, Evaluator de Fórmulas, Seno/Cosseno, Trigonometria, Exponencial, Logaritmo, Comparações (`>`, `<`, `==`), Lógica AND, OR, NOT. |
| 📝 **Dados e Strings** | Concatenação de Strings, Formatador de Texto, Busca Regex, Divisor de Texto, Construtor de Listas, Indexador de Listas, Construtor de Dicionários, Obter Chave-Valor. |
| 📊 **Arrays e Sinais** | Criar Array, Linspace/Range, Fatiamento de Array (Slicing), Espectro de Potência FFT, Filtros Passa-Baixas/Passa-Faixa, Detrend, Estatísticas (Média, Desvio Padrão, Mín, Máx), Detector de Picos, Ajuste de Curvas (Gaussiana, Exponencial, Polinomial, Customizada). |
| 💾 **Entrada/Saída de Arquivos** | Leitura/Escrita de arquivos CSV, JSON, armazenamento Parquet, Leitura/Escrita de Texto Puro, Carregador e Salvador de Imagens. |
| 📡 **VISA e Hardware** | Abrir Recurso VISA, Escrita SCPI, Leitura SCPI, Consulta SCPI (Query), Fechar VISA, Abrir/Ler/Escrever Porta Serial. |
| 🔬 **Drivers de Instrumentos** | Configuração e Leitura de Osciloscópio, Leitura de Multímetro Digital (DMM), Configuração/Leitura de Fonte DC, Gerador de Funções, entre outros. |
| 📈 **Exibição e UI** | Plotter de Linhas Interativo (Traço Único/Múltiplo, Eixos Log/Linear), Visualizador de Matriz de Imagem 2D, Tabela de Dados, Mostrador Digital (Gauge), Indicador de Status. |
| ⚙️ **Nativo e Scripts** | Invocação de Biblioteca Nativa (DLL/SO), Nó Script Poliglota (Python, JS, Julia, Rust, etc.). |

<div style="page-break-before: always; break-before: page;"></div>

---

## 6. Tutoriais Práticos Iniciais

### Tutorial 1: Fluxo Matemático e Inspeção ao Vivo
**Objetivo**: Criar dois números, multiplicá-los, aplicar uma fórmula matemática e inspecionar o resultado no Inspetor de Blocos.

```
┌──────────────┐
│ Número (5.0) ├──┐   ┌────────────┐   ┌─────────────┐
└──────────────┘  ├──▶│ Multiplica ├──▶│ Fórmula     ├──► Saída
┌──────────────┐  │   └────────────┘   │ "x^2 + 10"  │
│ Número (3.0) ├──┘                    └─────────────┘
└──────────────┘
```

#### Instruções Passo a Passo:
1. Abra o ComfyLAB e crie um novo workspace/blueprint.
2. Na **Barra Lateral** esquerda, busque por `Number` (Número) e arraste **dois** blocos Número para a tela (canvas).
3. Defina o valor do primeiro bloco para `5.0` e do segundo para `3.0`.
4. Arraste um bloco **Multiply** (Multiplicar - em *Matemática e Lógica*) para a tela.
5. Conecte o pino de saída de dados do Número 1 à Entrada A do bloco Multiplicar, e o Número 2 à Entrada B.
6. Arraste um bloco **Formula** (Fórmula) para a tela. Defina seu parâmetro de equação como `x^2 + 10`.
7. Conecte o pino de saída do bloco Multiplicar (`15.0`) à entrada `x` do bloco Fórmula.
8. Clique em **Rodar Blueprint** (▶️) na barra de ferramentas superior.
9. Clique no bloco **Fórmula** para abrir o **Inspetor de Blocos** na barra lateral direita.
10. **Verificação**: No Inspetor de Blocos, verifique o valor atual no pino de saída. Ele deve calcular `(15)^2 + 10 = 235.0`.

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 2: Geração de Sinal Sintético e Gráfico ao Vivo
**Objetivo**: Gerar um vetor de onda senoidal com ruído, calcular seu espectro de potência FFT e renderizar em um plotador interativo.

```
┌────────────────────┐     ┌────────────────────┐
│ Linspace (0 a 10s) ├────▶│ Gerador de Seno    ├─┐
└────────────────────┘     └────────────────────┘ │
                                                  ▼
┌────────────────────┐     ┌────────────────────┐ │
│ Gráfico Interativo │◀────┤ Sinal + Ruído      │◀┘
└────────────────────┘     └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ Espectro FFT       │
                           └────────────────────┘
```

#### Instruções Passo a Passo:
1. Busque por `Linspace` na Barra Lateral. Defina `Start = 0`, `Stop = 10`, `Points = 1000` para criar um vetor de tempo.
2. Busque por `Sine` (Seno - em *Matemática* ou *Vetores*). Conecte a saída do Linspace à entrada de tempo do bloco Sine. Defina a frequência para `5.0 Hz`.
3. Adicione um bloco de **Ruído Aleatório** e um bloco de **Adição** para corromper a onda senoidal com ruído branco (`Sinal + Ruído`).
4. Arraste um bloco **Plotador Interativo** para a tela.
5. Conecte o vetor de tempo ao **Pino X** do Plotador e o sinal com ruído ao **Pino Y**.
6. (Opcional) Conecte o sinal ruidoso a um bloco **Espectro FFT**, e conecte a saída do FFT a um segundo traço no Plotador.
7. Clique em **Rodar Blueprint** (▶️).
8. **Verificação**: O widget do Plotador na sua tela exibirá imediatamente a onda senoidal com ruído ao vivo. Use a roda do mouse sobre o gráfico para aplicar zoom e arraste para navegar pelos eixos!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 3: Varredura Automática de Parâmetros e Registro CSV
**Objetivo**: Usar um `For Loop` para simular a varredura de tensão de uma fonte de alimentação, calcular o consumo de energia, exibir a curva ao vivo e registrar os dados em um arquivo CSV.

```
┌─────────────────────┐    ┌────────────────────┐
│ For Loop (0 a 50)   │▶──▶│ Escritor CSV       │
└──────────┬──────────┘    └────────────────────┘
           │ (Índice)
           ▼
┌─────────────────────┐
│ Tensão = Índice*0.1 │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Corrente = V / R    ├─► Plotador ao Vivo
└─────────────────────┘
```

#### Instruções Passo a Passo:
1. Arraste um bloco **For Loop** (Laço For) para a tela. 
2. Defina a contagem de iterações do `For Loop` como `50`.
3. Dentro do caminho de execução do laço, multiplique o pino `Índice de Iteração` por `0.1` usando um bloco **Multiply** (Multiplicar) para gerar uma varredura de tensão de `0.0 V` a `5.0 V`.
4. Divida a tensão por uma resistência constante (`R = 100 Ohms`) usando um bloco **Divide** (Dividir) para calcular a corrente `I`.
5. Conecte os valores de Tensão e Corrente a um bloco **CSV Writer** (Escritor CSV). Defina o nome do arquivo como `sweep_results.csv`.
6. Conecte o pino de execução de saída do bloco CSV de volta à entrada de iteração do laço para completar o ciclo.
7. Clique em **Rodar Blueprint** (▶️).
8. **Verificação**: Assista o laço rodar passo a passo com linhas de execução violeta animadas. Após a execução ser concluída, abra a pasta do seu workspace ativo — você encontrará o arquivo `sweep_results.csv` preenchido com todas as 50 linhas de dados!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 4: Escrevendo e Publicando um Bloco Script Python Customizado
**Objetivo**: Criar um bloco customizado de script Python que filtre valores abaixo de um limite, testá-lo e publicá-lo na paleta da barra lateral esquerda.

```
┌──────────────────────────────────────────────────┐
│ Bloco Script Customizado (Python)                │
│ Entradas: data_in (Vetor), threshold (Número)    │
│ Saídas:   filtered_data (Vetor), count (Número)  │
├──────────────────────────────────────────────────┤
│ arr = np.array(inputs['data_in'])                │
│ result = arr[arr > inputs['threshold']]          │
│ outputs['filtered_data'] = result.tolist()       │
│ outputs['count'] = len(result)                   │
└──────────────────────────────────────────────────┘
```

#### Instruções Passo a Passo:
1. Arraste um **Script Block** (de *Scripts & Nativo*) para a tela. Selecione **Python** como a linguagem.
2. No **Inspetor de Blocos**, clique em **Editar Pinos**:
   * Adicionar Pino de Entrada: `data_in` (Tipo: Vetor)
   * Adicionar Pino de Entrada: `threshold` (Tipo: Número)
   * Adicionar Pino de Saída: `filtered_data` (Tipo: Vetor)
   * Adicionar Pino de Saída: `count_passed` (Tipo: Número)
3. Clique duas vezes no Script Block para abrir o editor de código embutido.
4. Digite o código Python mostrado acima.
5. Conecte um vetor de amostra em `data_in` e defina `threshold = 2.5`.
6. Clique em **Rodar Blueprint** (▶️) e inspecione `filtered_data` e `count_passed` no Inspetor de Blocos.
7. Após verificar o funcionamento, clique em **Publicar Bloco** no Inspetor de Blocos. Nomeie-o como `Filtro de Limite`, escolha um ícone e atribua-o à categoria `Vetores`.
8. **Verificação**: Olhe na paleta da **Barra Lateral** esquerda. Seu recém-criado bloco `Filtro de Limite` estará permanentemente disponível para arrastar para qualquer tela no seu workspace!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 5: Interface de Hardware VISA (Consulta de Identificação SCPI)
**Objetivo**: Conectar a um instrumento físico ou simulado via VISA, enviar uma consulta SCPI `*IDN?` e exibir o modelo do instrumento respondido.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ VISA Abrir  │▶─▶│ Consulta SCPI▶─▶│ VISA Fechar │
│ Recurso     ├─▶ │ "*IDN?"     ├─▶ │ Identificador│
└─────────────┘   └──────┬──────┘   └─────────────┘
                         │ String de Resposta
                         ▼
                  [Inspetor de Blocos]
```

#### Instruções Passo a Passo:
1. Arraste um bloco **VISA Open** para a tela. Defina o parâmetro de String de Recurso para o endereço do seu instrumento (ex: `TCPIP0::192.168.1.100::INSTR`, `GPIB0::14::INSTR`, ou `COM3`).
2. Arraste um bloco **SCPI Query**. Conecte a saída de execução (`ExecOut`) do VISA Open à entrada (`ExecIn`) da Consulta SCPI.
3. Conecte o pino de saída `Handle VISA` (pino ciano) do VISA Open à entrada `Handle VISA` da Consulta SCPI.
4. Defina o parâmetro de string de comando na Consulta SCPI como `*IDN?\n`.
5. Arraste um bloco **VISA Close** e conecte a linha de execução e o handle VISA a ele para garantir a liberação limpa do recurso.
6. Clique em **Rodar Blueprint** (▶️).
7. **Verificação**: Clique no bloco **SCPI Query** e olhe o Inspetor de Blocos. O pino de saída de string exibirá a identificação do fabricante (ex., `HEWLETT-PACKARD,34401A,0,11-5-2` ou `KEYSIGHT TECHNOLOGIES,DSOX2002A,...`).
8. **Dica**: Você também pode utilizar o bloco Gerenciador de Recursos VISA para descobrir instrumentos conectados automaticamente!
