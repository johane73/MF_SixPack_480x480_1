
#include "myTest.h"
#include "allocateMem.h"
#include "commandmessenger.h"
#include <math.h>

myTest::myTest(uint8_t Pin1, uint8_t Pin2, const char *title)
    : _needleSprite(&_tft)
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

    _tft.setPivot(160, 115);

    drawDial();
    createNeedleSprite();
    drawNeedle(0);
    drawNeedleHub();

    _verticalSpeed = 0;
    _displayedVerticalSpeed = 0;

    _initialised = true;
}

// void myTest::begin()
// {
//     pinMode(45, OUTPUT);
//     digitalWrite(45, HIGH);

//     _tft.init();
//     _tft.setRotation(1);
//     _tft.fillScreen(TFT_BLACK);

//     // Allocate the full-screen background sprite.
//     // _backgroundSprite.setColorDepth(16);

//     // if (_backgroundSprite.createSprite(320, 240) == nullptr)
//     // {
//     //     _tft.fillScreen(TFT_RED);
//     //     _initialised = true;
//     //     return;
//     // }

//     pinMode(45, OUTPUT);
//     digitalWrite(45, HIGH);

//     // Initialise and display the background.
//     // _backgroundSprite.fillSprite(TFT_BLACK);
//     // _backgroundSprite.pushSprite(0, 0);

//     _tft.fillCircle(160, 115, 10, TFT_WHITE);
//     _tft.fillCircle(160, 115, 5, TFT_RED);


//     // Set the display pivot to the centre of the screen.
//     _tft.setPivot(160, 115);

//     _needleSprite.setColorDepth(16);

//     if (_needleSprite.createSprite(160, 160) == nullptr)
//     {
//         _tft.fillScreen(TFT_RED);
//         _initialised = true;
//         return;
//     }

//     // Set the sprite pivot to its centre.
//     _needleSprite.setPivot(80, 80);

//     // _needleSprite.fillSprite(TFT_MAGENTA);
//     // _needleSprite.drawLine(50, 50, 10, 50, TFT_WHITE);
//     // _needleSprite.fillCircle(50, 50, 5, TFT_YELLOW);

//     // _needleSprite.pushRotated(90, TFT_MAGENTA);
//     _needleSprite.fillSprite(TFT_MAGENTA);
//     // Main needle body
//     _needleSprite.drawLine(88, 80, 145, 80, TFT_WHITE);
//     _needleSprite.drawLine(88, 79, 140, 79, TFT_WHITE);
//     _needleSprite.drawLine(88, 81, 140, 81, TFT_WHITE);

//     // Tapered needle tip
//     _needleSprite.fillTriangle(
//         145, 80,
//         137, 76,
//         137, 84,
//         TFT_WHITE
//     );
//     _needleSprite.pushRotated(180, TFT_MAGENTA);

//     // Central needle hub
//     _tft.fillCircle(160, 115, 7, TFT_WHITE);
//     _tft.fillCircle(160, 115, 3, TFT_DARKGREY);

//     _initialised = true;
// }

void myTest::drawNeedleHub()
{
    _tft.fillCircle(160, 115, 7, TFT_WHITE);
    _tft.fillCircle(160, 115, 3, TFT_DARKGREY);
}

void myTest::drawDial()
{
    _tft.fillScreen(TFT_BLACK);
}

void myTest::drawNeedle(int32_t verticalSpeed)
{
    verticalSpeed = constrain(verticalSpeed, -2000, 2000);

    float angle = 45.0f +
        ((verticalSpeed + 2000) / 4000.0f) * 270.0f;

    _needleSprite.pushRotated(
        static_cast<int16_t>(lroundf(angle)),
        TFT_MAGENTA
    );
}

void myTest::createNeedleSprite()
{
    _needleSprite.setColorDepth(16);

    if (_needleSprite.createSprite(160, 160) == nullptr)
    {
        _tft.fillScreen(TFT_RED);
        return;
    }

    _needleSprite.setPivot(80, 80);

    _needleSprite.fillSprite(TFT_MAGENTA);

    // Main needle body
    _needleSprite.drawLine(88, 80, 145, 80, TFT_WHITE);
    _needleSprite.drawLine(88, 79, 140, 79, TFT_WHITE);
    _needleSprite.drawLine(88, 81, 140, 81, TFT_WHITE);

    // Tapered needle tip
    _needleSprite.fillTriangle(
        145, 80,
        137, 76,
        137, 84,
        TFT_WHITE
    );
}


void myTest::drawVSI()
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

    _needleSprite.deleteSprite();
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
