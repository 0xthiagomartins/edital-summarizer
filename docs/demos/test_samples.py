from edital_summarizer import process_edital
import json
import os

def test_edital(edital_path: str, target: str, threshold: int = 500, output_file: str = "llmResponse.json"):
    """
    Testa um edital com os parâmetros especificados.
    
    Args:
        edital_path: Caminho para o edital
        target: Target para análise
        threshold: Threshold mínimo para dispositivos
        output_file: Arquivo de saída
    """
    print(f"\n=== Testando edital: {edital_path} ===")
    print(f"Target: {target}")
    print(f"Threshold: {threshold}")
    
    # Processa o edital
    result = process_edital(
        document_path=edital_path,
        target=target,
        threshold=threshold,
        verbose=True
    )
    
    # Salva o resultado
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nResultado salvo em: {output_file}")
    print("=== Fim do teste ===\n")

def main():
    # Diretório base dos editais
    base_dir = "samples"
    
    # Lista de editais para testar
    editais = [
        "edital-004",
        "edital-005",
        "edital-006"
    ]
    
    # Parâmetros de teste
    target = ""  # Target vazio conforme solicitado
    threshold = 500
    
    # Testa cada edital
    for edital in editais:
        edital_path = os.path.join(base_dir, edital)
        output_file = f"llmResponse_{edital}.json"
        test_edital(edital_path, target, threshold, output_file)

if __name__ == "__main__":
    main() 