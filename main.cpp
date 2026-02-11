#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// --- CONFIGURAÇÕES DA NOVA REDE DO ROBÔ ---
const char *ssid = "ROBOCAMP";       // Nome da rede que o robô vai criar
const char *password = "@Marcelo2025"; // Senha da rede (mínimo 8 caracteres)

WiFiUDP udp;
const int localPort = 4210;
char packetBuffer[255];

// --- PINOS & LED ---
const int PIN_LED_DEBUG = 15;

// Motor Esquerdo
const int PIN_M1_MORTO = 13; 
const int PIN_M1_VIVO = 14; 
// Motor Direito
const int PIN_M2_FRENTE = 4;
const int PIN_M2_RE = 27;

// Canais PWM
const int CH_M1_MORTO = 0; const int CH_M1_VIVO = 1;
const int CH_M2_FRENTE = 2; const int CH_M2_RE = 3;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_DEBUG, OUTPUT);
  digitalWrite(PIN_LED_DEBUG, LOW);

  // PWM Setup
  ledcSetup(CH_M1_MORTO, 5000, 8); ledcAttachPin(PIN_M1_MORTO, CH_M1_MORTO);
  ledcSetup(CH_M1_VIVO, 5000, 8);  ledcAttachPin(PIN_M1_VIVO, CH_M1_VIVO);
  ledcSetup(CH_M2_FRENTE, 5000, 8); ledcAttachPin(PIN_M2_FRENTE, CH_M2_FRENTE);
  ledcSetup(CH_M2_RE, 5000, 8);     ledcAttachPin(PIN_M2_RE, CH_M2_RE);

  // --- CONFIGURAÇÃO DO ACCESS POINT (Cria a rede) ---
  Serial.println("Criando rede Wi-Fi do Robô...");
  
  // Inicia o modo Access Point
  WiFi.softAP(ssid, password);

  Serial.println("\n=== REDE CRIADA COM SUCESSO! ===");
  Serial.print("Nome da Rede (SSID): ");
  Serial.println(ssid);
  Serial.print("IP para conectar no App: ");
  // Atenção: O IP geralmente é 192.168.4.1
  Serial.println(WiFi.softAPIP()); 
  Serial.println("================================");
  
  udp.begin(localPort);
  
  // Pisca o LED para indicar que iniciou
  for(int i=0; i<5; i++) { 
    digitalWrite(PIN_LED_DEBUG, HIGH); delay(200); 
    digitalWrite(PIN_LED_DEBUG, LOW); delay(200); 
  }
}

void parar() {
  ledcWrite(CH_M1_VIVO, 0); ledcWrite(CH_M1_MORTO, 0);
  ledcWrite(CH_M2_FRENTE, 0); ledcWrite(CH_M2_RE, 0);
}

void frente() {
  // Motor Esquerdo: FRENTE
  ledcWrite(CH_M1_VIVO, 255); 
  ledcWrite(CH_M1_MORTO, 0);
  
  // Motor Direito: FRENTE (invertido - era Ré)
  ledcWrite(CH_M2_FRENTE, 0);    
  ledcWrite(CH_M2_RE, 255);      
}

void esquerda() {
  // Motor Esquerdo: PARADO
  ledcWrite(CH_M1_VIVO, 0); 
  ledcWrite(CH_M1_MORTO, 0);
  
  // Motor Direito: FRENTE (para girar sobre o eixo)
  ledcWrite(CH_M2_FRENTE, 0);    
  ledcWrite(CH_M2_RE, 255);      
}

void direita() {
  // Motor Esquerdo: FRENTE
  ledcWrite(CH_M1_VIVO, 255);
  ledcWrite(CH_M1_MORTO, 0);     
  
  // Motor Direito: PARADO
  ledcWrite(CH_M2_FRENTE, 0);
  ledcWrite(CH_M2_RE, 0);
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0;
    
    char cmd = packetBuffer[0];
    
    // Serial.print("RECEBIDO: "); Serial.println(cmd); // Debug opcional
    
    digitalWrite(PIN_LED_DEBUG, HIGH);
    
    switch(cmd) {
      case 'F': frente(); break;
      case 'E': esquerda(); break;
      case 'D': direita(); break;
      case 'P': parar(); break;
      default: parar(); break;
    }
    
    delay(10);
    digitalWrite(PIN_LED_DEBUG, LOW);
  }
}