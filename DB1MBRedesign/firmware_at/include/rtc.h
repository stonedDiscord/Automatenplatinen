#ifndef RTC_H
#define RTC_H

// RTC pins
#define RTC_CLK_PIN     PB5
#define RTC_DATA_PIN    PC4
#define RTC_CE_PIN      PB1
#define RTC_WR_PIN      PB3

void rtc_read_52bits(uint8_t *buffer);

#endif // RTC_H
