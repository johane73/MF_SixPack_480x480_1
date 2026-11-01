#include "myTest.h"
#include "allocateMem.h"
#include "commandmessenger.h"

/* **********************************************************************************
    This is just the basic code to set up your custom device.
    Change/add your code as needed.
********************************************************************************** */

myTest::myTest(uint8_t Pin1, uint8_t Pin2)
{
    _pin1 = Pin1;
    _pin2 = Pin2;

    pinMode(45, OUTPUT);
    digitalWrite(45, HIGH);
}

void myTest::begin()
{
    Serial.println("[myTest] begin() started");

    pinMode(45, OUTPUT);
    digitalWrite(45, HIGH);

    Serial.println("[myTest] Backlight enabled");

    _tft.init();
    Serial.println("[myTest] TFT initialized");

    _tft.setRotation(1);
    _tft.fillScreen(TFT_NAVY);

    _tft.setTextColor(TFT_WHITE, TFT_NAVY);
    _tft.setTextSize(2);
    _tft.setCursor(20, 40);

    _tft.println("MobiFlight");
    _tft.println("myTest");
    _tft.println("Display OK");

    _initialised = true;

    Serial.println("[myTest] begin() completed");
}

void myTest::attach(uint16_t Pin3, char *init)
{
    _pin3 = Pin3;
}

void myTest::detach()
{
    if (!_initialised)
        return;

    _tft.fillScreen(TFT_BLACK);
    _initialised = false;
}

void myTest::set(int16_t messageID, char *setPoint)
{
    /* **********************************************************************************
        Each messageID has it's own value
        check for the messageID and define what to do.
        Important Remark!
        MessageID == -2 will be send from the board when PowerSavingMode is set
            Message will be "0" for leaving and "1" for entering PowerSavingMode
        MessageID == -1 will be send from the connector when Connector stops running
        Put in your code to enter this mode (e.g. clear a display)

    ********************************************************************************** */
    int32_t  data = atoi(setPoint);
    uint16_t output;

    // do something according your messageID
    switch (messageID) {
    case -1:
        // tbd., get's called when Mobiflight shuts down
    case -2:
        // tbd., get's called when PowerSavingMode is entered
    case 0:
        output = (uint16_t)data;
        data   = output;
        break;
    case 1:
        /* code */
        break;
    case 2:
        /* code */
        break;
    default:
        break;
    }
}

void myTest::update()
{
    // Do something which is required regulary
}
