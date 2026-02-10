import cv2
import mediapipe as mp
import socket
import time

# --- CONFIGURAÇÕES DE REDE ---
# Como o ESP32 agora é o Roteador (AP), o IP padrão dele é este:
ROBOT_IP = "192.168.4.1" 
ROBOT_PORT = 4210

# Configuração do UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.1)

def enviar_comando(cmd):
    try:
        sock.sendto(cmd.encode(), (ROBOT_IP, ROBOT_PORT))
    except Exception as e:
        print(f"Erro ao enviar UDP: {e}")

# --- CONFIGURAÇÃO MEDIAPIPE (Mãos) ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

def contar_dedos(hand_landmarks):
    fingers = []
    
    # 1. Polegar (Lógica para eixo X - Mão Direita)
    # Nota: Se estiver usando mão esquerda, a lógica do polegar inverte
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # 2. Outros 4 dedos (Eixo Y - Ponta acima da dobradiça)
    tips_ids = [8, 12, 16, 20]
    pip_ids = [6, 10, 14, 18]

    for i in range(4):
        if hand_landmarks.landmark[tips_ids[i]].y < hand_landmarks.landmark[pip_ids[i]].y:
            fingers.append(1)
        else:
            fingers.append(0)
            
    return fingers

# --- INICIALIZAÇÃO DA WEBCAM ---
print("Iniciando Webcam do PC...")
# O índice 0 geralmente é a webcam integrada. Se tiver erro, tente 1.
cap = cv2.VideoCapture(0)

# Define tamanho para processar mais rápido (opcional)
cap.set(3, 640)
cap.set(4, 480)

ultimo_comando = "" 

print(f"Conectado. Enviando comandos para {ROBOT_IP}:{ROBOT_PORT}")

while True:
    success, img = cap.read()
    
    if not success:
        print("Falha ao ler a câmera (verifique se outra app está usando).")
        break

    # Espelha a imagem (fica mais natural para controlar)
    img = cv2.flip(img, 1)
    
    # Converte para RGB (MediaPipe usa RGB, OpenCV usa BGR)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    comando_atual = "P" # Padrão é Parar
    texto_tela = "PARADO"
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Conta quais dedos estão levantados
            fingers_up = contar_dedos(hand_landmarks)
            
            # --- LÓGICA DE COMANDOS ---
            # Dedos: [Polegar, Indicador, Meio, Anelar, Mindinho]
            
            # Indicador (FRENTE)
            if fingers_up == [0, 1, 0, 0, 0] or fingers_up == [1, 1, 0, 0, 0]:
                comando_atual = "F"
                texto_tela = "FRENTE"
            
            # Mindinho (ESQUERDA)
            elif fingers_up == [0, 0, 0, 0, 1] or fingers_up == [1, 0, 0, 0, 1]:
                comando_atual = "E"
                texto_tela = "ESQUERDA"
            
            # Polegar (DIREITA) -> Ajuste conforme sua preferência
            elif fingers_up == [1, 0, 0, 0, 0]:
                comando_atual = "D"
                texto_tela = "DIREITA"
            
            # Mão aberta (PARAR - opcional, ou usar como ré)
            elif fingers_up == [1, 1, 1, 1, 1]:
                comando_atual = "P"
                texto_tela = "PARAR"

    # Envia o comando apenas se mudou (para não inundar a rede)
    if comando_atual != ultimo_comando:
        enviar_comando(comando_atual)
        ultimo_comando = comando_atual
        print(f"Enviando: {texto_tela} ({comando_atual})")

    # --- INTERFACE VISUAL ---
    cor = (0, 255, 0) if texto_tela != "PARADO" else (0, 0, 255)
    
    # Desenha retângulo e texto
    cv2.rectangle(img, (20, 20), (350, 100), cor, -1)
    cv2.putText(img, f"CMD: {texto_tela}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 
                1.5, (255, 255, 255), 3)

    cv2.imshow("Controle Vespa - Webcam", img)

    # Pressione 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        enviar_comando("P") # Garante que o robô pare ao fechar
        break

cap.release()
cv2.destroyAllWindows()
sock.close()