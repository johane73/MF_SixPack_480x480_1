#include "MFCustomDevice.h"
#include "commandmessenger.h"
#include "allocateMem.h"
#include "MFEEPROM.h"
#if defined(HAS_CONFIG_IN_FLASH)
#include "MFCustomDevicesConfig.h"
#else
const char CustomDeviceConfig[] PROGMEM = {};
#endif

extern MFEEPROM MFeeprom;

/* **********************************************************************************
    The custom device pins, type and configuration is stored in the EEPROM
    While loading the config the adresses in the EEPROM are transferred to the constructor
    Within the constructor you have to copy the EEPROM content to a buffer
    and evaluate him. The buffer is used for all 3 types (pins, type configuration),
    so do it step by step.
    The max size of the buffer is defined here. It must be the size of the
    expected max length of these strings.

    E.g. 6 pins are required, each pin could have two characters (two digits),
    each pins are delimited by "|" and the string is NULL terminated.
    -> (6 * 2) + 5 + 1 = 18 bytes is the maximum.
    The custom type is "myTest", which means 14 characters plus NULL = 15
    The configuration is "myConfig", which means 8 characters plus NULL = 9
    The maximum characters to be expected is 18, so MEMLEN_STRING_BUFFER has to be at least 18
********************************************************************************** */
#define MEMLEN_STRING_BUFFER 40

// reads a string from EEPROM or Flash at given address which is '.' terminated and saves it to the buffer
bool MFCustomDevice::getStringFromMem(uint16_t addrMem, char *buffer, bool configFromFlash)
{
    char     temp     = 0;
    uint8_t  counter  = 0;
    uint16_t length   = MFeeprom.get_length();
    do {
        if (configFromFlash) {
            temp = pgm_read_byte_near(CustomDeviceConfig + addrMem++);
            if (addrMem > sizeof(CustomDeviceConfig))
                return false;
        } else {
            temp = MFeeprom.read_byte(addrMem++);
            if (addrMem > length)
                return false;
        }
        buffer[counter++] = temp;              // save character and locate next buffer position
        if (counter >= MEMLEN_STRING_BUFFER) { // nameBuffer will be exceeded
            return false;                      // abort copying to buffer
        }
    } while (temp != '.'); // reads until limiter '.' and locates the next free buffer position
    buffer[counter - 1] = 0x00; // replace '.' by NULL, terminates the string
    return true;
}

MFCustomDevice::MFCustomDevice()
{
    _initialized = false;
}

/* **********************************************************************************
    Within the connector pins, a device name and a config string can be defined
    These informations are stored in the EEPROM or Flash like for the other devices.
    While reading the config from the EEPROM or Flash this function is called.
    It is the first function which will be called for the custom device.
    If it fits into the memory buffer, the constructor for the customer device
    will be called
********************************************************************************** */


