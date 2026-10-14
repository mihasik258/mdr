# Примеры проектов MDR1206FI

> Разбор трёх официальных примеров АО «ПКК Миландр» для MDR1206FI. Все три собраны в **IDE Eclipse** с тулчейном **RISC-V GCC**, используют общую библиотеку **SPL** (Standard Peripheral Library) и **CMSIS**, и запускаются на отладочной плате с MDR1206FI.
>
> Исходники: каталог с исходными архивами — файлы `.zip` рядом с этим документом.
>
> **Назначение.** Каждый разбор отвечает на вопрос «как это делается на MDR1206FI» — с реальным кодом из проекта, а не с общими соображениями.

## Содержание

- [1. Общая архитектура всех трёх проектов](#1-общая-архитектура-всех-трёх-проектов)
- [2. Демонстрационный проект для модуля ELMETER](#2-демонстрационный-проект-для-модуля-elmeter)
- [3. Пример программного расчёта CRC](#3-пример-программного-расчёта-crc)
- [4. Пример эмуляции памяти EEPROM](#4-пример-эмуляции-памяти-eeprom)
- [5. Сквозные рецепты](#5-сквозные-рецепты)

---

## 1. Общая архитектура всех трёх проектов

### 1.1. Структура каталогов

Все проекты имеют идентичную раскладку:

| Каталог | Содержимое |
|---|---|
| `src/` | Пользовательский код: `main.c`, `syscalls.c`, специфика для примера |
| `Library/CMSIS/CoreSupport/` | Ядро RISC-V: `core_clic.c`, `core_clint.c`, `core_plic.c`, `core_pmp.c` |
| `Library/CMSIS/DeviceSupport/` | `system_MDR32VF0xI.c`, `system_MDR32VF0xI_it.c`, стартап под `src/gcc/MDR1206` и `src/iar/MDR1206` |
| `Library/SPL/inc`, `Library/SPL/src` | Драйверы периферии `MDR32VF0xI_*.c` |
| `launch_cfg/` | Конфигурации отладки Eclipse |
| `svd/MDR1206/` | SVD-описания для отладчика |
| `bootloader/` | `MDR1206_Bootloader.hex` (v1.1.0) |

### 1.2. Библиотека SPL — состав драйверов

Единый набор для всех проектов:

| Файл | Периферия |
|---|---|
| `MDR32VF0xI_adc.c` | SAR АЦП |
| `MDR32VF0xI_adcui.c` | ∆∑ АЦП (24-бит, 7 каналов) |
| `MDR32VF0xI_bkp.c` | Батарейный домен, RTC |
| `MDR32VF0xI_clk_measure.c` | Измерение частоты |
| `MDR32VF0xI_crc.c` | Аппаратный CRC |
| `MDR32VF0xI_dma.c` | DMA |
| `MDR32VF0xI_flash.c` | Flash-контроллер |
| `MDR32VF0xI_i2c.c` | I2C |
| `MDR32VF0xI_iwdg.c` | Сторожевой таймер IWDG |
| `MDR32VF0xI_l_block.c` | Криптографический блок (L-преобразование) |
| `MDR32VF0xI_otp.c` | OTP-память |
| `MDR32VF0xI_port.c` | Порты ввода-вывода |
| `MDR32VF0xI_power.c` | PVD |
| `MDR32VF0xI_random.c` | Генератор случайных чисел |
| `MDR32VF0xI_rst_clk.c` | Тактирование |
| `MDR32VF0xI_sensors.c` | Датчики |
| `MDR32VF0xI_ssp.c` | SSP (SPI) |
| `MDR32VF0xI_timer.c` | Таймеры |
| `MDR32VF0xI_uart.c` | UART |
| `MDR32VF0xI_usart.c` | USART (ISO7816) |
| `MDR32VF0xI_utils.c` | Утилиты, задержки |
| `MDR32VF0xI_wwdg.c` | Сторожевой таймер WWDG |

> ⚠️ Имя драйвера — `MDR32VF0xI_*`, а не `MDR1206*`. Это историческое имя семейства: библиотека покрывает и MDR32F02. Не пугаться несоответствия: `MDR1206FI` — просто один из вариантов `MDR32VF0xI`.

### 1.3. Типовые макросы выбора исполнения

В коде используется условная компиляция:

```c
#if defined(USE_MDR1206FI) || defined(USE_MDR1206AFI) || defined(USE_MDR1206)
    /* код для CHIP_ID = 217 / 215 */
#endif
#if !defined(USE_MDR32F02_REV_1X)
    /* код для ревизии, где есть бит PullUp */
#endif
```

Это тот самый механизм, которым в SPL разделяются различия `CHIP_ID = 217` и `CHIP_ID = 215`, описанные в [MDR1206FI.md](MDR1206FI.md).

---

## 2. Демонстрационный проект для модуля ELMETER

**Файл:** `Миландр. [MDR1206FI, IDE Eclipse] Демонстрационный проект для модуля ELMETER.zip`
**Версия:** V1.0.0, 18.09.2025
**Плата:** ELMETER с MDR1206FI

### 2.1. Что делает

1. После старта мигает встроенный светодиод на выводе **PD15**.
2. При нажатии встроенной кнопки **SB2** (вывод **PD14**) микросхема непрерывно шлёт по UART инкрементирующиеся значения.
3. Выводы UART1 (**PB0**, **PB1**) подключены к встроенному адаптеру USB-UART.

**Настройки UART1:** 9600 бод, 8 бит данных, 1 стоп-бит, без контроля чётности.

> Напомним: это ровно те же параметры, что использует режим загрузки **UART+J** по умолчанию (см. [MDR1206FI.md, раздел 6.3](MDR1206FI.md#63-режим-uartj--параметры-связи-с-46)). Это удобно: одна терминальная программа подходит и для загрузчика, и для демо.

### 2.2. Окружение и запуск

1. Настроить среду: **IDE Eclipse**, тулчейн **RISC-V GCC**, **пропатченный OpenOCD** с поддержкой MDR1206FI.
2. Импортировать проект в workspace, собрать.
3. Подключить USB-кабель к плате и ПК — **плата питается по USB**.
4. Подключить отладчик **CMSIS-DAP**. При использовании другого отладчика — внести правки в конфигурации отладки Eclipse.
5. Запустить любую из конфигураций отладки в `launch_cfg/`.

### 2.3. Состав

- `bootloader/MDR1206_Bootloader.hex` — загрузчик **v1.1.0** для МК.
- `Library/` — SPL **v0.2.0**.
- `src/main.c` — основная программа.
- `src/syscalls.c` — минимальная реализация syscalls Newlib **с выводом через UART**.
- `svd/` — SVD-файлы МК.

> ⚠️ Требуется **пропатченный OpenOCD**. Стандартный OpenOCD поддержки MDR1206FI не имеет — без патча отладка не заработает. Это самая частая причина «не удаётся подключиться» при первом запуске.

---

## 3. Пример программного расчёта CRC

**Файл:** `Миландр. [MDR1206FI, MDR1206AFI, MDR1215LGI] Пример программного расчёта CRC.zip`
**Версия:** V0.1.0, 07.08.2025
**Поддержаны:** MDR1206FI, MDR1206AFI, MDR1215LGI

### 3.1. Зачем этот пример

Он показывает **программный** расчёт CRC, в отличие от аппаратного блока CRC (описан в [MDR1206FI.md, раздел 12](MDR1206FI.md#12-аппаратный-crc)). Ключевая идея — реализовать CRC **через команды битовых манипуляций RISC-V** (`clmul`, `clmulh`, `clmulr`), то есть использовать расширение ZBC вместо табличных или побитовых алгоритмов.

Это эффективнее табличного подхода и не требует таблиц в памяти.

### 3.2. Реализованные варианты CRC

| Функция | Полином | Где применяется |
|---|---|---|
| `crc32_le` | `CRC32_POLY_LE = 0xedb88320` | CRC-32 (Ethernet, ZIP, PNG) |
| `crc32c_le` | `CRC32C_POLY_LE = 0x82F63B78` | CRC-32C (Castagnoli; iSCSI, SCTP, Btrfs) |
| `crc32_be` | `CRC32_POLY_BE = 0x04c11db7` | CRC-32 в прямом порядке |
| `crc16_ccitt` | `CRC16_CCITT_POLY_BE = 0x1021` | X.25, HDLC, XMODEM, Bluetooth, SD |
| `crc16_be` | `CRC16_POLY_BE = 0x8005` | Bisync, Modbus, USB, ANSI X3.28 |
| `crc16` | `CRC16_POLY_LE = 0xA001` | тот же, в обратном порядке бит |
| `crc8_ccitt` | `CRC8_CCITT_POLY_LE = 0xE0` | ITU-T I.432.1, ATM HEC, SMBus PEC |
| `crc8_itu` | `CRC8_CCITT_POLY_BE = 0x07` | то же, прямой порядок |
| `crc8_dallas` | `CRC8_DALLAS_POLY_LE = 0x8C` | 1-Wire (Dallas/Maxim) |

Обратите внимание: `CRC16_POLY_LE = 0xA001` — это в точности `rev(0x8005)`, а `CRC8_CCITT_POLY_LE = 0xE0` — `rev(0x07)`. В коде это указано прямо в комментариях.

### 3.3. Ключевая идея: пересчёт полинома в «частное»

Сердце примера — две `static inline` функции в `crc32.h`, вычисляемые **на этапе компиляции**:

```c
// x^63 // (x^32 + poly)  — для прямого порядка
static inline uint32_t poly2q(uint32_t poly) {
    uint32_t t;
    t = 1ul << 31;
    #pragma GCC unroll 31 // must be unrolled for compile-time constant propagation
    for (int n = 0; n < 31; n++)
        t ^= ((poly >> (n + 1)) & -((t >> (32 - 1 - n)) & 1));
    return t;
}

// rev(x^63 // (x^32 + rev(poly_le))) — для обратного порядка
static inline uint32_t poly2q_le(uint32_t poly_le) {
    uint32_t x;
    x = 1ul;
    #pragma GCC unroll 31
    for (int n = 0; n < 31; n++)
        x ^= ((poly_le << (n + 1)) & -((x >> n) & 1));
    return x;
}
```

> ⚠️ **`#pragma GCC unroll 31` обязателен.** Без разворачивания цикла компилятор не сможет вычислить результат на этапе компиляции, и весь смысл оптимизации пропадёт — в комментарии это подчёркнуто явно.

Готовые значения, закомментированные в заголовке (полезны для проверки):

```
CRC32_Q_LE  = 0xF7011641   // = poly2q_le(CRC32_POLY_LE)
CRC32C_Q_LE = 0xDEA713F1   // = poly2q_le(CRC32C_POLY_LE)
CRC32_Q_BE  = 0x826880EF   // = poly2q(CRC32_POLY_BE)
```

### 3.4. Обёртки над RISC-V командами

```c
static inline __attribute__((always_inline)) uint32_t rv_rev8 (uint32_t rs)
    { uint32_t rd; __asm__ ("rev8 %0, %1" : "=r"(rd) : "r"(rs)); return rd; }
static inline __attribute__((always_inline)) uint32_t rv_minu (uint32_t rs1, uint32_t rs2)
    { uint32_t rd; __asm__ ("minu %0, %1, %2" : "=r"(rd) : "r"(rs1), "r"(rs2)); return rd; }
static inline __attribute__((always_inline)) uint32_t rv_clmulh(uint32_t rs1, uint32_t rs2)
    { uint32_t rd; __asm__ ("clmulh %0, %1, %2" : "=r"(rd) : "r"(rs1), "r"(rs2)); return rd; }
static inline __attribute__((always_inline)) uint32_t rv_clmulr(uint32_t rs1, uint32_t rs2)
    { uint32_t rd; __asm__ ("clmulr %0, %1, %2" : "=r"(rd) : "r"(rs1), "r"(rs2)); return rd; }
static inline __attribute__((always_inline)) uint32_t rv_clmul (uint32_t rs1, uint32_t rs2)
    { uint32_t rd; __asm__ ("clmul %0, %1, %2" : "=r"(rd) : "r"(rs1), "r"(rs2)); return rd; }

#define cpu_to_le32
#define cpu_to_be32 rv_rev8
```

Здесь используются команды расширений **ZBB** (`minu`, `rev8`) и **ZBC** (`clmul`, `clmulh`, `clmulr`) — тех самых, что перечислены в системе команд RV32IMCNZX.

### 3.5. Основной цикл расчёта

```c
uint32_t crc32_generic(uint32_t crc, uint8_t const *p, size_t len,
                       uint32_t poly, uint32_t quotient)
{
    size_t head_len, words, tail_len;
    const uint32_t *p_ul;

    // Handle the unaligned head.
    head_len = rv_minu(len, -(uintptr_t)p % sizeof(int));
    if (head_len != 0u) {
        for (size_t i = 0; i < head_len; i++) {
            crc ^= (uint32_t)*p++ << (i * 8u);
        }
        crc = rv_clmulr(rv_clmul(crc, quotient << (32 - head_len * 8u)), poly)
              ^ (crc >> (head_len * 8u));
    }

    words = (len - head_len) / sizeof(int);
    p_ul = (uint32_t const *)(void const *)p;
    for (size_t i = 0; i < words; i++) {
        crc ^= cpu_to_le32(*p_ul++);
        crc = rv_clmulr(rv_clmul(crc, quotient), poly);
    }

    // Handle the tail bytes.
    tail_len = (len - head_len) % sizeof(int);
    if (tail_len != 0u) {
        p = (uint8_t const *)p_ul;
        for (size_t i = 0; i < tail_len; i++) {
            crc ^= (uint32_t)*p++ << (i * 8u);
        }
        crc = rv_clmulr(rv_clmul(crc, quotient << (32 - tail_len * 8u)), poly)
              ^ (crc >> (tail_len * 8u));
    }

    return crc;
}
```

**Разбор структуры — три фазы:**
1. **Невыровненная голова** (`head_len`) — обрабатывается побайтно до выравнивания указателя на 4 байта. Величина головы — `rv_minu(len, -(uintptr_t)p % 4)` (минимум из длины и расстояния до выравнивания).
2. **Выровненные 32-битные слова** — основной быстрый цикл: XOR слова в CRC и один шаг `clmulr(clmul(crc, quotient), poly)`.
3. **Хвост** (`tail_len`) — остаток байт обрабатывается так же, как голова.

Для `crc32_generic_be` используется симметричная логика с `rv_clmul(rv_clmulr(...))` и сдвигами в другую сторону.

### 3.6. Функция объединения CRC (`combine`)

Это самая интересная часть. Она позволяет **распараллелить** расчёт: посчитать CRC по независимым диапазонам буфера, а потом объединить результаты.

```c
static uint32_t crc32_generic_shift(uint32_t crc, size_t len,
                                    uint32_t polynomial, uint32_t quotient)
{
    uint32_t power = polynomial; /* CRC of x^32 */
    unsigned int head_len = len % 4;

    if (head_len)
        crc = rv_clmulr(rv_clmul(crc, quotient << (32 - head_len * 8u)), polynomial)
              ^ (crc >> (head_len * 8u));

    if (len & 4)
        crc = rv_clmulr(rv_clmul(crc, quotient), polynomial);

    len >>= 3;
    while (len) {
        /* Square power, advancing to x^(2^(i+1)) */
        power = gf2_multiply(power, power, polynomial, quotient);

        /* "power" is x^(2^i), modulo the polynomial */
        if (len & 1)
            crc = gf2_multiply(crc, power, polynomial, quotient);

        len >>= 1;
    }
    return crc;
}
```

Дописывание `len` нулевых байт к CRC выполняется за время, **пропорциональное log(len)**, а не `len`. Это классический приём «CRC сдвиг за логарифм»: умножение полиномов в GF(2) с возведением в квадрат по методу double-and-add.

Публичный интерфейс объединения (`crc32.h`):

```c
uint32_t crc32_le_shift(uint32_t crc, size_t len);
uint32_t crc32c_le_shift(uint32_t crc, size_t len);
uint32_t crc32_be_shift(uint32_t crc, size_t len);

static inline uint32_t crc32_le_combine(uint32_t crc1, uint32_t crc2, size_t len2)
{ return crc32_le_shift(crc1, len2) ^ crc2; }
```

**Смысл:** если `crc1` посчитан по первому блоку, а `crc2` — по второму, начиная с нуля, то `crc32_le_combine(crc1, crc2, len2)` даёт CRC конкатенации. Важно: `crc2` должен быть посчитан с **нулевым начальным значением**, а `crc1` — с тем же инициализатором, что и полный CRC.

### 3.7. Самопроверка

Пример содержит готовый набор тестов — **4096 случайных байт** и **100 тестовых случаев** с эталонными значениями для `crc32_le`, `crc32_be` и `crc32c_le`:

```c
static struct crc_test {
    uint32_t crc;       /* random starting crc */
    uint32_t start;     /* random 6 bit offset in buf */
    uint32_t length;    /* random 11 bit length of test */
    uint32_t crc_le;    /* expected crc32_le result */
    uint32_t crc_be;    /* expected crc32_be result */
    uint32_t crc32c_le; /* expected crc32c_le result */
} const test[] = {
    {0x674bf11d, 0x00000038, 0x00000542, 0x0af6d466, 0xd8b6e4c1, 0xf6e93d6c},
    /* ... ещё 99 записей ... */
};
```

Тесты проверяют корректность на **невыровненных** диапазонах (`start` — произвольное смещение) и разных длинах — именно тех местах, где легко ошибиться в голове/хвосте.

| Тест | Что проверяет |
|---|---|
| `crc32_test()` | 100 случаев × 3 варианта CRC против эталонов |
| `crc32_combine_test()` | Все возможные точки разбиения первых 10 случаев: `crc_full == crc32_le_combine(crc1, crc2, len2)` |
| `crc32c_combine_test()` | То же для CRC-32C |
| `crc32_be_combine_test()` | То же для прямого порядка |

### 3.8. `main.c`: демонстрация и «точки истины»

```c
const uint8_t data[] = "123456789";
uint32_t crc32le, crc32cle, crc32be;

crc32le  = ~crc32_le(~0u, data, 9);
crc32cle = ~crc32c_le(~0u, data, 9);
crc32be  = ~crc32_be(~0u, data, 9);
```

Строка `"123456789"` — **стандартный check value для CRC-алгоритмов**. Результаты можно сверить с публичными калькуляторами (ссылки на `crccalc.com` есть в комментариях кода).

> ⚠️ Обратите внимание на `~` (побитовую инверсию) вокруг вызовов и на начальное значение `~0u`. Это стандартная схема «reflected CRC»: начальное значение и результат инвертируются. **Без инверсии результат не совпадёт** с табличными значениями CRC-32.

Настройка тактирования в этом примере:

```c
static const RST_CLK_HCLK_InitTypeDef Clk = {
    .RST_CLK_CPU_C1_Source      = RST_CLK_CPU_C1_CLK_SRC_HSE,
    .RST_CLK_PLLCPU_ClockSource = RST_CLK_PLLCPU_CLK_SRC_HSE,
    .RST_CLK_PLLCPU_Multiplier  = RST_CLK_PLLCPU_MUL_4,
    .RST_CLK_CPU_C2_ClockSource = RST_CLK_CPU_C2_CLK_SRC_PLLCPU,
    .RST_CLK_CPU_C3_Prescaler   = RST_CLK_CPU_C3_PRESCALER_DIV_1,
    .RST_CLK_HCLK_ClockSource   = RST_CLK_CPU_HCLK_CLK_SRC_CPU_C3,
};
```

То есть: **HSE → PLL ×4 → CPU_C3 (делитель 1) → HCLK**. При HSE 8 МГц это даёт ядро 32 МГц.

> ⚠️ При смене частоты ядра **обязательно** скорректировать `Delay[2:0]` в `FLASH_CMD` (см. [MDR1206FI.md, раздел 7.1](MDR1206FI.md#71-chip_id--217-mdr1206fi-mdr1215lgi-mdr1219lgi)). В примере этого не видно — вероятно, это делается внутри `RST_CLK_HCLK_Init`. Проверять в SPL `MDR32VF0xI_rst_clk.c`.

UART для вывода отладочной информации: **115200 бод** на UART1 (PB0 — выход, PB1 — вход), тактирование `PER1_C2` от `CPU_C1` с делителем 1.

---

## 4. Пример эмуляции памяти EEPROM

**Файл:** `Миландр. [MDR1206FI, MDR1215LGI] Пример эмуляции памяти EEPROM.zip`
**Версия:** V0.1.0, 07.08.2025
**Поддержаны:** MDR1206FI, MDR1215LGI (ID217)

### 4.1. Что делает

Показывает **эмуляцию EEPROM на Flash**. В основе — **модифицированная библиотека STM EEPROM emulation expansion software для STM32Cube**, адаптированная под MDR1206FI.

Задача, которую это решает: у MDR1206FI нет настоящей EEPROM, а Flash имеет ограниченный ресурс и требует стирания страницы перед перезаписью. Эмулятор реализует поверх Flash абстракцию «переменных по виртуальным адресам» с выравниванием износа.

### 4.2. Состав

| Путь | Содержимое |
|---|---|
| `src/main.c` | Основная программа |
| `src/flash_interface.c/.h` | Интерфейс Flash для эмулятора **под MDR1206FI** |
| `EEPROM_Emul/` | Модифицированная библиотека STM EEPROM emulator для MDR1206FI ID217 |
| `Library/` | SPL |
| `svd/MDR1206FI.svd`, `svd/MDR1206AFI.svd` | SVD для обоих исполнений |
| `bootloader/MDR1206_Bootloader.hex` | Загрузчик МК |

> Файл `flash_interface.c` — самое ценное здесь: это **готовый рабочий пример низкоуровневых операций с Flash MDR1206FI**, извлечённый из настоящего проекта Миландра.

### 4.3. `flash_interface.c` — низкоуровневый доступ к Flash

**Запись слов (CHIP_ID = 217):**

```c
static void __RAM_TEXT_NOINLINE mdr217_flash_write_code(register uint32_t mem_type,
                                                        register uint32_t byte_count,
                                                        register uint32_t *buffer,
                                                        register uint32_t address)
{
    register uint32_t FLASH_Cmd;
    register uint32_t DelayConst = DELAY_CYCLE_COUNTER_GET_CONST_US(SystemCoreClock);

    RST_CLK_PCLKCmd(RST_CLK_PCLK_FLASH, ENABLE);

    FLASH_SetRegistersLock(RESET);
    FLASH_Cmd = MDR_FLASH->CMD;

    /* Switch on register access */
    FLASH_Cmd = (FLASH_Cmd & FLASH_CMD_DELAY_Msk) | FLASH_CMD_CON_Msk | FLASH_CMD_TMR_Msk;
    if (mem_type) {
        FLASH_Cmd |= FLASH_CMD_IFREN_Msk;
    }
    MDR_FLASH->CMD = FLASH_Cmd;

    while (byte_count > 0) {
        MDR_FLASH->ADR = address;
        MDR_FLASH->DI = *buffer;

        FLASH_Cmd |= FLASH_CMD_XE_Msk | FLASH_CMD_PROG_Msk;
        MDR_FLASH->CMD = FLASH_Cmd;
        DELAY_CycleCounter_WaitTicksAsm(DELAY_GET_TICKS_US(FLASH_TNVS_US, DelayConst));
        FLASH_Cmd |= FLASH_CMD_NVSTR_Msk;
        MDR_FLASH->CMD = FLASH_Cmd;
        DELAY_CycleCounter_WaitTicksAsm(DELAY_GET_TICKS_US(FLASH_TPGS_US, DelayConst));
        FLASH_Cmd |= FLASH_CMD_YE_Msk;
        MDR_FLASH->CMD = FLASH_Cmd;

        DELAY_CycleCounter_WaitTicksAsm(DELAY_GET_TICKS_US(FLASH_TPROG_US, DelayConst));

        FLASH_Cmd &= ~FLASH_CMD_YE_Msk;
        MDR_FLASH->CMD = FLASH_Cmd;

        FLASH_Cmd &= ~FLASH_CMD_PROG_Msk;
        MDR_FLASH->CMD = FLASH_Cmd;
        DELAY_CycleCounter_WaitTicksAsm(DELAY_GET_TICKS_US(FLASH_TNVH_US, DelayConst));
        FLASH_Cmd &= ~(FLASH_CMD_XE_Msk | FLASH_CMD_NVSTR_Msk);
        MDR_FLASH->CMD = FLASH_Cmd;
        DELAY_CycleCounter_WaitTicksAsm(DELAY_GET_TICKS_US(FLASH_TRCV_US, DelayConst));

        buffer += 1;
        address += 4;
        byte_count -= 4;
    }
    MDR_FLASH->CMD = (FLASH_Cmd & FLASH_CMD_DELAY_Msk) | FLASH_CMD_TMR_Msk;
    FLASH_SetRegistersLock(SET);
}
```

**Сверка с документацией.** Эта последовательность точно соответствует разделу 7.3 спецификации:

| Шаг в коде | Требование спецификации | Задержка |
|---|---|---|
| `CON \| TMR` + опционально `IFREN` | Включить регистровое управление, `TMR = 1` всегда | — |
| `ADR`, `DI` | Установить адрес и данные | — |
| `XE \| PROG` | Установить `XE` и `PROG` | — |
| `NVSTR` | Установить `NVSTR` | **Tnvs ≥ 5 мкс** (`FLASH_TNVS_US`) |
| `YE` | Установить `YE` | **Tpgs ≥ 10 мкс** (`FLASH_TPGS_US`) |
| снять `YE` | Запись длится Tprog | **Tprog = 20…40 мкс** (`FLASH_TPROG_US`) |
| снять `PROG` | — | — |
| снять `XE`, `NVSTR` | — | **Tnvh ≥ 5 мкс** (`FLASH_TNVH_US`) |
| — | — | **Trcv ≥ 10 мкс** (`FLASH_TRCV_US`) |

> ⚠️ **Ключевая деталь: `__RAM_TEXT_NOINLINE`.** Функция обязана исполняться **из ОЗУ**, потому что в режиме программирования Flash не может выдавать инструкции процессору (см. [MDR1206FI.md, раздел 7.1](MDR1206FI.md#71-chip_id--217-mdr1206fi-mdr1215lgi-mdr1219lgi)). Атрибут помещает код в RAM. Если написать такую функцию без атрибута — микросхема зависнет.
>
> ⚠️ **Бит `TMR` всегда должен быть `1`.** В коде он выставляется и при входе, и при выходе. Спецификация прямо рекомендует всегда записывать «1» — иначе разрешается тестовый режим Flash.
>
> ⚠️ **`Delay` сохраняется, а не сбрасывается.** Обратите внимание: `FLASH_Cmd & FLASH_CMD_DELAY_Msk` — поле `Delay` при входе **читается** и затем восстанавливается. Тактовая частота ядра не должна пострадать от операций с Flash.

**Стирание страницы:**

```c
static void __RAM_TEXT_NOINLINE mdr217_flash_erase_sect(register uint32_t mem_type,
                                                        register uint32_t first,
                                                        register uint32_t last)
{
    RST_CLK_PCLKCmd(RST_CLK_PCLK_FLASH, ENABLE);
    FLASH_SetRegistersLock(RESET);

    for (uint32_t sect = first; sect <= last; sect++) {
        FLASH_ErasePage(sect * 0x1000, mem_type ? FLASH_BANK_INFO : FLASH_BANK_MAIN);
    }

    FLASH_SetRegistersLock(SET);
}
```

> Шаг адреса страницы — **`0x1000` = 4 Кбайт**, что точно соответствует размеру страницы стирания для CHIP_ID = 217.

**Блокировка регистрового доступа:**

Перед операциями — `FLASH_SetRegistersLock(RESET)` (разрешить), после — `FLASH_SetRegistersLock(SET)` (запретить). Это соответствует требованию спецификации: «После окончания операций записи или стирания необходимо сбросить ключ для запрещения регистрового доступа».

**Запись двойного слова:**

```c
HAL_StatusTypeDef FI_WriteDoubleWord(uint32_t Address, uint64_t Data)
{
    assert(*(volatile uint64_t *)Address == (uint64_t)0xFFFFFFFFFFFFFFFFU);
    mdr217_flash_write_code(START_PAGE_ADDRESS < 0x10000000, 8, (uint32_t *)&Data, Address);
    return HAL_OK;
}
```

> ⚠️ **`assert` в начале — не украшение.** Flash можно записывать только в стёртое состояние (`0xFFFF...`). Эмулятор EEPROM держит инвариант «пишем только в стёртое», и assert это фиксирует. При отладке `assert` сработает ровно там, где нарушена логика выравнивания износа.

**Определение банка по адресу:** выражение `START_PAGE_ADDRESS < 0x10000000` различает основную память (адреса `0x1000_xxxx` и выше) и информационную (`0x0002_xxxx`) — это ровно те два диапазона, что даны в спецификации.

### 4.4. `main.c`: использование эмулятора

```c
/* Initialize EEPROM emulation driver (mandatory). */
ee_status = EE_Init(EE_CONDITIONAL_ERASE);
if (ee_status != EE_OK) { Error_Handler(); }

for (uint16_t VirtAddress = 1; VirtAddress < NB_OF_VARIABLES + 1; VirtAddress++) {
    ee_status = EE_WriteVariable32bits(VirtAddress, VirtAddress + 42);
    if (ee_status == EE_CLEANUP_REQUIRED) { ee_status = EE_CleanUp(); }
    if (ee_status != EE_OK) { Error_Handler(); }
}

for (int i = 1; i < 1000; i++) {
    ee_status = EE_WriteVariable32bits(1, rand());
    if (ee_status == EE_CLEANUP_REQUIRED) { ee_status = EE_CleanUp(); }
    if (ee_status != EE_OK) { Error_Handler(); }
}

for (uint16_t VirtAddress = 1; VirtAddress < NB_OF_VARIABLES + 1; VirtAddress++) {
    uint32_t val;
    ee_status = EE_ReadVariable32bits(VirtAddress, &val);
    if (ee_status != EE_OK) { Error_Handler(); }
    printf("@%d = %lu\r\n", VirtAddress, val);
}
```

**Сценарий теста — три фазы:**
1. Инициализация эмулятора (`EE_Init`) — **обязательный** вызов.
2. Запись переменных 1…`NB_OF_VARIABLES` начальными значениями.
3. **1000 перезаписей** одной переменной случайными значениями — это стресс-тест выравнивания износа и очистки.
4. Чтение всех переменных и вывод через UART.

> ⚠️ **`EE_CLEANUP_REQUIRED` — не ошибка, а штатная ситуация.** Когда страница заполнена, эмулятор требует «сборки мусора» — вызова `EE_CleanUp()`. Обрабатывать этот код нужно **явно**, как в примере; если его проигнорировать, запись в итоге провалится. Обратите внимание: в примере `EE_CleanUp()` вызывается и потом результат проверяется тем же `!= EE_OK`.
>
> ⚠️ Стирание страницы может **занять десятки миллисекунд** (для CHIP_ID = 217: `Terase = 20…40 мс`). При 1000 перезаписях цикл будет работать заметное время. Это нормальное поведение, а не зависание.

**Генератор случайных чисел** используется для получения действительно разных значений:

```c
void RNG_Config(void)
{
    RANDOM_InitTypeDef RNG;
    RANDOM_StructInit(&RNG);
    RNG.RANDOM_WorkMode = RANDOM_WORK_MODE_START_ON_READ;
    RST_CLK_PCLKCmd(RST_CLK_PCLK_RANDOM, ENABLE);
    RANDOM_Init(&RNG);
    while (RANDOM_GetFlagStatus(RANDOM_FLAG_UNREAD_DATA) == RESET) {}
    srand(RANDOM_GetData());
}
```

Обратите внимание на режим `RANDOM_WORK_MODE_START_ON_READ` и на **ожидание флага `RANDOM_FLAG_UNREAD_DATA`** перед чтением — генератору нужно время на формирование значения.

### 4.5. Интерфейс эмулятора

| Функция | Назначение |
|---|---|
| `EE_Init(EE_CONDITIONAL_ERASE)` | Инициализация; обязательно вызвать перед работой |
| `EE_WriteVariable32bits(VirtAddress, data)` | Запись 32-битной переменной по виртуальному адресу |
| `EE_ReadVariable32bits(VirtAddress, &val)` | Чтение переменной |
| `EE_CleanUp()` | Сборка мусора, когда возвращён `EE_CLEANUP_REQUIRED` |
| `FI_WriteDoubleWord(Address, Data)` | Низкоуровневая запись (реализация примера) |
| `FI_PageErase(Page, NbPages)` | Стирание страниц (реализация примера) |

---

## 5. Сквозные рецепты

### 5.1. Настройка тактирования (идиома, повторяется во всех проектах)

```c
static const RST_CLK_HCLK_InitTypeDef Clk = {
    .RST_CLK_CPU_C1_Source      = RST_CLK_CPU_C1_CLK_SRC_HSE,
    .RST_CLK_PLLCPU_ClockSource = RST_CLK_PLLCPU_CLK_SRC_HSE,
    .RST_CLK_PLLCPU_Multiplier  = RST_CLK_PLLCPU_MUL_4,
    .RST_CLK_CPU_C2_ClockSource = RST_CLK_CPU_C2_CLK_SRC_PLLCPU,
    .RST_CLK_CPU_C3_Prescaler   = RST_CLK_CPU_C3_PRESCALER_DIV_1,
    .RST_CLK_HCLK_ClockSource   = RST_CLK_CPU_HCLK_CLK_SRC_CPU_C3,
};

RST_CLK_DeInit();
#if defined(USE_MDR1206FI) || defined(USE_MDR1206AFI) || defined(USE_MDR1206)
    RST_CLK_HCLK_ClkSelection(RST_CLK_CPU_HCLK_CLK_SRC_HSI);
#endif
SystemCoreClockUpdate();

RST_CLK_HSE_Cmd(ENABLE);
while (RST_CLK_HSE_GetStatus() != SUCCESS) { }   // ждём стабилизации HSE

ErrorCode = RST_CLK_HCLK_Init(&Clk);
if (ErrorCode != SUCCESS) { exit(EXIT_FAILURE); }
```

**Последовательность важна:**
1. `RST_CLK_DeInit()` — сброс блока тактирования.
2. `RST_CLK_HCLK_ClkSelection(...HSI)` — **явно переключиться на HSI** перед настройкой HSE. Это защита: пока HSE запускается, ядро должно от чего-то работать.
3. `SystemCoreClockUpdate()` — пересчитать переменную частоты (нужна для расчёта задержек).
4. Запустить HSE и **дождаться** `RST_CLK_HSE_GetStatus() == SUCCESS`.
5. `RST_CLK_HCLK_Init(&Clk)` — переключиться на PLL.

> ⚠️ **Не пропускать ожидание HSE.** Без него переключение на PLL произойдёт до стабилизации осциллятора. Вспомните из спецификации: бит `HSERDY` появляется раньше, чем заканчиваются переходные процессы, а время старта кварца может составлять **единицы миллисекунд** (для 8 МГц — порядка 5,7 мс).

### 5.2. Вывод через UART (для отладки)

```c
PORT_InitTypeDef UART_Pins = {
    .PORT_Pin       = PORT_PIN_0,
    .PORT_Mode      = PORT_MODE_DIGITAL,
    .PORT_Direction = PORT_DIRECTION_OUTPUT,   // PB0 — TX
    .PORT_Function  = PORT_FUNCTION_MAIN,      // основная функция = UART1_TXD
    .PORT_Power     = PORT_POWER_NOMINAL_UPTO_2mA,
    .PORT_PullUp    = PORT_PULL_UP_OFF,
    .PORT_PullDown  = PORT_PULL_DOWN_OFF,
};

RST_CLK_PCLKCmd(RST_CLK_PCLK_PORTB, ENABLE);
PORT_Init(MDR_PORTB, &UART_Pins);

UART_Pins.PORT_Pin = PORT_PIN_1;
UART_Pins.PORT_Direction = PORT_DIRECTION_INPUT;   // PB1 — RX
PORT_Init(MDR_PORTB, &UART_Pins);

RST_CLK_PER1_C2_ClkSelection(RST_CLK_PER1_C2_CLK_SRC_CPU_C1);
RST_CLK_PER1_C2_SetPrescaler(RST_CLK_PER1_C2_UART1, RST_CLK_PER1_PRESCALER_DIV_1);
RST_CLK_PER1_C2_Cmd(RST_CLK_PER1_C2_UART1, ENABLE);
RST_CLK_PCLKCmd(RST_CLK_PCLK_UART1, ENABLE);

UART_DeInit(MDR_UART1);
UART_StructInit(&UART_Print);
UART_Print.UART_BaudRate = 115200;
UART_Init(MDR_UART1, &UART_Print);
UART_Cmd(MDR_UART1, ENABLE);
```

**Здесь нужны две отдельные операции тактирования:**
- `RST_CLK_PCLKCmd(RST_CLK_PCLK_UART1, ...)` — тактирование **самого блока** UART1 (бит `PCLK[1]` в `PER2_CLOCK`).
- `RST_CLK_PER1_C2_Cmd(RST_CLK_PER1_C2_UART1, ...)` + `SetPrescaler` — выбор **источника и делителя** для `UART1_CLK`.

Это два разных мультиплексора, и нужно настроить оба — иначе UART либо не работает, либо выдаёт неверную скорость.

Выводы PB0/PB1 имеют основную функцию `UART1_TXD`/`UART1_RXD` (см. [MDR1206FI.md, раздел 2.2](MDR1206FI.md#22-функции-выводов-портов-таблица-2-с-2631)), поэтому достаточно `PORT_FUNCTION_MAIN`.

### 5.3. Настройка выводов порта (идиома)

```c
static const PORT_InitTypeDef LedPins = {
    .PORT_Pin       = LED_PINS,
    .PORT_Mode      = PORT_MODE_DIGITAL,
    .PORT_Direction = PORT_DIRECTION_OUTPUT,
    .PORT_Function  = PORT_FUNCTION_PORT,
    .PORT_Power     = PORT_POWER_NOMINAL_UPTO_2mA,
    .PORT_PullUp    = PORT_PULL_UP_OFF,
    .PORT_PullDown  = PORT_PULL_DOWN_OFF,
};

RST_CLK_PCLKCmd(LED_PORT_CLK, ENABLE);   // сначала тактирование порта!
PORT_Init(LED_PORT, &LedPins);
```

**Отображение полей на регистры** (см. [MDR1206FI.md, раздел 10.2](MDR1206FI.md#102-регистры-портов-таблица-330-с-213)):

| Поле SPL | Регистр |
|---|---|
| `PORT_Mode` | `PORT_ANALOG` (`ANALOG_EN`) |
| `PORT_Direction` / `PORT_Power` | `PORT_OE` / `PORT_PWR` |
| `PORT_Function` | `PORT_FUNC` (`MODE[1:0]`) |
| `PORT_PullUp` / `PORT_PullDown` | `PORT_PULL` |

> ⚠️ **Сначала `RST_CLK_PCLKCmd`, потом `PORT_Init`.** Пока не включено тактирование порта, запись в его регистры не подействует. Это ошибка №1 при работе с GPIO на этом семействе.
>
> ⚠️ **`PORT_POWER_NOMINAL_UPTO_2mA`** — обратите внимание, что в SPL значение этого поля абстрагировано, но в железе бит `PORT_PWR` **инвертирован между CHIP_ID = 217 и 215** (см. [MDR1206FI.md, раздел 10.2](MDR1206FI.md#102-регистры-портов-таблица-330-с-213)). SPL это скрывает через `#if defined(...)`, но при прямом доступе к регистрам об этом надо помнить.
>
> ⚠️ Поле `.PORT_PullUp` обёрнуто в `#if !defined(USE_MDR32F02_REV_1X)` — в ревизии 1.x этого бита нет. При переносе кода на другую ревизию проверять.

### 5.4. Что нужно для запуска любого из примеров

| Требование | Детали |
|---|---|
| IDE | **Eclipse** |
| Тулчейн | **RISC-V GCC** |
| Отладчик | **CMSIS-DAP** (или иной, с правкой `launch_cfg/`) |
| OpenOCD | **Пропатченный**, с поддержкой MDR1206FI |
| Питание | По USB-кабелю от ПК |
| Прошивка загрузчика | `MDR1206_Bootloader.hex` v1.1.0 |

---

## Связанные документы

- Справочник по микроконтроллеру: [MDR1206FI.md](MDR1206FI.md)
- Отладочная плата ELMETER (мануал, схема, распиновка): [ELMETER.md](ELMETER.md)
- Исходные архивы: каталог каталог с исходными архивами