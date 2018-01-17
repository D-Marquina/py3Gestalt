/*
  Arduino code for 'test_machine.py'
*/

char r = 0;
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    r = Serial.read();
    if (r == 'a'){
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      Serial.print("LED toggled!");
    }
    else{ 
      Serial.print("Received character was an '");
      Serial.print(r);
      Serial.print("'.");                  
    }
  }
}
