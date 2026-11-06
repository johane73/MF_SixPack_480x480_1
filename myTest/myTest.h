
#pragma once

#include "Arduino.h"
#include <TFT_eSPI.h>

class myTest
{
public:
    myTest(uint8_t Pin1, uint8_t Pin2, const char *title);

    void begin();
    void attach(uint16_t Pin3, char *init);
    void detach();
    void set(int16_t messageID, char *setPoint);
    void update();

    void drawVSI();
    void drawNeedle(int32_t verticalSpeed);

private:
    bool _initialised = false;

    uint8_t _pin1, _pin2, _pin3;
    const char *_title;

    // Vertical Speed Indicator
    int32_t _verticalSpeed = 0;
    int32_t _displayedVerticalSpeed = -99999;

    TFT_eSPI _tft = TFT_eSPI();

    // Temporary sprite test
    TFT_eSprite _testSprite;
};
