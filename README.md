# TrabalhoSO

# 🚀 Simulador de Escalonamento de SO

[cite_start]Este projeto é um simulador de algoritmos de escalonamento de processos (FIFO, SJF, RR, EDF, CFS) [cite: 8-14] desenvolvido para a disciplina de Sistemas Operacionais.

[cite_start]O objetivo é carregar processos a partir de um arquivo de entrada (JSON) [cite: 112-122][cite_start], executar a simulação e gerar como saída um Gráfico de Gantt [cite: 47] [cite_start]e métricas de desempenho[cite: 53, 54].

## 🔧 Setup do Ambiente

Siga estes passos para configurar seu ambiente de desenvolvimento local.

# 1. Clonar o Repositório\*\*

git clone [https://github.com/guneves/TrabalhoSO.git](https://github.com/guneves/TrabalhoSO.git)
cd TrabalhoSO

## Comando para macOS/Linux

python3 -m venv .venv

## Ativar no macOS/Linux

source .venv/bin/activate

### --- ou ---

## Comando para Windows (PowerShell)

python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Criar e Ativar o Ambiente Virtual (venv)

Recomendamos usar o nome .venv para que o .gitignore o ignore automaticamente.

## Comando para macOS/Linux

python3 -m venv .venv

## Ativar no macOS/Linux

source .venv/bin/activate

### --- ou ---

## Comando para Windows (PowerShell)

python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar as Dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias:

Bash

pip install -r requirements.txt
Pronto! Agora você pode executar o projeto.

# 🏃 Como Executar

O main.py é o ponto de entrada. Você deve especificar o algoritmo e o arquivo de entrada.

Bash

# Exemplo de execução

python main.py --algoritmo SJF --input casos/caso_base.json
