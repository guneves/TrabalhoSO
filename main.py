import argparse
import json
import sys
import os
from typing import Dict, Any, List

# --- Importação dos Módulos do Projeto ---
# (Assumindo que 'main.py' está na raiz e 'src' é um pacote)

try:
    from src.processo import Processo
    from src.simulador import Simulador
    from src.escalonadores import (
        EscalonadorFIFO,
        EscalonadorSJF,
        EscalonadorRoundRobin,
        EscalonadorEDF,
        EscalonadorCFSSim
    )
    # TODO: Crie estes arquivos/funções
    from src.visualizacao import gerar_gantt
    from src.metricas import imprimir_tabela_final, imprimir_resumo_quantitativo

except ImportError as e:
    print(f"Erro ao importar módulos: {e}", file=sys.stderr)
    print("Verifique se 'main.py' está no diretório raiz e se 'src/__init__.py' existe.", file=sys.stderr)
    sys.exit(1)

def carregar_config(caminho_arquivo: str) -> Dict[str, Any]:
    """Carrega o arquivo JSON de configuração."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validação básica
        if 'processos' not in config or 'sobrecarga_contexto' not in config:
            raise ValueError("Arquivo JSON deve conter 'processos' e 'sobrecarga_contexto'.")
            
        return config
    except FileNotFoundError:
        print(f"Erro: Arquivo de entrada não encontrado: {caminho_arquivo}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Arquivo JSON mal formatado: {caminho_arquivo}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Erro no JSON: {e}", file=sys.stderr)
        sys.exit(1)


def criar_escalonador(algoritmo: str, quantum: int, config: Dict[str, Any]) -> Any:
    """Factory para criar a instância do escalonador correto."""
    
    algoritmos_map = {
        "FIFO": EscalonadorFIFO,
        "SJF": EscalonadorSJF,
        "RR": EscalonadorRoundRobin,
        "EDF": EscalonadorEDF,
        "CFS": EscalonadorCFSSim
    }

    if algoritmo not in algoritmos_map:
        print(f"Erro: Algoritmo '{algoritmo}' não reconhecido.", file=sys.stderr)
        print(f"Opções válidas: {list(algoritmos_map.keys())}", file=sys.stderr)
        sys.exit(1)

    # Lida com o caso especial do Round-Robin que precisa do quantum
    if algoritmo == "RR":
        if 'quantum' not in config:
            print("Erro: 'quantum' não definido no JSON (necessário para RR).", file=sys.stderr)
            sys.exit(1)
        return EscalonadorRoundRobin(quantum=config['quantum'])
    else:
        return algoritmos_map[algoritmo]()


def main():
    """Função principal: Parseia args, carrega dados, roda a simulação e gera saídas."""
    
    # 1. Configurar o Parser de Argumentos
    parser = argparse.ArgumentParser(description="Simulador de Escalonamento de Processos SO.")
    parser.add_argument("--alg", 
                        type=str, 
                        required=True, 
                        choices=['FIFO', 'SJF', 'RR', 'EDF', 'CFS'],
                        help="Algoritmo de escalonamento a ser usado.")
    parser.add_argument("--input", 
                        type=str, 
                        required=True, 
                        help="Caminho para o arquivo .json de entrada.")
    parser.add_argument("--gantt", 
                        type=str, 
                        help="Caminho para salvar o gráfico de Gantt (ex: out/saida.png)")
    parser.add_argument("--log", 
                        type=str, 
                        help="Caminho para salvar o log de saída (opcional).")

    args = parser.parse_args()

    # 2. Carregar Configuração e Processos
    print(f"Carregando configuração de: {args.input}")
    config = carregar_config(args.input)
    
    # Cria a lista de objetos Processo a partir dos dados do JSON
    try:
        lista_processos = [Processo(**p) for p in config['processos']]
    except TypeError as e:
        print(f"Erro ao criar processos: {e}", file=sys.stderr)
        print("Verifique se as chaves do JSON batem com os atributos da classe 'Processo'.", file=sys.stderr)
        sys.exit(1)

    # 3. Criar o Escalonador (Strategy)
    escalonador = criar_escalonador(args.alg, config.get('quantum'))
    
    # 4. Instanciar e Executar o Simulador
    print(f"Iniciando simulação com o algoritmo: {args.alg}")
    
    simulador = Simulador(
        processos=lista_processos,
        escalonador=escalonador,
        sobrecarga_contexto=config['sobrecarga_contexto']
    )
    
    # O método 'executar()' deve retornar tudo que precisamos para as saídas
    # (Esta é uma sugestão de estrutura de retorno)
    resultados = simulador.executar()
    
    print("Simulação concluída.")

    # 5. Gerar Saídas
    
    # Saída 1: Tabela final e Resumo (Console)
    print("\n--- Tabela Final de Processos ---")
    imprimir_tabela_final(resultados['processos_terminados'])
    
    print("\n--- Resumo Quantitativo ---")
    imprimir_resumo_quantitativo(
        resultados['metricas_globais'], 
        resultados['processos_terminados']
    )

    # Saída 2: Gráfico de Gantt (Arquivo)
    if args.gantt:
        print(f"Gerando gráfico de Gantt em: {args.gantt}")
        # Garante que o diretório de saída exista
        os.makedirs(os.path.dirname(args.gantt), exist_ok=True)
        
        gerar_gantt(
            log_execucao=resultados['log_gantt'],
            processos_originais=config['processos'], # Para plotar deadlines
            caminho_saida=args.gantt,
            algoritmo_nome=args.alg
        )
        print("Gráfico gerado.")

    # Saída 3: Arquivo de Log (Opcional)
    # (Pode ser uma cópia do console ou um dump JSON dos resultados)
    if args.log:
        print(f"Salvando log em: {args.log}")
        os.makedirs(os.path.dirname(args.log), exist_ok=True)
        try:
            with open(args.log, 'w', encoding='utf-8') as f:
                # Por simplicidade, vamos salvar o JSON dos resultados
                json.dump(resultados, f, indent=2, default=str) # 'default=str' ajuda a serializar
        except Exception as e:
            print(f"Não foi possível escrever o log: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()