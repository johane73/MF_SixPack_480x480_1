#include <stdlib.h>
#include "myTest.h"
#include "allocateMem.h"
#include "commandmessenger.h"
#include <math.h>
#include <vsi_dial.h>

myTest::myTest(uint8_t Pin1, uint8_t Pin2, const char *title)
    :   _needleSprite(&_tft)
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

    _tft.setPivot(160, 120);

    _tft.setSwapBytes(true);
    _tft.pushImage(40, 0, 240, 240, vsiDial);

    createNeedleSprite();
    if (_needleSprite.created())
    {
        drawNeedle(0);
    }

    _verticalSpeed = 0;
    _displayedVerticalSpeed = 0;

    _initialised = true;
}

void myTest::drawNeedleHub()
{
    _tft.fillCircle(160, 115, 7, TFT_WHITE);
    _tft.fillCircle(160, 115, 3, TFT_DARKGREY);
}

void myTest::drawDial()
{
    const int cx = 160;
    const int cy = 115;
    const int radius = 105;

    _tft.fillScreen(TFT_BLACK);

    // Outer instrument bezel
    _tft.drawCircle(cx, cy, radius, TFT_DARKGREY);
    _tft.drawCircle(cx, cy, radius - 2, TFT_WHITE);
    _tft.drawCircle(cx, cy, radius - 4, TFT_DARKGREY);

    // Scale markings: -4000 to +4000 FPM
    // 500 FPM minor intervals, 1000 FPM major intervals.
    for (int speed = -4000; speed <= 4000; speed += 500)
    {
        // float angle = (180.0f + speed * 135.0f / 4000.0f)
        //               * DEG_TO_RAD;
        float angle = (180.0f + speed * 180.0f / 4000.0f)
              * DEG_TO_RAD;

        bool major = (speed % 1000 == 0);

        int innerRadius = major ? 78 : 84;
        int outerRadius = 96;

        int x1 = cx + lroundf(cosf(angle) * innerRadius);
        int y1 = cy + lroundf(sinf(angle) * innerRadius);

        int x2 = cx + lroundf(cosf(angle) * outerRadius);
        int y2 = cy + lroundf(sinf(angle) * outerRadius);

        _tft.drawLine(x1, y1, x2, y2, TFT_WHITE);
    }

    // Number labels
    _tft.setTextColor(TFT_WHITE, TFT_BLACK);
    _tft.setTextDatum(MC_DATUM);
    _tft.setTextSize(2);

    for (int speed = -4000; speed <= 4000; speed += 1000)
    {
        float angle = (180.0f + speed * 180.0f / 4000.0f)
                      * DEG_TO_RAD;

        int labelRadius = 66;

        int x = cx + lroundf(cosf(angle) * labelRadius);
        int y = cy + lroundf(sinf(angle) * labelRadius);

        char label[4];
        snprintf(label, sizeof(label), "%d", abs(speed) / 1000);

        _tft.drawString(label, x, y);
    }

    // Instrument text
    _tft.setTextSize(1);
    _tft.drawString("VERTICAL SPEED", cx, 91);
    _tft.drawString("FT / MIN", cx, 103);

    _tft.setTextSize(2);
    _tft.drawString("UP", 160, 143);
    _tft.drawString("DN", 160, 163);
}

void myTest::drawNeedle(int32_t verticalSpeed)
{
    // const int x = 90;
    // const int y = 45;

    // verticalSpeed = constrain(verticalSpeed, -4000, 4000);

    // // Restore the original dial underneath the previous needle.
    // _dialBackgroundSprite.pushSprite(x, y);

    // float angle = 45.0f +
    //     ((verticalSpeed + 4000) / 8000.0f) * 270.0f;

    // _needleSprite.pushRotated(
    //     static_cast<int16_t>(lroundf(angle)),
    //     TFT_MAGENTA
    // );
    verticalSpeed = constrain(verticalSpeed, -4000, 4000);

    float angle = 180.0f +
        (verticalSpeed / 4000.0f) * 180.0f;

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

    // Broad needle body
    _needleSprite.fillRect(88, 76, 49, 9, TFT_WHITE);

    // Tapered needle tip
    _needleSprite.fillTriangle(
        137, 73,
        153, 80,
        137, 87,
        TFT_WHITE
    );

    // Rounded base near the pivot
    _needleSprite.fillTriangle(
        88, 76,
        88, 85,
        98, 80,
        TFT_WHITE
    );
}

void myTest::drawVSI()
{
    if (!_initialised || !_needleSprite.created())
        return;

    if (_verticalSpeed == _displayedVerticalSpeed)
        return;

    const int16_t oldAngle = static_cast<int16_t>(
        lroundf(180.0f +
        (_displayedVerticalSpeed / 4000.0f) * 180.0f)
    );

    const float rad = -oldAngle * DEG_TO_RAD;
    const float c = cosf(rad);
    const float s = sinf(rad);

    const float needleX[] = { 88, 153, 153, 88 };
    const float needleY[] = { 73, 73, 87, 87 };

    float minX = 1000, minY = 1000;
    float maxX = -1000, maxY = -1000;

    for (int i = 0; i < 4; i++)
    {
        const float dx = needleX[i] - 80;
        const float dy = needleY[i] - 80;

        const float x = 160 + dx * c - dy * s;
        const float y = 120 - dx * s + dy * c;

        minX = fminf(minX, x);
        maxX = fmaxf(maxX, x);
        minY = fminf(minY, y);
        maxY = fmaxf(maxY, y);
    }

    const int x1 = max(40, (int)floorf(minX) - 2);
    const int x2 = min(279, (int)ceilf(maxX) + 2);
    const int y1 = max(0, (int)floorf(minY) - 2);
    const int y2 = min(239, (int)ceilf(maxY) + 2);

    // Begin one shared SPI transaction.
    _tft.startWrite();

    // Restore the previous needle area.
    for (int y = y1; y <= y2; y++)
    {
        const uint16_t *row = &vsiDial[y * 240 + (x1 - 40)];
        _tft.pushImage(x1, y, x2 - x1 + 1, 1, row);
    }

    // Draw the new needle.
    drawNeedle(_verticalSpeed);

    // Finish the shared SPI transaction.
    _tft.endWrite();

    _displayedVerticalSpeed = _verticalSpeed;
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
    if (messageID != 0 || setPoint == nullptr)
        return;

    _verticalSpeed = strtol(setPoint, nullptr, 10);
    _verticalSpeed = constrain(_verticalSpeed, -4000, 4000);

    // Draw immediately when a new value arrives.
    drawVSI();
}

void myTest::update()
{
    drawVSI();
}