void MFCustomDevice::attach(uint16_t adrPin, uint16_t adrType, uint16_t adrConfig, bool configFromFlash)
{
    #if 0
    Serial.println("[myTest] MFCustomDevice::attach ENTERED");
    Serial.printf("[myTest] attach called: adrPin=%u adrType=%u adrConfig=%u flash=%d\n", adrPin, adrType, adrConfig, configFromFlash);
    #endif

    if (adrPin == 0) {
        #if 0
        Serial.println("[myTest] EXIT: adrPin is zero");
        #endif
        return;
    }

    char *params, *p = NULL;
    char parameter[MEMLEN_STRING_BUFFER];
    uint8_t _pin1, _pin2, _pin3;

    getStringFromMem(adrType, parameter, configFromFlash);
    #if 0
    Serial.printf("[myTest] Device type='%s'\n", parameter);
    #endif

    if (strcmp(parameter, "myTest") == 0)
        _customType = MY_CUSTOM_DEVICE_1;
    else if (strcmp(parameter, "myTest2") == 0)
        _customType = MY_CUSTOM_DEVICE_2;

    #if 0
    Serial.printf("[myTest] customType=%u sizeof(myTest)=%u\n", _customType, (unsigned)sizeof(myTest));
    #endif

    if (_customType == MY_CUSTOM_DEVICE_1) {
        if (!FitInMemory(sizeof(myTest))) {
            #if 0
            Serial.println("[myTest] EXIT: insufficient device memory");
            #endif
            cmdMessenger.sendCmd(kStatus, F("Custom Device does not fit in Memory"));
            return;
        }

        #if 0
        Serial.println("[myTest] Memory check passed");
        #endif
        // Read the three configured pins
        if (!getStringFromMem(adrPin, parameter, configFromFlash)) {
            cmdMessenger.sendCmd(kStatus, F("Failed to read custom device pins"));
            return;
        }

        params = strtok_r(parameter, "|", &p);
        if (params == NULL) {
            cmdMessenger.sendCmd(kStatus, F("Missing custom device pin 1"));
            return;
        }
        _pin1 = atoi(params);

        params = strtok_r(NULL, "|", &p);
        if (params == NULL) {
            cmdMessenger.sendCmd(kStatus, F("Missing custom device pin 2"));
            return;
        }
        _pin2 = atoi(params);

        params = strtok_r(NULL, "|", &p);
        if (params == NULL) {
            cmdMessenger.sendCmd(kStatus, F("Missing custom device pin 3"));
            return;
        }
        _pin3 = atoi(params);

        // Construct and initialize the custom device
        _mydevice = new (allocateMemory(sizeof(myTest))) myTest(_pin1, _pin2, "myTest 1");
        _mydevice->attach(_pin3, nullptr);
        _mydevice->begin();
        _initialized = true;
    }
    else if (_customType == MY_CUSTOM_DEVICE_2) {
        if (!FitInMemory(sizeof(myTest))) {
            cmdMessenger.sendCmd(kStatus, F("Custom Device does not fit in Memory"));
            return;
        }

        // Read the three configured pins
        if (!getStringFromMem(adrPin, parameter, configFromFlash)) {
            cmdMessenger.sendCmd(kStatus, F("Failed to read custom device pins"));
            return;
        }

        params = strtok_r(parameter, "|", &p);
        if (params == NULL) {
            cmdMessenger.sendCmd(kStatus, F("Missing custom device pin 1"));
            return;
        }
        _pin1 = atoi(params);

        params = strtok_r(NULL, "|", &p);
        if (params == NULL) {
            cmdMessenger.sendCmd(kStatus, F("Missing custom device pin 2"));
            return;
        }
        _pin2 = atoi(params);

        params = strtok_r(NULL, "|", &p);
        if (params == NULL) {
            cmdMessenger.sendCmd(kStatus, F("Missing custom device pin 3"));
            return;
        }
        _pin3 = atoi(params);

        // Construct and initialize the custom device
        _mydevice = new (allocateMemory(sizeof(myTest))) myTest(_pin1, _pin2, "myTest 2" );
        _mydevice->attach(_pin3, nullptr);
        _mydevice->begin();
        _initialized = true;
    }
    else {
        #if 0
        Serial.println("[myTest] EXIT: unsupported device type");
        #endif
        cmdMessenger.sendCmd(kStatus, F("Custom Device is not supported by this firmware version"));
    }
}


/* **********************************************************************************
    The custom devives gets unregistered if a new config gets uploaded.
    Keep it as it is, mostly nothing must be changed.
    It gets called from CustomerDevice::Clear()
********************************************************************************** */
void MFCustomDevice::detach()
{
    _initialized = false;
    if (_customType == MY_CUSTOM_DEVICE_1) {
        _mydevice->detach();
    } else if (_customType == MY_CUSTOM_DEVICE_2) {
        _mydevice->detach();
    }
}

/* **********************************************************************************
    Within in loop() the update() function is called regularly
    Within the loop() you can define a time delay where this function gets called
    or as fast as possible. See comments in loop().
    It is only needed if you have to update your custom device without getting
    new values from the connector.
    Otherwise just make a return; in the calling function.
    It gets called from CustomerDevice::update()
********************************************************************************** */
void MFCustomDevice::update()
{
    if (!_initialized) return;
    /* **********************************************************************************
        Do something if required
    ********************************************************************************** */
    if (_customType == MY_CUSTOM_DEVICE_1) {
        _mydevice->update();
    } else if (_customType == MY_CUSTOM_DEVICE_2) {
        _mydevice->update();
    }
}

/* **********************************************************************************
    If an output for the custom device is defined in the connector,
    this function gets called when a new value is available.
    It gets called from CustomerDevice::OnSet()
********************************************************************************** */
void MFCustomDevice::set(int16_t messageID, char *setPoint)
{
    if (!_initialized) return;

    if (_customType == MY_CUSTOM_DEVICE_1) {
        _mydevice->set(messageID, setPoint);
    } else if (_customType == MY_CUSTOM_DEVICE_2) {
        _mydevice->set(messageID, setPoint);
    }
}
