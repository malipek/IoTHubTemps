#include <OneWire.h> // https://www.pjrc.com/teensy/td_libs_OneWire.html
#include <DallasTemperature.h> // https://github.com/milesburton/Arduino-Temperature-Control-Library

// Pull-up resistor connected to external source (not controlled by Arduino)
// DQ pin connected to digital 2 input
#define ONE_WIRE_BUS 11

// Setup a oneWire instance to communicate with any OneWire devices
OneWire oneWire(ONE_WIRE_BUS);

// Pass our oneWire reference to Dallas Temperature. 
DallasTemperature sensors(&oneWire);


void setup() {
    Serial.begin(9600);
    while (!Serial) {
      ; // wait for serial port to connect
    }
    // Start up the library
    sensors.begin();
}

void loop(void)
{ 
  while (!Serial.findUntil("GET TEMPS", "\n")){
    ; // wait for "GET TEMPS" command on serial
  }
  sensors.requestTemperatures(); // Send the command to get temperatures

  //format JSON array
  Serial.print(F("{\"temps\":["));
  
  for(int i=0;i<sensors.getDeviceCount();i++) {
    // output all sensors' readings to serial
    Serial.print(String(sensors.getTempCByIndex(i)));
    if (i<sensors.getDeviceCount()-1) Serial.print(F(","));
  }
  
 Serial.println(F("]}"));
}
