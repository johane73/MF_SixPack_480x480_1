#include "myTest.h"
#include "allocateMem.h"
#include "commandmessenger.h"
#include <math.h>

/* **********************************************************************************
    This is just the basic code to set up your custom device.
    Change/add your code as needed.
********************************************************************************** */

myTest::myTest(uint8_t Pin1, uint8_t Pin2, const char *title)
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

    drawVSI();
    drawNeedle(0);

    _verticalSpeed = 0;
    _displayedVerticalSpeed = 0;

    _initialised = true;
}

void myTest::drawVSI()
{
    const int cx = 160;
    const int cy = 115;
    const int radius = 95;

    _tft.fillScreen(TFT_BLACK);

    // Instrument outer bezel
    _tft.drawCircle(cx, cy, radius, TFT_WHITE);
    _tft.drawCircle(cx, cy, radius - 2, TFT_DARKGREY);

    // Draw 13 scale marks over a 270-degree arc.
    for (int i = 0; i <= 12; i++)
    {
        float angle = (135.0f + i * 22.5f) * DEG_TO_RAD;

        int x1 = cx + cosf(angle) * 76;
        int y1 = cy + sinf(angle) * 76;
        int x2 = cx + cosf(angle) * 88;
        int y2 = cy + sinf(angle) * 88;

        _tft.drawLine(x1, y1, x2, y2, TFT_WHITE);
    }

    // Scale labels
    _tft.setTextColor(TFT_WHITE, TFT_BLACK);
    _tft.setTextSize(2);
    _tft.setTextDatum(MC_DATUM);

    _tft.drawString("-2", 237, 173);
    _tft.drawString("-1", 107, 211);
    _tft.drawString("0", 65, 115);
    _tft.drawString("+1", 107, 20);
    _tft.drawString("+2", 237, 49);

    // Instrument title
    _tft.setTextSize(2);
    _tft.drawString("VSI", 160, 190);

    // Units
    _tft.setTextSize(1);
    _tft.drawString("x1000 FT/MIN", 160, 211);
}

void myTest::drawNeedle(int32_t verticalSpeed)
{
    const int cx = 160;
    const int cy = 115;

    // Limit the displayed value to the instrument range.
    verticalSpeed = constrain(verticalSpeed, -2000, 2000);

    // Map -2000...+2000 to 135...405 degrees.
    // Zero is straight up; positive values move clockwise.
    float angle = (45.0f +
        ((verticalSpeed + 2000) / 4000.0f) * 270.0f) * DEG_TO_RAD;

    // Red needle
    // int needleX = cx + cosf(angle) * 70;
    // int needleY = cy + sinf(angle) * 70;
    int needleX = lroundf(cx + cosf(angle) * 70);
    int needleY = lroundf(cy + sinf(angle) * 70);

    _tft.drawLine(cx, cy, needleX, needleY, TFT_RED);

    _tft.fillCircle(cx, cy, 6, TFT_WHITE);
    _tft.fillCircle(cx, cy, 3, TFT_RED);


    // Digital vertical speed readout
    _tft.fillRect(105, 145, 110, 25, TFT_BLACK);

    _tft.setTextColor(TFT_GREEN, TFT_BLACK);
    _tft.setTextSize(2);
    _tft.setTextDatum(MC_DATUM);

    char valueText[16];
    snprintf(valueText, sizeof(valueText), "%+ld",
             (long)verticalSpeed);

    _tft.drawString(valueText, 160, 157);
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
    // Connector shutdown
    if (messageID == -1)
    {
        _tft.fillScreen(TFT_BLACK);
        return;
    }

    // Power-saving mode
    if (messageID == -2)
    {
        if (setPoint != nullptr && atoi(setPoint) == 1)
        {
            _tft.fillScreen(TFT_BLACK);
        }
        else
        {
            _displayedVerticalSpeed = -99999;
        }
        return;
    }

    // Message ID 0: Vertical Speed in ft/min
    // if (messageID == 0 && setPoint != nullptr)
    // {
    //     _verticalSpeed = atoi(setPoint);

    //     // Clamp to the instrument's range.
    //     _verticalSpeed = constrain(_verticalSpeed, -2000, 2000);
    // }

    if (messageID == 0 && setPoint != nullptr)
    {
        _verticalSpeed = atoi(setPoint);
        _verticalSpeed = constrain(_verticalSpeed, -2000, 2000);

        drawVSI();
        drawNeedle(_verticalSpeed);

        _displayedVerticalSpeed = _verticalSpeed;
    }
}

void myTest::update()
{
    if (!_initialised)
        return;

    if (_verticalSpeed != _displayedVerticalSpeed)
    {
        // Redraw the face to erase the previous needle.
        drawVSI();

        // Draw the needle at the new vertical speed.
        drawNeedle(_verticalSpeed);

        _displayedVerticalSpeed = _verticalSpeed;
    }
}