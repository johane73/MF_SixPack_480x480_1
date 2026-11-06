
#include "myTest.h"
#include "allocateMem.h"
#include "commandmessenger.h"
#include <math.h>

myTest::myTest(uint8_t Pin1, uint8_t Pin2, const char *title)
    : _testSprite(&_tft)
{
    _pin1 = Pin1;
    _pin2 = Pin2;
    _title = title;

    pinMode(45, OUTPUT);
    digitalWrite(45, HIGH);
}

void myTest::begin()
{
    pinMode(45, OUTPUT);
    digitalWrite(45, HIGH);

    _tft.init();
    _tft.setRotation(1);
    _tft.fillScreen(TFT_BLACK);

    // Set the display pivot to the centre of the screen.
    _tft.setPivot(160, 120);

    _testSprite.setColorDepth(16);

    if (_testSprite.createSprite(100, 100) == nullptr)
    {
        _tft.fillScreen(TFT_RED);
        _initialised = true;
        return;
    }

    // Set the sprite pivot to its centre.
    _testSprite.setPivot(50, 50);

    _testSprite.fillSprite(TFT_MAGENTA);
    _testSprite.drawLine(50, 50, 10, 50, TFT_WHITE);
    _testSprite.fillCircle(50, 50, 5, TFT_YELLOW);

    _testSprite.pushRotated(90, TFT_MAGENTA);

    _initialised = true;
}



void myTest::drawVSI()
{
    // Not used during the temporary sprite test.
}

void myTest::drawNeedle(int32_t verticalSpeed)
{
    // Not used during the temporary sprite test.
}

void myTest::attach(uint16_t Pin3, char *init)
{
    _pin3 = Pin3;
}

void myTest::detach()
{
    if (!_initialised)
        return;

    _testSprite.deleteSprite();
    _tft.fillScreen(TFT_BLACK);

    _initialised = false;
}

void myTest::set(int16_t messageID, char *setPoint)
{
    // Not used during the temporary sprite test.
}

void myTest::update()
{
    // Not used during the temporary sprite test.
}
