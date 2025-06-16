#include <EEPROM.h>
#include "OneWireHub.h"
#include "DS2506.h"

constexpr uint8_t pin_onewire   { 2 };

auto hub = OneWireHub(pin_onewire);

void setup()
{

    Serial.begin(115200);
    Serial.println("OneWire-Hub DS2506");

    auto ds2506 = DS2506(EEPROM.read(0x00),EEPROM.read(0x01),EEPROM.read(0x02),EEPROM.read(0x03),EEPROM.read(0x04),EEPROM.read(0x05),EEPROM.read(0x06));

    // Setup OneWire
    hub.attach(ds2506);

    Serial.println("write header");
    constexpr char header[] = {0x1D, 0x54, 0x11, 0x00, 0x00, 0x42, 0x41, 0x4C, 0x4C, 0x59, 0x20, 0x57, 0x55, 0x4C, 0x46, 0x46, 0x20, 0x47, 0x4D, 0x42, 0x48};
    ds2506.writeMemory(reinterpret_cast<const uint8_t *>(header),sizeof(header),0x00);

    Serial.println("write first identifier");
    char id1[] = {EEPROM.read(0x07),EEPROM.read(0x08),EEPROM.read(0x09)};
    ds2506.writeMemory(reinterpret_cast<const uint8_t *>(id1),sizeof(id1),0x15);

    Serial.println("write tag");
    constexpr char tag[] = {0x00, 0x44, 0x56, 0x32, 0x39, 0x39}; // DV299
    ds2506.writeMemory(reinterpret_cast<const uint8_t *>(tag),sizeof(tag),0x18);

    Serial.println("write second identifier");
    char id2[] = {EEPROM.read(0x0a),EEPROM.read(0x0b)};
    ds2506.writeMemory(reinterpret_cast<const uint8_t *>(id1),sizeof(id2),0x1e);

    Serial.println("write machine type");
    char id2[] = {EEPROM.read(0x0a),EEPROM.read(0x0b)};
    ds2506.writeMemory(reinterpret_cast<const uint8_t *>(id1),sizeof(id2),0x7ec);

    Serial.println("config done");
}

void loop()
{
    // following function must be called periodically
    hub.poll();
} 